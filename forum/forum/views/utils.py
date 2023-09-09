from typing import Union, List

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.utils import timezone

from badges.jobs import review_bagdes_event
from badges.logic.utils import TRIGGER_EVENT_TYPES
from common.utils import *  # noqa
from forum import jobs
from forum import models
from forum.apps import logger
from forum.models import PostInvitation
from forum.views import notifications, follow_models
from tags import jobs as tag_jobs
from tags.models import Tag, Synonym
from userauth.models import ForumUser


def recalculate_user_reputation(user: AbstractUser):
    """
    Calculate user reputation based on VoteActivity
    """
    if user is None:
        return
    reputation_qs = (models.VoteActivity.objects
                     .filter(target=user)
                     .aggregate(rep=Sum('reputation_change')))
    reputation = reputation_qs['rep'] or 0
    if isinstance(user, ForumUser):
        user.reputation_score = reputation
        user.save()


def create_activity(source: Union[AbstractUser, None],
                    target: AbstractUser,
                    userinput: models.UserInput,
                    rep_change: int) -> models.VoteActivity:
    """Create VoteActivity if it does not exist.
    :param source: Originator of VoteActivity (upvoter, downvoter, ...) - can be None
    :param target: Target of VoteActivity who will earn the rep-points - can NOT be None
    :param userinput: Input the VoteActivity is on (can be Question or Answer)
    :param rep_change: Value of VoteActivity
    :returns: Created VoteActivity
    """
    source_username = source.username if source else None
    logger.debug(f'Create activity by {source_username}: '
                 f'{rep_change} for {target.username} on {userinput.get_model()} {userinput.id}')

    exist = (models.VoteActivity.objects
             .filter(source=source,
                     target=target,
                     question=userinput.get_question(),
                     answer=userinput.get_answer(),
                     reputation_change=rep_change)
             .first())
    if exist is not None:
        logger.warning('Activity already exist, exiting')
        return exist
    activity = models.VoteActivity.objects.create(source=source,
                                                  target=target,
                                                  question=userinput.get_question(),
                                                  answer=userinput.get_answer(),
                                                  reputation_change=rep_change)
    recalculate_user_reputation(target)
    return activity


def delete_activity(
        source: AbstractUser,
        target: AbstractUser,
        userinput: models.UserInput,
        rep_change: int) -> None:
    """Find an activity with parameters and delete it
    """
    logger.debug(f'Delete activity by {source.username}: '
                 f'{rep_change} for {target.username} on {userinput.get_model()} {userinput.id}')

    activity = (models.VoteActivity.objects
                .filter(source=source, target=target,
                        question=userinput.get_question(), answer=userinput.get_answer(),
                        reputation_change=rep_change)
                .first())
    if activity is not None:
        activity.delete()
        recalculate_user_reputation(target)
    return None


MODELS_MAP = {
    'question': models.Question,
    'answer': models.Answer,
    'comment_answer': models.AnswerComment,
    'comment_question': models.QuestionComment,
}


def get_model(model_name: str, pk: int):
    """Get a model instance based on model name and primary key
    :param model_name: model name to look for, based on MODELS_MAP dictionary
    :param pk: primary key to look for
    :returns: the instance
    """
    if model_name is None or model_name not in MODELS_MAP:
        logger.error(f"Attempt to get model {model_name} which is not supported")
        raise NotImplementedError
    try:
        q = MODELS_MAP[model_name].objects.get(pk=pk)
    except MODELS_MAP[model_name].DoesNotExist:
        q = None
    return q


# ======== Question methods ================

def _get_tag(tag_word: str, user: AbstractUser) -> Tag:
    """
    Get tag with tag_word.
    If such tag doesn't exist, check for synonym with tag_word.
    If it doesn't exist, create a tag (with the user as its author).
    """
    tag = Tag.objects.filter(tag_word=tag_word).first()
    if tag is not None:
        return tag
    synonym = Synonym.objects.filter(name=tag_word, active=True).first()
    if synonym is not None:
        return synonym.tag
    tag = Tag.objects.create(tag_word=tag_word, author=user)
    return tag


def create_article(user: AbstractUser, title: str, content: str, tags: str, **kwargs) -> models.Question:
    if 'type' not in kwargs:
        kwargs['type'] = models.Question.POST_TYPE_ARTICLE
    return create_question(user, title, content, tags, **kwargs)


def create_question(user: AbstractUser, title: str, content: str, tags: str,
                    send_notifications=True,
                    **kwargs) -> models.Question:
    """Create a question in the DB, add tags to the question and notify tag followers about new question.
    :param user: question author
    :param title: question title
    :param content: question content
    :param tags: tags to include, as string, separated by commas
    :param send_notifications: should notifications be sent? on by default
    :param kwargs: anonymous flag
    :return: the question created.
    """
    q = models.Question.objects.create(
        title=title, content=content, author=user, **kwargs)
    follow_models.create_follow_question(q, user)
    tags_to_add = set(tags.replace(' ', '').lower().split(','))
    if '' in tags_to_add:
        tags_to_add.remove('')
    for tag_word in tags_to_add:
        tag = _get_tag(tag_word, user)
        q.tags.add(tag)
        follow_models.create_follow_tag(tag, user)
    q.save()
    if send_notifications:
        notifications.notify_tag_followers_new_question(user, tags_to_add, q, )
    jobs.start_job(jobs.update_tag_follow_stats, q.id, user.id)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES['Create post'])
    return q


def update_question(user: AbstractUser, q: models.Question, title: str, content: str, tags: str) -> models.Question:
    """Update question content if there are changes
    :param user: User who is updating the post
    :param q: Question to be updated
    :param title: new title
    :param content: new content
    :param tags: new tags, separated by comma
    :returns: the updated Question
    """
    curr_tag_words = set(q.tag_words())
    new_tag_words = set(tags.replace(' ', '').lower().split(','))
    if '' in new_tag_words:
        new_tag_words.remove('')
    if q.title == title and q.content == content and curr_tag_words == new_tag_words:
        logger.info(f'No changes when updating question {q.id}, returning')
        return q
    old_title = q.title
    old_content = q.content
    q.title = title
    q.content = content
    if user != q.author:
        # If user updating is not the author, add them as editor and create edit reputation for them
        q.editor = user
        create_activity(None, user, q, 2)
    tags_to_remove = curr_tag_words.difference(new_tag_words)
    for tag_word in tags_to_remove:
        tag = Tag.objects.get(tag_word=tag_word)
        q.tags.remove(tag)
    tags_to_add = new_tag_words.difference(curr_tag_words)
    for tag_word in tags_to_add:
        tag = _get_tag(tag_word, user)
        q.tags.add(tag)
        follow_models.create_follow_tag(tag, q.author)
    jobs.start_job(jobs.update_tag_follow_stats, q.id, q.author.id)
    q.last_activity = timezone.now()
    q.save()
    follow_models.create_follow_question(q, user)
    notifications.notify_question_changes(user, q, old_title, old_content)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES['Update post'])
    return q


def delete_question(question: models.Question):
    answers_list = list(question.answer_set.all().using('default'))
    for answer in answers_list:
        delete_answer(answer)
    jobs.start_job(tag_jobs.update_tag_stats)
    author = question.author
    editor = question.editor
    question.delete()
    recalculate_user_reputation(author)
    recalculate_user_reputation(editor)


# Answers method

def create_answer(content: str, user: AbstractUser, question: models.Question,
                  send_notifications: bool = True) -> Union[models.Answer, None]:
    if content is None or content.strip() == '':
        logger.warning('Trying to create answer without content, ignoring')
        return None
    if question is None:  # Should not happen since it is tested in view
        logger.warning('Trying to create answer without question, ignoring')
        return None
    if question.answer_set.filter(author=user).count() > 0:
        logger.warning(f'User {user.username} already answered question, please update existing answer')
        return None
    a = models.Answer.objects.create(content=content, author=user, question=question)
    tags = a.question.tags.all()
    for tag in tags:
        follow_models.create_follow_tag(tag, user)
    jobs.start_job(jobs.update_tag_follow_stats, a.question_id, user.id)
    if send_notifications:
        notifications.notify_new_answer(user, a)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES['Create post'])
    return a


def update_answer(user: AbstractUser, answer: models.Answer, content: str) -> models.Answer:
    if content == answer.content:
        logger.info('no changes when updating answer, ignoring')
        return answer
    old_content = answer.content
    answer.content = content
    if user != answer.author:
        answer.editor = user
        create_activity(None, user, answer, 2)
    answer.save()
    notifications.notify_answer_changes(user, answer, old_content)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES['Update post'])
    return answer


def delete_answer(answer: models.Answer):
    author = answer.author
    editor = answer.editor
    answer.delete()
    recalculate_user_reputation(author)
    recalculate_user_reputation(editor)


def undo_upvote(user: AbstractUser, model_obj: models.VotableUserInput) -> models.VotableUserInput:
    model_obj.users_upvoted.remove(user)
    model_obj.save()
    delete_activity(user, model_obj.author, model_obj, settings.UPVOTE_CHANGE)
    return model_obj


def undo_downvote(user: AbstractUser, model_obj: models.VotableUserInput) -> models.VotableUserInput:
    model_obj.users_downvoted.remove(user)
    model_obj.save()
    delete_activity(user, model_obj.author, model_obj, settings.DOWNVOTE_CHANGE)
    return model_obj


def upvote(user: AbstractUser, model_obj: models.VotableUserInput) -> models.VotableUserInput:
    if model_obj.users_downvoted.filter(id=user.id).count() > 0:
        logger.debug(f'User {user.username} previously downvoted, removing downvote first')
        undo_downvote(user, model_obj)

    model_obj.users_upvoted.add(user)
    model_obj.save()
    follow_models.create_follow_question(model_obj.get_question(), user)
    create_activity(user, model_obj.author, model_obj, settings.UPVOTE_CHANGE)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES['Upvote'])
    return model_obj


def downvote(user: AbstractUser, model_obj: models.VotableUserInput) -> models.VotableUserInput:
    if model_obj.users_upvoted.filter(id=user.id).count() > 0:
        logger.info(f'User {user.username} previously downvoted, removing downvote first')
        undo_upvote(user, model_obj)

    model_obj.users_downvoted.add(user)
    model_obj.save()
    follow_models.create_follow_question(model_obj.get_question(), user)
    create_activity(user, model_obj.author, model_obj, settings.DOWNVOTE_CHANGE)
    return model_obj


def accept_answer(answer: models.Answer):
    """Mark an answer as accepted answer.
    :param answer: answer to mark
    """
    if answer is None:
        return
    answer.question.answer_set.update(is_accepted=False)
    answer.question.has_accepted_answer = True
    answer.is_accepted = True
    answer.save()
    logger.info(f"Answer {answer.id} marked as accepted for question {answer.question_id}")


# Comment method
def create_comment(content: str, user: AbstractUser, parent: models.UserInput) -> Union[models.Comment, None]:
    if content is None or content.strip() == '':
        logger.warning('Trying to create comment without content, ignoring')
        return None
    if parent is None:  # should never happen
        logger.warning('Trying to create comment without parent, ignoring')
        return None
    if isinstance(parent, models.Question):
        comment = models.QuestionComment(content=content, author=user, question=parent)
    else:  # isinstance(parent,models.Answer)
        comment = models.AnswerComment(content=content, author=user, answer=parent)
    comment.save()
    q = comment.get_question()
    notifications.notify_new_comment(user, parent, comment)
    follow_models.create_follow_question(q, user)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES['Create comment'])
    return comment


def delete_comment(comment: models.Comment):
    logger.debug(f'deleting {comment.pk}')
    follow_models.delete_follow_question(comment.get_question(), comment.author)
    comment.delete()


def upvote_comment(user: AbstractUser, comment: models.Comment) -> models.Comment:
    comment.users_upvoted.add(user)
    comment.votes += 1
    comment.save()
    comment.get_question().last_activity = timezone.now()
    comment.get_question().save()
    return comment


# QuestionFollow and TagFollow methods


def get_user_followed_tags(user: AbstractUser):
    follows = models.TagFollow.objects.filter(user=user)
    return [f.tag for f in follows]


def create_invites_and_notify_invite_users_to_question(
        inviter: AbstractUser, invitees: List[AbstractUser], question: models.Question):
    # Generate invitees list
    invited_list = []
    for invitee in invitees:
        if inviter == invitee:
            continue
        logger.debug(f'User {inviter.username} invited {invitee.username} to answer question id: {question.id}')
        existing = PostInvitation.objects.filter(
            question=question,
            inviter=inviter,
            invitee=invitee,
        ).first()
        if existing is None:
            PostInvitation.objects.create(
                question=question,
                inviter=inviter,
                invitee=invitee,
            )
            invited_list.append(invitee)
    notifications.notify_invite_users_to_question(inviter, question, invited_list)
    return len(invited_list)

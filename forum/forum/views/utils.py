from typing import Union, List, Optional

from constance import config
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
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
from wiwik_lib.models import Follow
from wiwik_lib.views.follow_views import delete_follow, create_follow


def recalculate_user_reputation(user: AbstractUser) -> None:
    """Calculate a user reputation based on VoteActivity"""
    if user is None or not isinstance(user, ForumUser):
        logger.warning(f"User {user} is not a ForumUser, skipping reputation recalculation")
        return
    reputation_qs = models.VoteActivity.objects.filter(target=user, reputation_change__isnull=False)
    reputation = sum([a.reputation_change for a in reputation_qs])
    user.reputation_score = reputation
    user.save()


def create_activity(
        source: Union[AbstractUser, None],
        target: AbstractUser,
        userinput: models.UserInput,
        activity_type: models.VoteActivity.ActivityType,
) -> models.VoteActivity:
    """Create VoteActivity if it does not exist.
    :param source: Originator of VoteActivity (upvoter, downvoter, ...) - can be None
    :param target: Target of VoteActivity who will earn the rep-points - can NOT be None
    :param userinput: Input the VoteActivity is on (can be Question or Answer)
    :param activity_type: Type of activity
    :returns: Created VoteActivity
    """
    rep_change_map = {
        models.VoteActivity.ActivityType.EDITED: config.EDITED_CHANGE,
        models.VoteActivity.ActivityType.UPVOTE: config.UPVOTE_CHANGE,
        models.VoteActivity.ActivityType.DOWNVOTE: config.DOWNVOTE_CHANGE,
        models.VoteActivity.ActivityType.ACCEPT: config.ACCEPT_ANSWER_CHANGE,
        models.VoteActivity.ActivityType.ACCEPT_OLD: config.ACCEPT_ANSWER_OLD_QUESTION_CHANGE,
    }
    source_username = source.username if source else None
    if activity_type not in rep_change_map:
        logger.warning(f'Activity type {activity_type} unknown')
        rep_change = 0
    else:
        rep_change = rep_change_map[activity_type]
    logger.debug(
        f"Create activity by {source_username}: "
        f"{rep_change} for {target.username} on {userinput.get_model()} {userinput.id}"
    )

    exist = models.VoteActivity.objects.filter(
        source=source,
        target=target,
        question=userinput.get_question(),
        answer=userinput.get_answer(),
        type=activity_type,
    ).first()
    if exist is not None:
        logger.warning("Activity already exist, exiting")
        return exist
    activity = models.VoteActivity.objects.create(
        source=source,
        target=target,
        question=userinput.get_question(),
        answer=userinput.get_answer(),
        reputation_change=rep_change,
        type=activity_type,
    )
    recalculate_user_reputation(target)
    return activity


def delete_activity(
        source: AbstractUser,
        target: AbstractUser,
        userinput: models.UserInput,
        activity_type: Optional[models.VoteActivity.ActivityType],
) -> None:
    """Find an activity with parameters and delete it
    :param source: Originator of VoteActivity (upvoter, downvoter, ...)
    :param target: Target of VoteActivity who will earn the rep-points
    :param userinput: Input the VoteActivity is on (can be Question or Answer)
    :param activity_type: Type of activity
    """
    activity_qs = models.VoteActivity.objects.filter(
        source=source,
        target=target,
        question=userinput.get_question(),
        answer=userinput.get_answer(),
    )
    if activity_type is not None:
        activity_qs = activity_qs.filter(type=activity_type)
    activity = activity_qs.first()
    if activity is None:
        logger.warning(
            f"Tried deleting activity by {source.username} with type {activity_type} for {target.username} "
            f"on {userinput.get_model()} {userinput.id} but could not find such activity"
        )
        return

    logger.debug(
        f"Delete activity by {source.username}: "
        f"{activity_type} for {target.username} on {userinput.get_model()} {userinput.id}"
    )
    activity.delete()
    recalculate_user_reputation(target)


# ======== Question methods ================


def _get_tag(tag_word: str, user: AbstractUser) -> Tag:
    """
    Get tag with tag_word.
    If no tag with the tag_word is found, check for a synonym with tag_word.
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
    if "type" not in kwargs:
        kwargs["type"] = models.Question.PostType.ARTICLE
    return create_question(user, title, content, tags, **kwargs)


def create_question(
        user: AbstractUser,
        title: str,
        content: str,
        tags: str,
        send_notifications: bool = True,
        **kwargs,
) -> models.Question:
    """Create a question in the DB, add tags to the question and notify tag followers about new question.
    :param user: Question author
    :param title: question title
    :param content: question content
    :param tags: tags to include, as string, separated by commas
    :param send_notifications: should notifications be sent? On by default
    :param kwargs:
        Other params to include in Question.objects.create,
        e.g., anonymous flag
    :return: the question created.
    """
    q = models.Question.objects.create(title=title, content=content, author=user, **kwargs)
    create_follow(q, user)
    question_tag_words = set(tags.replace(" ", "").lower().split(","))
    if "" in question_tag_words:
        question_tag_words.remove("")
    for tag_word in question_tag_words:
        tag: Tag = _get_tag(tag_word, user)
        q.tags.add(tag)
        follow_models.create_follow_tag(tag, user)
    q.save()
    if send_notifications:
        notifications.notify_tag_followers_new_question(
            user,
            question_tag_words,
            q,
        )
    jobs.start_job(jobs.update_user_tag_stats, q.id, user.id)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Create post"])
    return q


def update_question(user: AbstractUser, q: models.Question, title: str, content: str, tags: str) -> models.Question:
    """Update question content if there are changes
    :param user: User who is updating the post model
    :param q: Question to be updated
    :param title: new title
    :param content: new content
    :param tags: new tags, separated by comma
    :returns: the updated Question
    """
    curr_tag_words = set(q.tag_words())
    new_tag_words = set(tags.replace(" ", "").lower().split(","))
    if "" in new_tag_words:
        new_tag_words.remove("")
    if q.title == title and q.content == content and curr_tag_words == new_tag_words:
        logger.info(f"No changes when updating question {q.id}, returning")
        return q
    old_title = q.title
    old_content = q.content
    q.title = title
    q.content = content
    if user != q.author:
        # If user updating is not the author, add them as editor and create edit reputation for them
        q.editor = user
        create_activity(None, user, q, models.VoteActivity.ActivityType.EDITED)
    tags_to_remove = curr_tag_words.difference(new_tag_words)
    for tag_word in tags_to_remove:
        tag = Tag.objects.get(tag_word=tag_word)
        q.tags.remove(tag)
    tags_to_add = new_tag_words.difference(curr_tag_words)
    for tag_word in tags_to_add:
        tag = _get_tag(tag_word, user)
        q.tags.add(tag)
        follow_models.create_follow_tag(tag, q.author)
    jobs.start_job(jobs.update_user_tag_stats, q.id, q.author.id)
    q.last_activity = timezone.now()
    q.save()
    create_follow(q, user)
    notifications.notify_question_changes(user, q, old_title, old_content)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Update post"])
    return q


def delete_question(question: models.Question) -> None:
    answers_list = list(question.answer_set.all().using("default"))
    for answer in answers_list:
        delete_answer(answer)
    jobs.start_job(tag_jobs.update_tag_stats)
    author = question.author
    editor = question.editor
    question.delete()
    recalculate_user_reputation(author)
    recalculate_user_reputation(editor)


# Answers method


def create_answer(
        content: str,
        user: AbstractUser,
        question: models.Question,
        send_notifications: bool = True,
) -> Optional[models.Answer]:
    if content is None or content.strip() == "":
        logger.warning("Trying to create answer without content, ignoring")
        return None
    if question is None:  # Should not happen since it is tested in view
        logger.warning("Trying to create answer without question, ignoring")
        return None
    if question.answer_set.filter(author=user).count() > 0:
        logger.warning(f"User {user.username} already answered question, please update existing answer")
        return None
    # Protect creating answers on posts that do not accept answer
    if not question.is_accepting_answers:
        logger.warning(f"User {user.username} is trying to answer a post {question.id} that does not accept answer")
        return None
    a = models.Answer.objects.create(content=content, author=user, question=question)
    tags = a.question.tags.all()
    for tag in tags:
        follow_models.create_follow_tag(tag, user)
    jobs.start_job(jobs.update_user_tag_stats, a.question_id, user.id)
    create_follow(question, user)
    if send_notifications:
        notifications.notify_new_answer(user, a)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Create post"])
    return a


def update_answer(user: AbstractUser, answer: models.Answer, content: str) -> models.Answer:
    if content == answer.content:
        logger.info("no changes when updating answer, ignoring")
        return answer
    old_content = answer.content
    answer.content = content
    if user != answer.author:
        answer.editor = user
        create_activity(None, user, answer, models.VoteActivity.ActivityType.EDITED)
    answer.save()
    notifications.notify_answer_changes(user, answer, old_content)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Update post"])
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
    delete_activity(user, model_obj.author, model_obj, models.VoteActivity.ActivityType.UPVOTE)
    return model_obj


def undo_downvote(user: AbstractUser, model_obj: models.VotableUserInput) -> models.VotableUserInput:
    model_obj.users_downvoted.remove(user)
    model_obj.save()
    delete_activity(user, model_obj.author, model_obj, models.VoteActivity.ActivityType.DOWNVOTE)
    return model_obj


def upvote(user: AbstractUser, model_obj: models.VotableUserInput) -> models.VotableUserInput:
    if model_obj.users_downvoted.filter(id=user.id).count() > 0:
        logger.debug(f"User {user.username} previously downvoted, removing downvote first")
        undo_downvote(user, model_obj)

    model_obj.users_upvoted.add(user)
    model_obj.save()
    create_follow(model_obj.get_question(), user)
    create_activity(user, model_obj.author, model_obj, models.VoteActivity.ActivityType.UPVOTE)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Upvote"])
    return model_obj


def downvote(user: AbstractUser, model_obj: models.VotableUserInput) -> models.VotableUserInput:
    if model_obj.users_upvoted.filter(id=user.id).count() > 0:
        logger.info(f"User {user.username} previously downvoted, removing downvote first")
        undo_upvote(user, model_obj)

    model_obj.users_downvoted.add(user)
    model_obj.save()
    create_follow(model_obj.get_question(), user)
    create_activity(user, model_obj.author, model_obj, models.VoteActivity.ActivityType.DOWNVOTE)
    return model_obj


def accept_answer(answer: models.Answer) -> None:
    """Mark an answer as accepted answer.
    :param answer: Answer to mark
    :returns: None
    """
    if answer is None:
        return
    answer.question.answer_set.update(is_accepted=False)
    answer.question.has_accepted_answer = True
    answer.is_accepted = True
    answer.save()
    logger.info(f"Answer {answer.id} marked as accepted for question {answer.question_id}")


# Comment method
def create_comment(content: str, user: AbstractUser, parent: models.UserInput) -> Optional[models.Comment]:
    if content is None or content.strip() == "":
        logger.warning("Trying to create comment without content, ignoring")
        return None
    if parent is None:  # should never happen
        logger.warning("Trying to create comment without parent, ignoring")
        return None
    if isinstance(parent, models.Question):
        comment = models.QuestionComment.objects.create(content=content, author=user, question=parent)
    else:  # isinstance(parent,models.Answer)
        comment = models.AnswerComment.objects.create(content=content, author=user, answer=parent)
    q = comment.get_question()
    notifications.notify_new_comment(user, parent, comment)
    create_follow(q, user)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Create comment"])
    return comment


def delete_comment(comment: models.Comment) -> None:
    logger.debug(f"deleting {comment.pk}")
    delete_follow(comment.get_question(), comment.author)
    comment.delete()


def upvote_comment(user: AbstractUser, comment: models.Comment) -> models.Comment:
    comment.users_upvoted.add(user)
    comment.votes += 1
    comment.save()
    comment.get_question().last_activity = timezone.now()
    comment.get_question().save()
    return comment


def get_user_followed_tags(user: AbstractUser) -> list[Tag]:
    tag_type = ContentType.objects.get(app_label="tags", model="tag")
    follows = Follow.objects.filter(user=user, content_type=tag_type)
    return [f.content_object for f in follows]


def create_invites_and_notify_invite_users_to_question(
        inviter: AbstractUser, invitees: List[AbstractUser], post: models.Question
) -> int:
    """Generate invitations for user to participate in a post.

    Args:
        inviter: User who invited
        invitees: Collection of users to be invited
        post: Post to invite to

    Returns:
        Number of invitations created

    """
    invited_list = []
    for invitee in invitees:
        if inviter == invitee:
            logger.debug(f"User {inviter.username} invited itself to post[{post.id}] => skipping")
            continue
        existing = PostInvitation.objects.filter(
            question=post,
            inviter=inviter,
            invitee=invitee,
        ).first()
        if existing is not None:
            logger.debug(
                f"User {inviter.username} invited {invitee.username} to"
                f" post[{post.id}] but user is already invited => skipping"
            )
        if existing is None:
            PostInvitation.objects.create(
                question=post,
                inviter=inviter,
                invitee=invitee,
            )
            invited_list.append(invitee)
    logger.debug(f"Created {len(invited_list)} invitations: [{invited_list}]")
    notifications.notify_invite_users_to_question(inviter, post, invited_list)
    return len(invited_list)


# ======== General methods ================


_POST_TYPE_TO_VIEW_NAME = {
    models.Question.PostType.QUESTION.value: "forum:thread",
    models.Question.PostType.ARTICLE.value: "articles:detail",
    models.Question.PostType.HOWTO.value: "articles:detail",
    models.Question.PostType.DISCUSSION.value: "TBD",  # todo
}


def get_view_name_for_post_type(post: models.Question) -> str:
    return _POST_TYPE_TO_VIEW_NAME[post.type]


_MODELS_MAP = {
    "article": models.Question,
    "question": models.Question,
    "answer": models.Answer,
    "comment_answer": models.AnswerComment,
    "comment_question": models.QuestionComment,
    "tag": Tag,
}


def get_model(model_name: str, pk: int) -> Optional[Model]:
    """Get a model instance based on model name and primary key
    :param model_name: model name to look for, based on MODELS_MAP dictionary
    :param pk: primary key to look for
    :returns: the instance of the model with the primary key, or None if not found
    """
    if model_name is None or model_name not in _MODELS_MAP:
        logger.error(f"Attempt to get model {model_name} which is not supported")
        raise NotImplementedError
    try:
        q = _MODELS_MAP[model_name].objects.get(pk=pk)
    except _MODELS_MAP[model_name].DoesNotExist:
        q = None
    return q


_MODERATOR_ACTIONS = {"edit", "delete"}


def user_has_perm(action: str, user: ForumUser, model: str, pk: int) -> bool:
    """Check whether the user has permissions to perform action on a model instance
    :param action: action to check
    :param user: user to check
    :param model: model to check
    :param pk: the primary key of the model instance
    :returns: True if user has permission, False otherwise
    """
    if user.is_staff or user.is_superuser:
        return True
    ins = get_model(model, pk)
    author = getattr(ins, "author", None)
    if author == user:
        return True
    if model in _MODELS_MAP and user.is_moderator:
        return True
    return False

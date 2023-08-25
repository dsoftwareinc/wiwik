from typing import Union, List

from django.conf import settings
from scheduler import job
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.models.blocks import InputBlock, PlainTextInputElement, ExternalDataMultiSelectElement, SectionBlock, \
    TextObject, LinkButtonElement, DividerBlock, HeaderBlock
from slack_sdk.models.views import View
from slack_sdk.signature import SignatureVerifier

from wiwik_lib.utils import CURRENT_SITE
from forum.apps import logger
from forum.models import Question
from forum.views import utils
from forum.views.common import get_model_url_with_base
from userauth.models import ForumUser


def configure_slack_client():
    if settings.SLACK_BOT_TOKEN is None:
        logger.info('Slack integration disabled')
        return None
    else:
        logger.info('Slack integration enabled')
        return WebClient(settings.SLACK_BOT_TOKEN)


slack_client = configure_slack_client()


@job
def slack_post_channel_message(
        text: str, channel: str, thread_ts: str = None, notification_text: str = None):
    if settings.SLACK_BOT_TOKEN is None:
        return
    blocks = [SectionBlock(text=TextObject(text=text, type='mrkdwn')), ]
    try:
        logger.info(f'sending text msg to channel {channel}: {text}')
        slack_client.chat_postMessage(channel=channel,
                                      text=notification_text or text,
                                      thread_ts=thread_ts,
                                      blocks=blocks,
                                      mrkdwn=True)
    except SlackApiError as e:
        logger.warning(f"Got an error while posting to channel {channel}: {e.response['error']}")


def _get_slack_userid(email: str):
    user = ForumUser.objects.filter(email=email).first()
    if user is None:
        logger.warning(f"Couldn't find forum user for email {email}")
        return None
    if not user.slack_userid:
        try:
            response = slack_client.users_lookupByEmail(email=email)
            if not response['ok']:
                logger.warning(f"Couldn't find slack user for email {email}, slack error: {response['error']}")
                return None
            user.slack_userid = response['user']['id']
            user.save()
        except SlackApiError as e:
            logger.warning(f"Couldn't find slack user for email {email}, slack error: {e.response['error']}")
            return None
    return user.slack_userid


def _get_forumuser_by_slack_userid(slack_user_id: str) -> Union[ForumUser, None]:
    user = ForumUser.objects.filter(slack_userid=slack_user_id).first()
    if user is not None:
        return user
    try:
        response = slack_client.users_info(user=slack_user_id)
        if not response['ok']:
            logger.warning(f"Couldn't find slack user {slack_user_id}, slack error: {response['error']}")
            return None
        email = response.get('user', {}).get('profile', {}).get('email', None)
        user = ForumUser.objects.filter(email=email).first()
        if user is None:
            logger.warning(f"Couldn't find forum user for slack user {slack_user_id} with email: {email}")
            return None
        user.slack_userid = slack_user_id
        user.save()
        return user
    except SlackApiError as e:
        logger.warning(f"Couldn't find slack user {slack_user_id}, slack error: {e.response['error']}")
        return None


def _get_permalink(channel: str, message_ts: str) -> Union[str, None]:
    try:
        response = slack_client.chat_getPermalink(channel=channel, message_ts=message_ts)
        if not response['ok']:
            logger.warning(f"Couldn't find permalink to {channel}:{message_ts}, slack error: {response['error']}")
            return None
        return response.get('permalink', None)
    except SlackApiError as e:
        logger.warning(f"Couldn't find permalink to {channel}:{message_ts}, slack error: {e.response['error']}")
        return None


@job
def slack_post_im_message_to_email(text: str, email: str, notification_text: str = None):
    if settings.SLACK_BOT_TOKEN is None:
        return
    try:
        logger.info(f'sending text msg to email {email}: {text}')
        user_id = _get_slack_userid(email)
        if user_id is None:
            logger.warning(f"slack user for {email} not found, returning")
            return
        blocks = [SectionBlock(text=TextObject(text=text, type='mrkdwn')), ]
        slack_client.chat_postMessage(
            channel=user_id, text=notification_text or text, blocks=blocks, mrkdwn=True)
    except SlackApiError as e:
        logger.warning(f"Got an error: {e.response['error']}")


def slack_post_question_modal(user_id: str, text: str, post_id: str) -> View:
    return View(
        "modal",
        title="Post it to wiwik!",
        callback_id="post_wiwik",
        submit="Post",
        private_metadata=post_id,
        blocks=[
            InputBlock(
                block_id='title',
                label="Question title",
                element=PlainTextInputElement(action_id="title_id", multiline=False, placeholder='Question title'),
                optional=False),
            InputBlock(
                block_id='text',
                label="Question text",
                element=PlainTextInputElement(action_id="text_id", multiline=True, initial_value=text),
                optional=False),
            InputBlock(
                block_id='tags',
                label='Tags',
                optional=True,
                element=ExternalDataMultiSelectElement(
                    action_id='tags_id', placeholder='Tags', max_selected_items=5, )
            ),
            # todo Decide whether we want to allow in cases that a user
            #      will post for another user
            # InputBlock(
            #     block_id='author',
            #     label="Post question by",
            #     element=UserSelectElement(action_id="user_id", initial_user=user_id),
            #     optional=False),
        ]
    )


def slack_already_posted_modal(question: Question) -> View:
    question_url = get_model_url_with_base('question', question)
    return View(
        "modal",
        title="Already posted!",
        callback_id="post_wiwik",
        blocks=[
            SectionBlock(
                text=TextObject(text='This message was already posted', type='mrkdwn'),
                accessory=LinkButtonElement(text='Go to question', url=question_url)
            ),
        ]
    )


def _slack_view(payload: dict) -> View:
    message = payload['message']
    message_ts = message.get('thread_ts', message['ts'])
    # channel = payload['channel']['name']
    channel_id = payload['channel']['id']
    existing_question_data = Question.objects.filter(
        source='slack', source_id=f'{channel_id}:{message_ts}').first()
    if existing_question_data is None:
        slack_view = slack_post_question_modal(
            payload['user']['id'], payload['message']['text'], f"{channel_id}~~{message_ts}")
    else:
        slack_view = slack_already_posted_modal(existing_question_data.question)
    return slack_view


def post_from_slack(payload: dict) -> None:
    originator_slack_id = payload.get('user', {}).get('id', None)
    originator = _get_forumuser_by_slack_userid(originator_slack_id)
    if originator is None:
        blocks = [SectionBlock(text=TextObject(
            text=f'You are not signed up to wiwik. '
                 f'Please register <{CURRENT_SITE}|here> before you can post questions',
            type='mrkdwn')), ]
        slack_client.chat_postMessage(channel=originator_slack_id,
                                      blocks=blocks,
                                      mrkdwn=True)
        return
    if payload['type'] == 'message_action':
        slack_view = _slack_view(payload)
        try:
            slack_client.views_open(
                trigger_id=payload['trigger_id'], view=slack_view, )
        except SlackApiError as e:
            logger.warning(f"Got an error: {e.response['error']}")
    elif payload['type'] == 'view_submission':
        try:

            view = payload['view']
            values = view['state']['values']
            title = values['title']['title_id']['value']
            text = values['text']['text_id']['value']
            tags = values['tags']['tags_id']['selected_options']
            tags = [i['value'] for i in tags]
        except KeyError as e:
            logger.error(f'Slack payload does not have expected format. payload={payload},e={e}')
            return
        # author_slack_id = values['author']['user_id']['selected_user']
        # author = _get_forumuser_by_slack_userid(author_slack_id)
        logger.debug(f'{originator} posted from slack question[title={title}, '
                     f'text={text}, author={originator}, tags={tags}]')
        # actually creating the question.
        channel_id, message_ts = view['private_metadata'].split('~~')
        link = _get_permalink(channel_id, message_ts)
        q = utils.create_question(originator, title, text, ','.join(tags))
        q.source = 'slack'
        q.source_id = f'{channel_id}:{message_ts}'
        q.link = link
        q.save()
        # posting response to slack thread
        question_url = get_model_url_with_base('question', q)
        slack_post_channel_message(
            f'Posted as question to wiwik: <{question_url}|"{title}">',
            channel_id, thread_ts=message_ts)


def verify_request(request) -> bool:
    body = request.body
    timestamp = request.headers.get("x-slack-request-timestamp", None)
    signature = request.headers.get("x-slack-signature", None)
    verifier = SignatureVerifier(signing_secret=settings.SLACK_SIGNING_SECRET_KEY)
    return verifier.is_valid(body, timestamp, signature)


def questions_message(questions: List[Question]) -> List:
    blocks = []
    for question in questions:
        question_url = get_model_url_with_base('question', question)
        blocks.append(
            HeaderBlock(text=question.title, ).to_dict()
        )
        content = question.content
        content = '\r\n'.join(content.split('\r\n')[:4]) + '...'
        blocks.append(
            SectionBlock(
                text=TextObject(text=content, type='mrkdwn'),
                accessory=LinkButtonElement(text='Go to question', url=question_url),
            ).to_dict()
        )
        blocks.append(DividerBlock().to_dict())
    return blocks

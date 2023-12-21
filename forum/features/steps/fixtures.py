from behave import fixture

from forum.models import Question, Answer
from userauth.models import ForumUser


@fixture
def create_users(context):
    context.default_user_password = "magicalPa$$w0rd"
    context.usernames = [
        "myuser_name1",
        "myuser_name2",
        "myuser_name3",
    ]
    context.users = [
        ForumUser.objects.create_user(
            username=username,
            email=f"{username}@a.com",
            password=context.default_user_password,
        )
        for username in context.usernames
    ]


@fixture
def create_question_with_answer(context):
    context.question_details = dict(
        title="my_question_title",
        content="my_question_content_with more than 20 chars",
    )
    context.answer_details = dict(
        content="answer------content",
    )
    context.question = Question.objects.create(
        author=context.users[0], **context.question_details
    )
    context.answer = Answer.objects.create(
        author=context.users[1], question=context.question, **context.answer_details
    )

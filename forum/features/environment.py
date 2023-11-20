"""
behave environment module for testing behave-django
"""
from behave.fixture import use_fixture_by_tag

from features.steps.fixtures import create_users, create_question_with_answer

fixture_registry = {
    "fixture.users.exist": create_users,
    "fixture.question.with_answer": create_question_with_answer,
}


def before_tag(context, tag):
    if tag.startswith("fixture."):
        return use_fixture_by_tag(tag, context, fixture_registry)


def before_feature(context, feature):
    pass

def before_scenario(context, scenario):
    pass


def django_ready(context):
    context.django = True

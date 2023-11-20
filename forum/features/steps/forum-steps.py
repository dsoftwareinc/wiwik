from behave import given, when, then
from bs4 import BeautifulSoup
from django.urls import reverse


@given(u'logged in with user number {user_number:d}')
def login(context, user_number: int):
    context.test.client.login(username=context.usernames[user_number], password=context.default_user_password)


@then("The user should not have bookmarks in the user-navbar bookmarks")
def assert_no_bookmarks(context):
    res = context.test.client.get(reverse('forum:user_navbar'), follow=True)
    context.test.assertContains(res, 'No bookmarks')


@then("The user should have the question in the user-navbar bookmarks")
def assert_bookmark_in_navbar(context):
    res = context.test.client.get(reverse('forum:user_navbar'), follow=True)
    soup = BeautifulSoup(res.content, 'html.parser')

    bookmark_url = reverse('forum:thread', kwargs={'pk': context.question.pk})
    context.test.assertEqual(1, len(soup.select(f'a[href="{bookmark_url}"]')))


@when("The user bookmark the question")
def bookmark_question(context):
    context.test.client.get(reverse('forum:bookmark', args=[context.question.pk]), follow=True)


@when("The user remove the question's bookmark")
def remove_bookmark(context):
    context.test.client.get(reverse('forum:unbookmark', args=[context.question.pk]), follow=True)


@then(u"user {user_number:d} should not have votes in the user-navbar votes")
def assert_no_votes_in_navbar(context, user_number: int):
    context.test.client.login(username=context.usernames[user_number], password=context.default_user_password)
    res = context.test.client.get(reverse('forum:user_navbar'), follow=True)
    soup = BeautifulSoup(res.content, 'html.parser')

    bookmark_url = reverse('forum:thread', kwargs={'pk': context.question.pk})
    context.test.assertEqual(0, len(soup.select(f'a[href="{bookmark_url}"]')))


@then(u"user {user_number:d} should have votes in the user-navbar votes")
def assert_votes_in_navbar(context, user_number: int):
    context.test.client.login(username=context.usernames[user_number], password=context.default_user_password)
    res = context.test.client.get(reverse('forum:user_navbar'), follow=True)
    soup = BeautifulSoup(res.content, 'html.parser')

    bookmark_url = reverse('forum:thread', args=[context.question.pk])
    context.test.assertEqual(1, len(soup.select(f'a[href="{bookmark_url}"]')))


@when(u"user {user_number:d} upvote the question")
def user_upvote(context, user_number: int):
    context.test.client.login(username=context.usernames[user_number], password=context.default_user_password)
    res = context.test.client.get(
        reverse('forum:upvote', args=[context.question.pk, 'question', context.question.pk]),
        follow=True)
    assert res.status_code == 200


@when(u"user {user_number:d} downvote the question")
def user_downvote(context, user_number: int):
    context.test.client.login(username=context.usernames[user_number], password=context.default_user_password)
    res = context.test.client.get(
        reverse('forum:downvote', args=[context.question.pk, 'question', context.question.pk]),
        follow=True)
    assert res.status_code == 200

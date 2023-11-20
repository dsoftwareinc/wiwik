Feature: User nav-bar tests

    @fixture.users.exist @fixture.question.with_answer
    Scenario: Test that bookmarking works
        Given logged in with user number 0
        Then The user should not have bookmarks in the user-navbar bookmarks
        When The user bookmark the question
        Then The user should have the question in the user-navbar bookmarks
        When The user remove the question's bookmark
        Then The user should not have bookmarks in the user-navbar bookmarks

    @fixture.users.exist @fixture.question.with_answer
    Scenario: Test that voting appears on navbar and disappears when undone
        Then user 0 should not have votes in the user-navbar votes
        When user 1 upvote the question
        Then user 0 should have votes in the user-navbar votes
        When user 1 upvote the question
        Then user 0 should not have votes in the user-navbar votes
        When user 1 downvote the question
        Then user 0 should have votes in the user-navbar votes
        When user 1 downvote the question
        Then user 0 should not have votes in the user-navbar votes

    @fixture.users.exist @fixture.question.with_answer
    Scenario: Test that voting works only when voter is not the author
        When user 0 upvote the question
        Then user 0 should not have votes in the user-navbar votes
        When user 0 downvote the question
        Then user 0 should not have votes in the user-navbar votes

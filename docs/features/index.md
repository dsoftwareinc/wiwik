---
markdown_extensions:

    -   toc:
        permalink: True
        toc_depth: 4

---

# Features

## List of active features

### Forum functionality

The main purpose of wiwik is to serve as a platform for your developers to
quickly find answers for what they need. If they could not find it with the
existing data, they can post it as a new question for other developers to
answer.

- <details>
    <summary>Homepage for user</summary>
    <img src="/media/wiwik-home-short.jpg" alt=""/>
  </details>
- <details>
    <summary>Post view</summary>
    <img src="/media/wiwik-thread.jpg" alt=""/>
  </details>
- <details>
    <summary>Post with charts and LaTeX</summary>
    <img src="/media/wiwik-post-mermaidjs.jpg" alt=""/>
  </details>

- [Search existing posts.](./search.md)
- Post/edit questions and answers with Markdown, LaTeX and mermaidjs
  support.
- (Optional) Post question anonymously.
- Comment on questions/answers.
- Upvote/downvote posts enable measuring post relevancy and tracking of
  users' reputation.
- Bookmark thread for faster future access.
- Follow thread to get notifications on new activity.
- Dark/light mode
- [Invite to answer question](./invitation.md)
- Moderation (edit/delete posts)
- Flags
    - Users can flag posts/comments as duplicate/unclear/etc. and moderators can
      review flags and act upon them.
- Articles
    - New posts as articles, good for summarizing repetitive issues.
- Drafts (Roadmap)
    - Create new posts (Both Q&A) as drafts to be reviewed by moderators before they show up in wiwik.
      Crawlers can generate drafts as well.

### Notifications (emails)

- New activity on a tag/post user is following
- Weekly report for user
- Manager report on users' activity.

### Authentication/Authorization

* Ability to track user activity and limit what they can do.
* Seamless integration with external authentication systems such as:
  google, facebook, okta, LDAP.

### User profile management

- See user activity
- Edit profile
- Moderation (Deactivate user)
- Screenshots
    - <details>
          <summary>List of users</summary>
          <img src="/media/wiwik-users.jpg" alt=""/>
      </details>
    - <details>
          <summary>User profile</summary>
          <img src="/media/wiwik-profile.jpg" alt=""/>
      </details>

### Tags

* Follow tags.
* Edit tag description + info page.
* Tag leaders/rising stars.
* Screenshots
    - <details>
        <summary>List of tags</summary>
        <img src="/media/wiwik-tags.jpg" alt=""/>
      </details>
    - <details>
        <summary>Tag info view</summary>
        <img src="/media/wiwik-tag-info.jpg" alt=""/>
      </details>

### [Questions similarity (Related questions)](./similarity.md)

### [Slack integration](./slack.md)

- Search wiwik from Slack using `/wiwik` command
- Convert a Slack thread to a new wiwik post
- Get notified via Slack on new relevant activity
- Get admin notifications (when new user sign-up, etc.)

### [Badges](./badges.md)

- Gamification of wiwik. Add awards
- Screenshots
    - <details>
          <summary>List of badges</summary>
          <img src="/media/wiwik-badges.jpg" alt=""/>
      </details>
    - <details>
          <summary>Single badge info</summary>
          <img src="/media/wiwik-badge-single.jpg" alt=""/>
      </details>

### RSS feed

- Data is exposed as RSS feed.

## Under development

- [ ] Sub-communities: allow posts to belong to private communities
- [ ] Questions drafts
- [ ] Articles (Blogs)
- [ ] Microsoft Teams notifications
- [ ] GitHub view of user activity
- [ ] Soft-delete of posts
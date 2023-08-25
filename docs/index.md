# About

wiwik (What I wish I knew) is a knowledge management system aimed to be used
by tech companies.

> :information_source: wiwik follows the sponsorware release strategy, which
> means that new features are first exclusively released to sponsors as part
> of [wiwik-insiders](./wiwik-insiders.md). Click the link to understand how
> to get access to wiwik-insiders and what's in it for you.

In most tech organizations, developers ask other developers in messaging
applications. This interrupts developers answering, and the impact is
amplified for the developers answering as they have to restart their
work (i.e., context-switch). Senior developers dedicate 30-60% of their
time to answering such questions, which prevents them from delivering
features:
> "Interruption-driven work environments lead to lower-quality
> decisions and reduce speed on complex tasks...
> Distracted workers tend to skip or put off tasks with high value,
> like planning and problem-solving." [^1]

As the codebase of the company grows, there is an increased difficulty collecting, updating, and sharing developer
standards. Maintaining up-to-date documentation is a tedious task, and expecting developers to know where to look for
the part relevant to their specific work is not realistic.

## The solution wiwik offer

For developers, an environment with stack overflow look & feel, with:

- Easy to search and find concise answers (unlike documentation) ranked by developers like them.
- No answering the same question twice.
- Recognition for sharing knowledge, i.e., answering questions, which private messages do
  not offer.
- Living documentation as Q&A.
- Ability to be notified about new posts around what interests them.
- Fully integrated with Slack: Search from Slack, convert Slack msg to question,
  notifications, etc.

For technical managers, the ability to identify:

- Gaps in documentation and boarding process.
- Areas in the code that require attention.
- Experts in specific areas within the development team.

General

- wiwik is deployed on company “territory” and it can be leveraged for any analysis not offered directly by wiwik
  features. Also, the company can adjust the server capacity.
- Resource requirements to manage wiwik are minimal:
- Schedule some upfront question-and-answer seeding.
- Ongoing moderation and management are mostly done by its active users.

## Supported features

- [x] Ask and answer questions (Optional: also anonymously)
- [x] Similar questions while typing the title of new question
- [x] Comment on question/answer (and delete your own comments)
- [x] Accept answer as the correct answer
- [x] Upvote/Downvote question/answer
- [x] Bookmark thread (thread is question+its answers)
- [x] Follow thread (be notified whenever there is an activity on thread)
- [x] View user profiles including all data about them (questions/answers/votes/reputation/bookmarks)
- [x] Dark/light mode
- [x] Edit and delete your own question/answer
- [x] Download thread as markdown
- [x] Login with Google, facebook
- [x] Follow tags (be notified about activity on tag)
- [x] Add/edit tag descriptions
- [x] Search
- [x] All inputs support Markdown, LaTeX and mermaidjs
- [x] Email notifications regarding followed tags/threads
- [x] Invite others to answer a question
- [x] Forum moderation:
    - [x] Edit and delete questions/answers
- [x] Related questions
- [x] Slack integration
- [x] Badges (gamification)
- [x] Tags as wiki pages
- [x] Digest report, usage reports, etc.
- [x] Tag info pages as documentation
- [x] Ability to deactivate users as staff user
- [x] RSS feed
- [x] Articles (Blogs)

### Under development

- [ ] Sub-communities: allow posts to belong to private communities
- [ ] Questions drafts
- [ ] Microsoft Teams notifications
- [ ] GitHub view of user activity
- [ ] Soft-delete of posts

[^1]: [“Engineer Your Technology Environment To Improve Employee
Productivity And Flow,” Forrester Research, Inc., December 15, 2017.](
https://www.forrester.com/report/Engineer+Your+Technology+Environment+To+Improve+Employee+Productivity+And+Flow/-/E-RES113826#dialog-1573174355745-dialog)
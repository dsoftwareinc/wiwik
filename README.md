About
=====
![badge](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/cunla/b756396efb895f0e34558c980f1ca0c7/raw/wiwik.json)

![](https://img.shields.io/badge/Made_with-Django-blue?style=for-the-badge&logo=Django)

wiwik (What I wish I knew) is a knowledge management system aimed to be used by tech companies.

In most tech organizations, developers ask other developers in messaging applications. This interrupts developers
answering, and the impact is amplified for the developers answering as they have to restart their work (i.e.,
context-switch). Senior developers dedicate 30-60% of their time to answering such questions, which prevents them from
delivering features:
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
- Recognition for sharing knowledge, i.e., answering questions, which private messages do not offer.
- Living documentation as Q&A.
- Ability to be notified about new posts around what interests them.
- Fully integrated with Slack: Search from Slack, convert slack msg to post, notifications, etc.

For technical managers, the ability to identify:

- Gaps in documentation and onboarding process.
- Areas in the code that require attention.
- Experts in specific areas within the development team.

General

- wiwik is deployed on company “territory” and it can be leveraged for any analysis not offered directly by wiwik
  features. Also, the company can adjust the server capacity.
- Resource requirements to manage wiwik are minimal:
- Schedule some upfront question-and-answer seeding.
- Ongoing moderation and management is mostly done by its active users.

## Development guidelines

- [How to write commit messages](https://chris.beams.io/posts/git-commit/)
- Make sure you work on an issue-open one if one does not exist and add it to
  the [project sprint](https://github.com/orgs/dsoftwareinc/projects/1/views/1).
- Work on your own branch with as many commits as needed.
- When ready:
    - merge `master` branch to your own branch to avoid conflicts.
    - run tests using `./scripts/run_tests.sh` - ensure all tests passed. A coverage report will be generated
      in `coverage_report.txt`.
    - create a pull request, include the text from `coverage_report.txt` in it and assign one or more reviewers. Once
      approved - squash/merge to the `master` branch.
- You will notice notifications to DSoftware slack space whenever a new issue is opened, a PR is created, etc.

[^1]: [“Engineer Your Technology Environment To Improve Employee
Productivity And Flow,” Forrester Research, Inc., December 15, 2017.](
https://www.forrester.com/report/Engineer+Your+Technology+Environment+To+Improve+Employee+Productivity+And+Flow/-/E-RES113826#dialog-1573174355745-dialog)
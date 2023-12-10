# Environment variables

## Forum site configuration

- `ADMIN_EMAIL`
  email to send logs to when an error happens.

- `FAVICON_LINK_LIGHT` & `FAVICON_LINK_DARK`

- `ALLOWED_REGISTRATION_EMAIL_DOMAINS`
  Domains where users should be allowed to sign up from separated by space.
  Users that are not from these domains won't be allowed to sign up.

### Question settings

- `MIN_QUESTION_CONTENT_LENGTH` & `MAX_QUESTION_CONTENT_LENGTH`
  Defaults: 20 and 30000.

- `MIN_QUESTION_TITLE_LENGTH` & `MAX_QUESTION_TITLE_LENGTH`
  Defaults: 15 and 150.

- `MAX_ANSWERS_ON_QUESTION`
  Maximum number of answers allowed on questions.
  Meant to avoid creating a long thread discussion.

- `MAX_COMMENTS`
  Maximum number of comments on question/answer.

- `MIN_COMMENT_LENGTH` & `MAX_COMMENT_LENGTH`
  Minimum/Maximum length of comments.
  defaults: 15 & 200.

- `QUESTIONS_PER_PAGE`

- `DAYS_FOR_QUESTION_TO_BECOME_OLD`
  Number of days for a question to become "old".
  Old unanswered questions are promoted to be answered.
  To disable the feature, set this to None.
  Default: `None`.
- `ALLOW_ANONYMOUS_QUESTION`
  Should anonymous questions be allowed.
  Default: `False`.
- `MAX_SIZE_KB_IMAGE_UPLOAD`
  Max size allowed for uploading images

### Tag settings

- `NUMBER_OF_TAG_EXPERTS`
  Number of experts (users with most reputation on tag) allowed on a tag.
  Default: 2.

- `NUMBER_OF_TAG_RISING_STARS`
  Number of rising stars (users with most reputation on tag in the last month)
  allowed on a tag. Default: 2.

### Django settings

#### `SECRET_KEY`

#### `MEDIA_ROOT` = `./forum/media`

To be used in deployment, not hard coded.

#### `DJANGO_LOG_LEVEL`

Log level, `DEBUG` by default.

#### `DJANGO_ALLOWED_HOSTS`

Django setting `ALLOWED_HOSTS` - see more
info [here](https://docs.djangoproject.com/en/4.1/ref/settings/#allowed-hosts)

### `GOOGLE_ANALYTICS_KEY`

## Development related settings

### `DEBUG`

When set to `TRUE`, django debug mode is enabled, showing error views
with stacktrace, etc.

### `SEND_EMAILS`

Another guard for sending emails, when set to `TRUE`, emails will be sent
to the real address. When set to `FALSE` (default), emails will be
sent to `DEBUG_EMAIL_TO`.

### `DEBUG_EMAIL_TO`

email address to send emails to when in `DEBUG` mode.

### `RUN_ASYNC_JOBS_SYNC`

Whether async tasks should run in the background or not.

Notice running in the background requires redis and a worker on.

## Authentication using SSO

### Okta oauth

#### `OKTA_BASE_URL`, `OKTA_CLIENT_ID` & `OKTA_SECRET_KEY`

### Google oauth

#### `GOOGLE_CLIENT_ID` & `GOOGLE_SECRET_KEY`

### Facebook oauth

#### `FACEBOOK_CLIENT_ID` & `FACEBOOK_SECRET_KEY`

## Integrations (databases, smtp, Slack, ...)

### Database settings

#### `SQL_ENGINE`, `SQL_DATABASE`, `SQL_USER`, `SQL_PASSWORD`, `SQL_HOST`, `SQL_PORT`

by default, sqlite3 will be used if these variables are not set.
When `SQL_ENGINE` is set to `django.db.backends.postgresql`, postgres backend
will be used
connecting to the host/port/db using the user/password.

### Redis cache settings

- `REDIS_CACHE_URL` (default: No cache)
  Use format `redis://127.0.0.1:6379/1`

### Redis Queue settings

The redis server host, port, password and redis-database to configure
django-queues (See more details
about [django-tasks-scheduler](https://django-tasks-scheduler.readthedocs.io/en/latest/)
here.)

By default, `localhost` if values are not set.

- `REDIS_HOST` (default: `localhost`)
- `REDIS_PORT` (default: `6379`)
- `REDIS_PASSWORD` (default: `''`)
- `REDIS_DB` (default: `0`)

### Email integration (SMTP)

- `DEFAULT_FROM_EMAIL`
  Default from address.

- `EMAIL_BACKEND`
    - `django.core.mail.backends.console.EmailBackend` - print emails to console
    - `django.core.mail.backends.smtp.EmailBackend` - Send emails using SMTP
      settings, USE WITH CAUTION DURING DEVELOPMENT!

- `EMAIL_HOST` & `EMAIL_PORT`
  When `EMAIL_BACKEND` is set to SMTP, this is the host & port of the SMTP server.

- `EMAIL_HOST_USER` & `EMAIL_HOST_PASSWORD`
  When `EMAIL_BACKEND` is set to SMTP, this is the user & password to connect to
  the SMTP server.

### Slack integration

#### `SLACK_APP_ID`, `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET_KEY`, `SLACK_SIGNING_SECRET_KEY`

#### `SLACK_VERIFICATION_TOKEN`

Used to verify requests from Slack to wiwik, requests from Slack are not
going through the regular authentication process.

#### `SLACK_BOT_TOKEN`

Used to create a Slack client to send commands from wiwik to Slack.

#### `SLACK_NOTIFICATIONS_CHANNEL`

Channel to send general notifications to:

- Notify tag followers about new questions

#### `SLACK_ADMIN_NOTIFICATIONS_CHANNEL`

Channel to send admin notifications:

- Social signup.
- email signup.

### Meilisearch integration

To integrate with meilisearch, set the following env-variables:

- `MEILISEARCH_ENABLED` (default: `False`)
- `MEILISEARCH_SERVER_ADDRESS`
- `MEILISEARCH_MASTERKEY`

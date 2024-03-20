"""
All settings related to wiwik behavior.
Most of them can be set from environment variables.
"""
import os
from datetime import timedelta

from .base import getenv_asbool, getenv_asint

USE_CDN = getenv_asbool("USE_CDN", default="TRUE")
ALLOW_USER_NOTIFICATION_SKIPPING = True  # Allow skipping notifications in certain scenarios
RUN_ASYNC_JOBS_SYNC = getenv_asbool("RUN_ASYNC_JOBS_SYNC", default="FALSE")
FAVICON_LINK_LIGHT = os.getenv("FAVICON_LINK_LIGHT", "/static/favicon-light.ico")
FAVICON_LINK_DARK = os.getenv("FAVICON_LINK_LIGHT", "/static/favicon-dark.ico")
UPVOTE_CHANGE = 10
DOWNVOTE_CHANGE = -10
ACCEPT_ANSWER_CHANGE = 15
ACCEPT_ANSWER_OLD_QUESTION_CHANGE = 100
MAX_REPUTATION_ITEMS = 10
MAX_BOOKMARK_ITEMS = 20
ALLOW_ANONYMOUS_QUESTION = getenv_asbool("ALLOW_ANONYMOUS_QUESTION", "FALSE")
MAX_ANSWERS = int(os.getenv("MAX_ANSWERS_ON_QUESTION", 3))
MAX_COMMENTS = int(os.getenv("MAX_COMMENTS", 5))
POSTGRES_SEARCH = {
    "trigram_min_relevance": 0.05,
    "weights": {
        "title": 0.7,
        "content": 0.3,
    },
}
NUMBER_OF_TAG_EXPERTS = int(os.getenv("NUMBER_OF_TAG_EXPERTS", 2))
NUMBER_OF_TAG_RISING_STARS = int(os.getenv("NUMBER_OF_TAG_RISING_STARS", 2))
DAYS_TO_REVOKE_MODERATOR = 10
DAYS_TO_GRANT_MODERATOR = 16
DAYS_FOR_QUESTION_TO_BECOME_OLD = getenv_asint("DAYS_FOR_QUESTION_TO_BECOME_OLD", None)
ANSWER_IS_RECENT_DAYS = 3
QUESTIONS_PER_PAGE = int(os.getenv("QUESTIONS_PER_PAGE", 20))
LATEX_SUPPORT_ENABLED = True
GOOGLE_ANALYTICS_KEY = os.getenv("GOOGLE_ANALYTICS_KEY", None)
SHOWCASE_DEPLOYMENT = os.getenv("SHOWCASE_DEPLOYMENT", False)

MIN_COMMENT_LENGTH = int(os.getenv("MIN_COMMENT_LENGTH", 15))
MAX_COMMENT_LENGTH = int(os.getenv("MAX_COMMENT_LENGTH", 200))
MIN_QUESTION_TITLE_LENGTH = int(os.getenv("MIN_QUESTION_TITLE_LENGTH", 15))
MAX_QUESTION_TITLE_LENGTH = int(os.getenv("MAX_QUESTION_TITLE_LENGTH", 150))
MIN_QUESTION_CONTENT_LENGTH = int(os.getenv("MIN_QUESTION_CONTENT_LENGTH", 20))
MAX_QUESTION_CONTENT_LENGTH = int(os.getenv("MAX_QUESTION_CONTENT_LENGTH", 30000))
MIN_ARTICLE_TITLE_LENGTH = int(os.getenv("MIN_ARTICLE_TITLE_LENGTH", 10))
MIN_ARTICLE_CONTENT_LENGTH = int(os.getenv("MIN_ARTICLE_CONTENT_LENGTH", 50))
MAX_ARTICLE_CONTENT_LENGTH = int(os.getenv("MAX_ARTICLE_CONTENT_LENGTH", 100_000))
# Tag edit settings
MIN_TAG_DESCRIPTION_LENGTH = 20
MAX_TAG_DESCRIPTION_LENGTH = 460
MIN_TAG_WIKI_LENGTH = 20
MAX_TAG_WIKI_LENGTH = 30000
MIN_TAG_EDIT_SUMMARY_LENGTH = 10
MAX_TAG_EDIT_SUMMARY_LENGTH = 200
MAX_SIZE_KB_IMAGE_UPLOAD_KB = int(os.getenv("MAX_SIZE_KB_IMAGE_UPLOAD_KB", 1024))

MEILISEARCH_ENABLED = getenv_asbool("MEILISEARCH_ENABLED", default="FALSE")
MEILISEARCH_SERVER_ADDRESS = os.getenv("MEILISEARCH_SERVER_ADDRESS", None)
MEILISEARCH_MASTERKEY = os.getenv("MEILISEARCH_MASTERKEY", None)
EDIT_LOCK_TIMEOUT = timedelta(minutes=5)
_admin_email = os.getenv("ADMIN_EMAIL", None)
if _admin_email is not None:
    ADMINS = [
        ("wiwik-admin", _admin_email),
    ]
    MANAGERS = [
        ("wiwik-admin", _admin_email),
    ]

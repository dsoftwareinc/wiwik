"""
All settings related to wiwik behavior.
Most of them can be set from environment variables.
"""
import os
from datetime import timedelta

from .base import getenv_asbool, getenv_asint

CONSTANCE_CONFIG = {
    'USE_CDN': (True, 'Should 3rd party libraries be downloaded using CDN', bool),
    'FAVICON_LINK_LIGHT': ("/static/favicon-light.ico", 'site favicon for light-mode', str),
    'FAVICON_LINK_DARK': ("/static/favicon-dark.ico", 'site favicon for dark-mode', str),
    'MAX_BOOKMARK_ITEMS': (20, 'Bookmarks to show on nav-bar', int),
    'MAX_REPUTATION_ITEMS': (10, 'Reputation activity to show on nav-bar', int),
    'LATEX_SUPPORT_ENABLED': (True, 'Enable LaTex support', bool),
    'GOOGLE_ANALYTICS_KEY': (os.getenv("GOOGLE_ANALYTICS_KEY", ""), 'Google Analytics key', str),
    'SHOWCASE_DEPLOYMENT': (True, 'Show link to wiwik source code', bool),
    "UPVOTE_CHANGE": (10, "Points change for upvote", int),
    "DOWNVOTE_CHANGE": (-10, "Points change for downvote", int),
    "EDITED_CHANGE": (2, "Points change for editing post", int),
    "ACCEPT_ANSWER_CHANGE": (15, "Points change for accepted answer", int),
    "ACCEPT_ANSWER_OLD_QUESTION_CHANGE": (100, "Points change for accepted answer on an old question", int),
    "ALLOW_ANONYMOUS_QUESTION": (True, "Allow posting questions anonymously", bool),
    "MIN_QUESTION_CONTENT_LENGTH": (20, "Minimum characters allowed in question body", int),
    "MAX_QUESTION_CONTENT_LENGTH": (30000, "Max characters allowed in question body", int),
    "MIN_QUESTION_TITLE_LENGTH": (15, "Minimum characters allowed in question title", int),
    "MAX_QUESTION_TITLE_LENGTH": (150, "Maximum characters allowed in question title", int),
    "MIN_COMMENT_LENGTH": (15, "Minimum characters in a comment", int),
    "MAX_COMMENT_LENGTH": (200, "Maximum characters in a comment", int),
    "MIN_ARTICLE_TITLE_LENGTH": (10, "Minimum characters in an article title", int),
    "MAX_ARTICLE_TITLE_LENGTH": (255, "Maximum characters in an article title", int),
    "MIN_ARTICLE_CONTENT_LENGTH": (50, "Minimum characters allowed in article body", int),
    "MAX_ARTICLE_CONTENT_LENGTH": (100_000, "Maximum characters allowed in article body", int),
    "MAX_ANSWERS": (3, "Maximum number of answers on a question", int),
    "MAX_COMMENTS": (5, "Maximum number of comments on a post", int),
    "QUESTIONS_PER_PAGE": (20, "Number of questions on a page", int),
    "DAYS_TO_REVOKE_MODERATOR": (10, "Number of sequential days without activity to revoke moderator permissions", int),
    "DAYS_TO_GRANT_MODERATOR": (15, "Number of sequential days with activity to grant moderator permissions", int),
    "NUMBER_OF_TAG_EXPERTS":
        (2, "Number of experts per tag (expert is a user with the most reputation on the tag)", int),
    "NUMBER_OF_TAG_RISING_STARS":
        (2, "Number of rising stars on a tag (a rising star is a user who is not an expert "
            "but has the most reputation for a tag in the past month", int),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "Web": ("USE_CDN", "FAVICON_LINK_LIGHT", "FAVICON_LINK_DARK", "GOOGLE_ANALYTICS_KEY",),
    "Forum Web settings": (
        "LATEX_SUPPORT_ENABLED", "MAX_BOOKMARK_ITEMS", "MAX_REPUTATION_ITEMS", "SHOWCASE_DEPLOYMENT",
        "ALLOW_ANONYMOUS_QUESTION", "QUESTIONS_PER_PAGE",
    ),
    "Voting configuration": (
        "UPVOTE_CHANGE", "DOWNVOTE_CHANGE", "ACCEPT_ANSWER_CHANGE", "ACCEPT_ANSWER_OLD_QUESTION_CHANGE",
        "EDITED_CHANGE",
    ),
    "Post limits": (
        "MIN_QUESTION_TITLE_LENGTH", "MAX_QUESTION_TITLE_LENGTH",
        "MIN_QUESTION_CONTENT_LENGTH", "MAX_QUESTION_CONTENT_LENGTH",
        "MIN_COMMENT_LENGTH", "MAX_COMMENT_LENGTH",
        "MIN_ARTICLE_TITLE_LENGTH", "MAX_ARTICLE_TITLE_LENGTH",
        "MIN_ARTICLE_CONTENT_LENGTH", "MAX_ARTICLE_CONTENT_LENGTH",
        "MAX_ANSWERS", "MAX_COMMENTS",
    ),
    "Tags": (
        "NUMBER_OF_TAG_EXPERTS", "NUMBER_OF_TAG_RISING_STARS",
    ),
    "Moderator": (
        "DAYS_TO_REVOKE_MODERATOR", "DAYS_TO_GRANT_MODERATOR",
    ),
}

POSTGRES_SEARCH = {
    "trigram_min_relevance": 0.05,
    "weights": {
        "title": 0.7,
        "content": 0.3,
    },
}
DAYS_TO_REVOKE_MODERATOR = 10
DAYS_TO_GRANT_MODERATOR = 16
DAYS_FOR_QUESTION_TO_BECOME_OLD = getenv_asint("DAYS_FOR_QUESTION_TO_BECOME_OLD", None)
ANSWER_IS_RECENT_DAYS = 3

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

"""
All settings related to wiwik behavior.
Most of them can be set from environment variables.
"""
import os
from datetime import timedelta

from .base import getenv_asbool

CONSTANCE_CONFIG = {
    'USE_CDN': (True, 'Should 3rd party libraries be downloaded using CDN', bool),
    'FAVICON_LINK_LIGHT': ("/static/favicon-light.ico", 'site favicon for light-mode', str),
    'FAVICON_LINK_DARK': ("/static/favicon-dark.ico", 'site favicon for dark-mode', str),
    "QUESTIONS_PER_PAGE": (20, "Number of questions on a page", int),
    "MAX_SIZE_KB_IMAGE_UPLOAD_KB": (1024, "Max size of image allowed to upload (kb)", int),
    'GOOGLE_ANALYTICS_KEY': (os.getenv("GOOGLE_ANALYTICS_KEY", ""), 'Google Analytics key', str),
    'SHOWCASE_DEPLOYMENT': (True, 'Show link to wiwik source code', bool),

    'MAX_BOOKMARK_ITEMS': (20, 'Bookmarks to show on nav-bar', int),
    'MAX_REPUTATION_ITEMS': (10, 'Reputation activity to show on nav-bar', int),
    'LATEX_SUPPORT_ENABLED': (True, 'Enable LaTex support', bool),

    "UPVOTE_CHANGE": (10, "Points change for upvote", int),
    "DOWNVOTE_CHANGE": (-10, "Points change for downvote", int),
    "EDITED_CHANGE": (2, "Points change for editing post", int),
    "ACCEPT_ANSWER_CHANGE": (15, "Points change for accepted answer", int),
    "DAYS_FOR_QUESTION_TO_BECOME_OLD": (100, "Days for questions to be considered an old question", int),
    "ACCEPT_ANSWER_OLD_QUESTION_CHANGE": (100, "Points change for accepted answer on an old question", int),
    "ALLOW_ANONYMOUS_QUESTION": (True, "Allow posting questions anonymously", bool),
    "MIN_QUESTION_CONTENT_LENGTH": (20, "Minimum characters allowed in question body", int),
    "MAX_QUESTION_CONTENT_LENGTH": (30000, "Max characters allowed in question body", int),
    "MIN_QUESTION_TITLE_LENGTH": (15, "Minimum characters allowed in question title", int),
    "MAX_QUESTION_TITLE_LENGTH": (150, "Maximum characters allowed in question title", int),
    "MAX_ANSWERS": (3, "Maximum number of answers on a question", int),
    "MAX_COMMENTS": (5, "Maximum number of comments on a post", int),
    "MIN_COMMENT_LENGTH": (15, "Minimum characters in a comment", int),
    "MAX_COMMENT_LENGTH": (200, "Maximum characters in a comment", int),
    "ANSWER_IS_RECENT_DAYS": (3, "Number of days to consider an answer recent", int),
    # Article settings
    "MIN_ARTICLE_TITLE_LENGTH": (10, "Minimum characters in an article title", int),
    "MAX_ARTICLE_TITLE_LENGTH": (255, "Maximum characters in an article title", int),
    "MIN_ARTICLE_CONTENT_LENGTH": (50, "Minimum characters allowed in article body", int),
    "MAX_ARTICLE_CONTENT_LENGTH": (100_000, "Maximum characters allowed in article body", int),

    "DAYS_TO_REVOKE_MODERATOR": (10, "Number of sequential days without activity to revoke moderator permissions", int),
    "DAYS_TO_GRANT_MODERATOR": (15, "Number of sequential days with activity to grant moderator permissions", int),

    # Tag settings
    "NUMBER_OF_TAG_EXPERTS":
        (2, "Number of experts per tag (expert is a user with the most reputation on the tag)", int),
    "NUMBER_OF_TAG_RISING_STARS":
        (2, "Number of rising stars on a tag (a rising star is a user who is not an expert "
            "but has the most reputation for a tag in the past month", int),
    "MIN_TAG_DESCRIPTION_LENGTH": (20, "Minimum characters allowed in tag description", int),
    "MAX_TAG_DESCRIPTION_LENGTH": (460, "Maximum characters allowed in tag description", int),
    "MIN_TAG_WIKI_LENGTH": (20, "Minimum length of tag wiki page", int),
    "MAX_TAG_WIKI_LENGTH": (30000, "Maximum length of tag wiki page", int),
    "MIN_TAG_EDIT_SUMMARY_LENGTH": (10, "Maximum length of edit summary", int),
    "MAX_TAG_EDIT_SUMMARY_LENGTH": (200, "Maximum length of edit summary", int),

    # Search configuration
    "trigram_min_relevance": (0.05, "Minimum relevance for postgres trigram search", float),
    "trigram_weight_title": (0.7, "Weight for title in postgres trigram search", float),
    "trigram_weight_content": (0.3, "Weight for content in postgres trigram search", float),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "General Web settings": (
        "USE_CDN", "FAVICON_LINK_LIGHT", "FAVICON_LINK_DARK", "GOOGLE_ANALYTICS_KEY",
    ),
    "Forum Web settings": (
        "LATEX_SUPPORT_ENABLED", "MAX_BOOKMARK_ITEMS", "MAX_REPUTATION_ITEMS", "SHOWCASE_DEPLOYMENT",
        "ALLOW_ANONYMOUS_QUESTION", "QUESTIONS_PER_PAGE", "MAX_SIZE_KB_IMAGE_UPLOAD_KB",
    ),
    "Reputation change for activity": (
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
        "DAYS_FOR_QUESTION_TO_BECOME_OLD",
        "ANSWER_IS_RECENT_DAYS",
    ),
    "Tags configuration": (
        "NUMBER_OF_TAG_EXPERTS", "NUMBER_OF_TAG_RISING_STARS",
        "MIN_TAG_DESCRIPTION_LENGTH", "MAX_TAG_DESCRIPTION_LENGTH",
        "MIN_TAG_WIKI_LENGTH", "MAX_TAG_WIKI_LENGTH",
        "MIN_TAG_EDIT_SUMMARY_LENGTH", "MAX_TAG_EDIT_SUMMARY_LENGTH",
    ),
    "User permissions based on activity": (
        "DAYS_TO_REVOKE_MODERATOR", "DAYS_TO_GRANT_MODERATOR",
    ),
    "Search configuration": {
        "trigram_min_relevance", "trigram_weight_title", "trigram_weight_content",
    }
}

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

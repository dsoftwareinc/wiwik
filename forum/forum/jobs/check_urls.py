import datetime
import os
import re
from typing import Set

import django.core.mail
import requests
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from requests import ConnectTimeout
from scheduler import job
from urllib3.exceptions import MaxRetryError

from forum.apps import logger
from forum.models import Question

INLINE_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FOOTNOTE_LINK_TEXT_RE = re.compile(r"\[([^\]]+)\]\[(\d+)\]")
FOOTNOTE_LINK_URL_RE = re.compile(r"\[(\d+)\]:\s+(\S+)")


def _find_md_links(md):
    """Return dict of links in markdown"""

    links = dict(INLINE_LINK_RE.findall(md))
    footnote_links = dict(FOOTNOTE_LINK_TEXT_RE.findall(md))
    footnote_urls = dict(FOOTNOTE_LINK_URL_RE.findall(md))

    for key, value in footnote_links.items():
        footnote_links[key] = footnote_urls[value]
    links.update(footnote_links)

    return links


def _content_links() -> dict[int, list[str]]:
    questions = Question.objects.all().order_by("-created_at")
    results = dict()
    for q in questions:
        links = list(_find_md_links(q.content).values())
        answers_qs = q.answer_set.all()
        for a in answers_qs:
            links.extend(_find_md_links(a.content).values())
        results[q.id] = links
    return results


def _media_uploads() -> Set[str]:
    fss = FileSystemStorage()
    _, files = fss.listdir(os.path.join(settings.MEDIA_ROOT, "uploads"))
    links = {str(os.path.join(settings.MEDIA_URL, "uploads", filename)) for filename in files}
    return links


def _test_link(url: str) -> bool:
    try:
        response = requests.get(url)
        return response.status_code < 400
    except (MaxRetryError, ConnectTimeout):
        return False


@job()
def check_urls():
    res = dict()
    q_links = _content_links()
    for q in q_links:
        for link in q_links[q]:
            if not _test_link(link):
                res.setdefault(q, list()).append(link)
                logger.debug(f"Q{q} Link {link} does not work")
    return res


@job()
def scan_media_links_usage():
    uploads = _media_uploads()
    all_links = set()
    links = _content_links()
    for question_links in links.values():
        all_links.update(question_links)
    unused_media_uploads = uploads.difference(all_links)
    if len(unused_media_uploads) > 0:
        django.core.mail.mail_admins(
            f"Report - media files not used in any post {datetime.date.today()}",
            "\n".join(unused_media_uploads),
        )

from typing import List

from scheduler import job

from forum.apps import logger
from forum.models import SearchRecord
from userauth.models import ForumUser


@job
def log_search(user: ForumUser, query: str, results: List[int], timems: int):
    logger.info(f'Searching for: "{query}" in {timems}ms. got first 5 results: {results}')
    SearchRecord.objects.create(author=user, query=query, results=','.join(map(str, results)), time=timems)
    user.search_count += 1
    user.save()
    pass

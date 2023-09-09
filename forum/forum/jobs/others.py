import os
import random
from glob import glob
from typing import List

from scheduler import job

from forum.apps import logger
from forum.models import SearchRecord
from forum.views import utils
from main.settings import BASE_DIR
from userauth.models import ForumUser

DOCUMENTATION_DIRECTORY = os.path.join(BASE_DIR, '..', 'docs')


@job
def log_search(user: ForumUser, query: str, results: List[int], timems: int):
    logger.info(f'Searching for: "{query}" in {timems}ms. got first 5 results: {results}')
    SearchRecord.objects.create(author=user, query=query, results=','.join(map(str, results)), time=timems)
    user.search_count += 1
    user.save()
    pass


def create_documentation_posts():
    """Post documentation as knowledge articles"""

    def random_user_generator():
        users = ForumUser.objects.all()
        while True:
            yield random.choice(users)

    random_user = random_user_generator()
    filenames = [y for x in os.walk(DOCUMENTATION_DIRECTORY)
                 for y in glob(os.path.join(x[0], '*.md'))]
    logger.info(f"Populating {len(filenames)} documentation files")
    for filename in filenames:
        logger.info(f"Posting {filename} to wiwik")
        with open(filename, 'r') as f:
            content = f.read()
            title = content[content.find('# ') + 2:content.find('\n')]
            content = content[content.find('\n') + 1:]
            tags = filename.split('/')[:-1]
            tags.remove('..')
            utils.create_article(next(random_user), title, content, ','.join(tags), send_notifications=False)

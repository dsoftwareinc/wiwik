from functools import partial

from django.db.models import Count, F

from forum.models import Question
from userauth.models import ForumUser
from .utils import user_authored_vs_required, BadgeData, TRIGGER_EVENT_TYPES, BadgeType, BadgeCalculation


def question_bookmarked(required: int, user: ForumUser) -> BadgeCalculation:
    count = (Question.objects
             .filter(author=user)
             .annotate(num_bookmarks=Count('bookmarks'))
             .filter(num_bookmarks__gte=required)
             .count()) or 0
    closest = (Question.objects
               .filter(author=user)
               .annotate(next=Count('bookmarks') % required)
               .order_by('-next').values_list('next', flat=True)
               .first() or 0)
    return count, closest


def question_views(required: int, user: ForumUser) -> BadgeCalculation:
    count = (Question.objects
             .filter(author=user,
                     views__gte=required)
             .count())
    closest = (Question.objects
               .filter(author=user)
               .annotate(next=F('views') % required)
               .order_by('-next').values_list('next', flat=True)
               .first() or 0)
    return count, closest


def first_questions_in_site(user: ForumUser) -> BadgeCalculation:
    question_qs = Question.objects.all().order_by('created_at')[:10]
    user_authored = any([q.author == user for q in question_qs])
    return 1 if user_authored else 0, 0


question_badges = [
    BadgeData('Starter', 'Ask your first question',
              partial(user_authored_vs_required, Question, 1), BadgeType.BRONZE, True,
              TRIGGER_EVENT_TYPES['Create post'], group=1,
              ),
    BadgeData('Pioneer', 'Ask one of the first 10 questions on wiwik',
              first_questions_in_site, BadgeType.GOLD, True,
              TRIGGER_EVENT_TYPES['Create post'], group=20,
              ),
    BadgeData('Curious', 'Ask ten questions',
              partial(user_authored_vs_required, Question, 10), BadgeType.SILVER, True,
              TRIGGER_EVENT_TYPES['Create post'], group=1, required=10,
              ),
    BadgeData('Philosopher', 'Ask 100 questions',
              partial(user_authored_vs_required, Question, 100), BadgeType.GOLD, False,
              TRIGGER_EVENT_TYPES['Create post'], group=1, required=100,
              ),
    # Question bookmarks badges
    BadgeData('Favorite Question', 'Question bookmarked by 3 users',
              partial(question_bookmarked, 3), BadgeType.SILVER, False,
              TRIGGER_EVENT_TYPES['Bookmark thread'], group=2, required=3,
              ),
    BadgeData('Stellar Question', 'Question bookmarked by 10 users',
              partial(question_bookmarked, 10), BadgeType.GOLD, False,
              TRIGGER_EVENT_TYPES['Bookmark thread'], group=2, required=10,
              ),
    # Question views badges
    BadgeData('Popular Question', 'Question with 50 views',
              partial(question_views, 50), BadgeType.BRONZE, False,
              TRIGGER_EVENT_TYPES['View post'], group=3, required=50,
              ),
    BadgeData('Notable Question', 'Question with 250 views',
              partial(question_views, 250), BadgeType.SILVER, False,
              TRIGGER_EVENT_TYPES['View post'], group=3, required=250,
              ),
    BadgeData('Famous Question', 'Question with 1000 views',
              partial(question_views, 1000), BadgeType.GOLD, False,
              TRIGGER_EVENT_TYPES['View post'], group=3, required=1000,
              ),
]

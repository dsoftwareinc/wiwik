import datetime

from django.utils import timezone

from userauth.jobs import log_request
from userauth.models import ForumUser, UserVisit
from userauth.tests.utils import UserAuthTestCase


class UserAuthActivateTest(UserAuthTestCase):
    username = 'myusername'
    password = 'magicalPa$$w0rd'

    def test_first_visit__total_days_should_be_1(self):
        # assert start
        user = ForumUser.objects.create_user(self.username, f'{self.username}@a.com', self.password)

        self.assertEqual(0, UserVisit.objects.filter(user=user).count())
        # act
        log_request(user.id, '127.0.0.1', timezone.now(),
                    200, 'GET', '/path')
        # assert
        self.assertEqual(1, UserVisit.objects.filter(user=user).count())
        visit = UserVisit.objects.filter(user=user).first()
        self.assertEqual(1, visit.total_days)
        self.assertEqual(1, visit.max_consecutive_days)
        self.assertEqual(1, visit.consecutive_days)

    def test_visit_on_consecutive_day__green(self):
        # arrange
        user = ForumUser.objects.create_user(self.username, f'{self.username}@a.com', self.password)
        log_request(user.id, '127.0.0.1',
                    timezone.now() - datetime.timedelta(days=1), 200,
                    'GET', '/path')
        # assert start
        self.assertEqual(1, UserVisit.objects.filter(user=user).count())
        # act
        log_request(user.id, '127.0.0.1', timezone.now(), 200, 'GET', '/path')
        # assert
        self.assertEqual(2, UserVisit.objects.filter(user=user).count())
        visit = UserVisit.objects.filter(user=user).order_by('-visit_date').first()
        self.assertEqual(2, visit.total_days)
        self.assertEqual(2, visit.max_consecutive_days)
        self.assertEqual(2, visit.consecutive_days)

    def test_visit_on_consecutive_day__with_high_visit_count(self):
        # arrange
        user = ForumUser.objects.create_user(self.username, f'{self.username}@a.com', self.password)
        for i in range(20, 10, -1):
            log_request(user.id, '127.0.0.1',
                        timezone.now() - datetime.timedelta(days=i), 200,
                        'GET', '/path')
        # assert start
        self.assertEqual(10, UserVisit.objects.filter(user=user).count())
        self.assertEqual(10, UserVisit.objects.filter(user=user).order_by('-total_days').first().total_days)
        self.assertEqual(10, UserVisit.objects.filter(user=user).order_by(
            '-max_consecutive_days').first().max_consecutive_days)
        # act
        log_request(user.id, '127.0.0.1', timezone.now(), 200, 'GET', '/path')
        # assert
        self.assertEqual(11, UserVisit.objects.filter(user=user).count())
        visit = UserVisit.objects.filter(user=user).order_by('-visit_date').first()
        self.assertEqual(11, visit.total_days)
        self.assertEqual(10, visit.max_consecutive_days)
        self.assertEqual(1, visit.consecutive_days)

    def test_visit_on_consecutive_day__purged_visits_table_with_high_visit_count(self):
        # arrange
        user = ForumUser.objects.create_user(self.username, f'{self.username}@a.com', self.password)
        total_days = 20
        UserVisit.objects.create(user=user,
                                 ip_addr='127.0.0.1',
                                 visit_date=datetime.date(2021, 12, 10),
                                 country='Canada',
                                 city='Toronto',
                                 consecutive_days=10,
                                 max_consecutive_days=10,
                                 total_days=total_days)
        # act
        log_request(user.id, '127.0.0.1', timezone.now(), 200, 'GET', '/path')
        # assert
        self.assertEqual(2, UserVisit.objects.filter(user=user).count())
        visit = UserVisit.objects.filter(user=user).order_by('-visit_date').first()
        self.assertEqual(total_days + 1, visit.total_days)
        self.assertEqual(10, visit.max_consecutive_days)
        self.assertEqual(1, visit.consecutive_days)

    def test_visit_on_non_consecutive_day__green(self):
        # arrange
        user = ForumUser.objects.create_user(self.username, f'{self.username}@a.com', self.password)
        log_request(user.id, '127.0.0.1',
                    timezone.now() - datetime.timedelta(days=500), 200,
                    'GET', '/path')
        # assert start
        self.assertEqual(1, UserVisit.objects.filter(user=user).count())
        # act
        log_request(user.id, '127.0.0.1', timezone.now(), 200, 'GET', '/other')
        # assert
        self.assertEqual(2, UserVisit.objects.filter(user=user).count())
        visit = UserVisit.objects.filter(user=user).order_by('-visit_date').first()
        self.assertEqual(2, visit.total_days)
        self.assertEqual(1, visit.max_consecutive_days)
        self.assertEqual(1, visit.consecutive_days)

    def test_visit_on_same_day__green(self):
        # arrange
        user = ForumUser.objects.create_user(self.username, f'{self.username}@a.com', self.password)
        log_request(user.id, '127.0.0.1',
                    timezone.now(), 200,
                    'GET', '/path')
        # assert start
        self.assertEqual(1, UserVisit.objects.filter(user=user).count())
        # act
        log_request(user.id, '127.0.0.1', timezone.now(), 200, 'GET', '/other')
        # assert
        self.assertEqual(1, UserVisit.objects.filter(user=user).count())
        visit = UserVisit.objects.filter(user=user).order_by('-visit_date').first()
        self.assertEqual(1, visit.total_days)
        self.assertEqual(1, visit.max_consecutive_days)
        self.assertEqual(1, visit.consecutive_days)

    def test_visit__real_ip__green(self):
        # arrange
        user = ForumUser.objects.create_user(self.username, f'{self.username}@a.com', self.password)
        # act
        log_request(user.id, '174.95.73.69', timezone.now(), 200, 'GET', '/path')
        # assert
        self.assertEqual(1, UserVisit.objects.filter(user=user).count())
        visit = UserVisit.objects.filter(user=user).order_by('-visit_date').first()
        self.assertEqual(1, visit.total_days)
        self.assertEqual(1, visit.max_consecutive_days)
        self.assertEqual(1, visit.consecutive_days)
        self.assertEqual('Toronto', visit.city)
        self.assertEqual('Canada', visit.country)

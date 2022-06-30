from django.test import Client, TestCase

from django.contrib.auth.models import User
from membersapp.app.models import Members


member = None


def create_member(manager=False):
    global member
    user = User()
    member = Members(memid=user, name='testuser', email='test@spi-inc.org', ismanager=manager)
    user.save()
    member.save()


class ViewsTests(TestCase):

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the membership pages")


class LoggedInViewsTest(TestCase):
    def setUp(self):
        create_member()

    def test_index_loggedin(self):
        self.client.force_login(member.memid)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the membership pages")

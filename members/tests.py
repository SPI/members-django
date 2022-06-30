from django.test import Client, TestCase

from django.contrib.auth.models import User
from membersapp.app.models import Members


member = None
default_name = 'testuser'


def create_member(manager=False):
    global member
    user = User()
    member = Members(memid=user, name=default_name, email='test@spi-inc.org', ismanager=manager)
    user.save()
    member.save()


class NonLoggedInViewsTests(TestCase):

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the membership pages")

    def test_applications(self):
        response = self.client.get('/applications/all')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the membership pages")


class LoggedInViewsTest(TestCase):
    def setUp(self):
        create_member()

    def test_index_loggedin(self):
        self.client.force_login(member.memid)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Membership status for %s" % default_name)


class NonManagerTest(TestCase):
    def setUp(self):
        create_member(manager=False)

    def test_votes(self):
        self.client.force_login(member.memid)
        response = self.client.get('/votes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page is only accessible to application managers.")

    def test_applications(self):
        self.client.force_login(member.memid)
        response = self.client.get('/applications/all')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page is only accessible to application managers.")


class ManagerTest(TestCase):
    def setUp(self):
        create_member(manager=True)

    def test_votes(self):
        self.client.force_login(member.memid)
        response = self.client.get('/votes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the election pages of Software in the Public Interest, Inc.")

    def test_applications(self):
        self.client.force_login(member.memid)
        response = self.client.get('/applications/all')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page contains a list of ALL membership records")

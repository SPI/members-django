from django.test import Client, TestCase

from membersapp.app.models import Members


user = None


def create_user(manager=False):
    user = Members.objects.create(name='testuser', email='test@spi-inc.org')


class ViewsTests(TestCase):

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the membership pages")


class LoggedInViewsTest(TestCase):
    def setUp(self):
        create_user()

    def test_index_loggedin(self):
        self.client.force_login(user)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the membership pages")

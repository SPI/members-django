from django.test import Client, TestCase
from django.contrib.auth.models import User

from membersapp.app.models import Members, Applications


member = None
default_name = 'testuser'


def create_member(manager=False):
    global member
    user = User()
    member = Members(memid=user, name=default_name, email='test@spi-inc.org', ismanager=manager)
    user.save()
    member.save()

def create_application_post(testcase):
    data = {
            "contrib": "Hello wold",
            "sub_private": " on",
    }
    response = testcase.client.post("/apply/contrib", data=data)
    return response


class NonLoggedInViewsTests(TestCase):

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the membership pages")

    def test_applications(self):
        response = self.client.get('/applications/all')
        self.assertEqual(response.status_code, 302)

    def test_stats(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contrib Membership Applications")

    def test_404(self):
        response = self.client.get('/nonenxistent_page/')
        self.assertEqual(response.status_code, 404)

    def test_admin(self):
        response = self.client.get('/admin/', follow=True)
        self.assertRedirects(response, '/admin/login/?next=/admin/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Django administration")
        self.assertContains(response, "Username:")

    def test_member(self):
        response = self.client.get('/member/1')
        self.assertRedirects(response, '/accounts/login/?next=/member/1', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_apply(self):
        response = create_application_post(self)
        self.assertRedirects(response, '/accounts/login/?next=/apply/contrib', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertEqual(Applications.objects.count(), 0)


class LoggedInViewsTest(TestCase):
    def setUp(self):
        create_member()
        self.client.force_login(member.memid)

    def test_index_loggedin(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Membership status for %s" % default_name)
        self.assertContains(response, "Apply</a> for contributing membership")

    def test_stats(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contrib Membership Applications")

    def test_apply(self):
        response = create_application_post(self)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertEqual(Applications.objects.count(), 1)


class NonManagerTest(TestCase):
    def setUp(self):
        create_member(manager=False)
        self.client.force_login(member.memid)

    def test_votes(self):
        response = self.client.get('/votes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page is only accessible to application managers.")

    def test_applications(self):
        response = self.client.get('/applications/all')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page is only accessible to application managers.")

    def test_stats(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contrib Membership Applications")

    def test_member(self):
        response = self.client.get('/member/%d' % member.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page is only accessible to application managers.")


class ManagerTest(TestCase):
    def setUp(self):
        create_member(manager=True)
        self.client.force_login(member.memid)

    def test_votes(self):
        response = self.client.get('/votes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the election pages of Software in the Public Interest, Inc.")
        self.assertContains(response, "All Applications")

    def test_applications(self):
        response = self.client.get('/applications/all')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page contains a list of ALL membership records")
        self.assertContains(response, "All Applications")

    def test_stats(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contrib Membership Applications")
        self.assertContains(response, "All Applications")

    def test_application_unknown(self):
        response = self.client.get('/application/1337')
        self.assertEqual(response.status_code, 404)

    def test_member(self):
        response = self.client.get('/member/%d' % member.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Membership status for %s" % default_name)

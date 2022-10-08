import datetime

from django.test import Client, TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from membersapp.app.models import Members, Applications, VoteElection


member = None
default_name = 'testuser'
manager = None


# To dump a page to test.html, use:
# dump_page(response.content)
def dump_page(page):
    with open('test.html', 'w') as f:
        print(page.decode('UTF-8'), file=f)


def create_member(manager=False, contrib=False):
    global member
    user = User()
    member = Members(memid=user, name=default_name, email='test@spi-inc.org', ismanager=manager, iscontrib=contrib, createvote=manager)
    user.save()
    member.save()


def create_other_member(manager=False):
    user = User(username='other member')
    member = Members(memid=user, name='Other User', email='other_user@spi-inc.org', ismanager=manager)
    user.save()
    member.save()
    return member


def create_manager():
    global manager
    user = User(username='manager')
    manager = Members(memid=user, name='manager', email='manager@spi-inc.org', ismanager=True, createvote=True)
    user.save()
    manager.save()


def create_application_post(testcase):
    data = {
        "contrib": "Hello world create_application_post",
        "sub_private": " on",
    }
    response = testcase.client.post("/apply/contrib", data=data)
    return response


def create_vote(testcase, current=False, past=False, title="Test vote", target="/vote/create"):
    if current:
        data = {
            "title": title,
            "description": "Hello world create_vote",
            "period_start": (timezone.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d"),
            "period_stop": (timezone.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
            "system": "2",
            "winners": "1",
            "vote-btn": "Edit"
        }
    elif past:
        data = {
            "title": title,
            "description": "Hello world create_vote",
            "period_start": (timezone.now() + datetime.timedelta(days=-7)).strftime("%Y-%m-%d"),
            "period_stop": (timezone.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d"),
            "system": "2",
            "winners": "1",
            "vote-btn": "Edit"
        }
    else:
        data = {
            "title": title,
            "description": "Hello world create_vote",
            "period_start": (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "period_stop": (timezone.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
            "system": "2",
            "winners": "1",
            "vote-btn": "Edit"
        }
    response = testcase.client.post(target, data=data, follow=True)
    return response


def create_vote_manually(current=False, past=False, owner=None):
    if owner is None:
        # Can't pass global variable in the function's signature
        owner = member
    if current:
        vote = VoteElection(title="Test vote",
                            description="Hello world voteelection",
                            period_start=(timezone.now() + datetime.timedelta(days=-1)),
                            period_stop=(timezone.now() + datetime.timedelta(days=7)),
                            system=2,
                            owner=owner
                            )
        vote.save()
    elif past:
        vote = VoteElection(title="Test vote",
                            description="Hello world voteelection",
                            period_start=(timezone.now() + datetime.timedelta(days=-7)),
                            period_stop=(timezone.now() + datetime.timedelta(days=-1)),
                            system=2,
                            owner=owner
                            )
        vote.save()
    return vote


def create_vote_with_manager(testcase):
    testcase.client.logout()
    testcase.client.force_login(manager.memid)
    response = create_vote(testcase)
    testcase.assertEqual(response.status_code, 302)
    testcase.assertEqual(VoteElection.objects.count(), 1)
    # relog as non-manager
    testcase.client.logout()
    testcase.client.force_login(member.memid)


def create_vote_option(testcase, voteid):
    data = {
        "option_character": "A",
        "description": "Hello world voteoption",
        "sort": 1,
        "obtn": "Add"
    }
    response = testcase.client.post("/vote/%s/edit" % voteid, data=data, follow=True)
    return response


def create_vote_option2(testcase, voteid):
    data = {
        "option_character": "B",
        "description": "Hello world 2 voteoption",
        "sort": 2,
        "obtn": "Add"
    }
    response = testcase.client.post("/vote/%s/edit" % voteid, data=data)
    return response


def delete_vote_option(testcase, voteid):
    data = {
        "option_character": "A",
        "sort": 1,
        "obtn": "Delete"
    }
    response = testcase.client.post("/vote/%s/edit" % voteid, data=data, follow=True)
    return response


def edit_vote_option(testcase, voteid):
    data = {
        "option_character": "A",
        "description": "Hello world voteoption edited",
        "sort": 1,
        "obtn": "Edit"
    }
    response = testcase.client.post("/vote/%s/edit" % voteid, data=data)
    return response


def edit_vote_option2(testcase, voteid):
    data = {
        "option_character": "B",
        "description": "Hello world 2 voteoption edited",
        "sort": 2,
        "obtn": "Edit"
    }
    response = testcase.client.post("/vote/%s/edit" % voteid, data=data)
    return response


def vote_vote(testcase, voteid, correct=True):
    if correct:
        data = {
            "vote": "BA"
        }
    else:
        data = {
            "vote": "ABZ"
        }
    response = testcase.client.post("/vote/%s/vote" % voteid, data=data, follow=True)
    return response


def set_vote_current(vote):
    vote.period_start = timezone.now() + datetime.timedelta(days=-1)
    vote.period_stop = timezone.now() + datetime.timedelta(days=7)
    vote.save()


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

    def test_memberedit(self):
        data = {
            "sub_private": "on",
        }
        response = self.client.post("/member/edit", data=data)
        self.assertEqual(response.status_code, 302)


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

    def test_application_view(self):
        response = create_application_post(self)
        self.assertEqual(response.status_code, 302)
        application = Applications.objects.filter(member=member)[0]
        response = self.client.get('/application/%d' % application.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Application #%d status" % application.pk)
        self.assertContains(response, "Member Name</td><td>%s" % default_name)

    def test_memberedit(self):
        data = {
            "sub_private": "on",
        }
        response = self.client.post("/member/edit", data=data)
        user = Members.object.get(pk=member)  # get updated user
        self.assertEqual(user.sub_private, True)
        self.assertEqual(response.status_code, 302)

    def test_updateactive(self):
        data = {
        }
        response = self.client.post("/updateactive", data=data)
        user = Members.object.get(pk=member)  # get updated user
        self.assertEqual(user.lastactive, datetime.date.today())
        self.assertEqual(response.status_code, 302)

    def test_logout(self):
        # We can't test pgweb from here
        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)


class NonManagerTest(TestCase):
    def setUp(self):
        create_member(manager=False)
        create_manager()
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

    def test_application_view_not_own(self):
        other_member = create_other_member()
        other_application = Applications(member=other_member)
        other_application.save()
        response = self.client.get('/application/%d' % other_application.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page is only accessible to application managers.")

    def test_vote_view(self):
        create_vote_with_manager(self)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page is only accessible to application managers.")

    def test_viewvoteresult_noncontrib(self):
        create_vote_manually(self)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d/result' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "This page is only accessible to contributing members.")


class ManagerTest(TestCase):
    def setUp(self):
        create_member(manager=True, contrib=True)
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

    def test_votecreate(self):
        response = create_vote(self)
        self.assertEqual(VoteElection.objects.count(), 1)
        vote = VoteElection.objects.all()[0]
        self.assertRedirects(response, '/vote/%d/edit' % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        response = self.client.get('/')
        self.assertContains(response, "Your votes")
        self.assertContains(response, "Test vote")

    def test_vote_edit(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        response = create_vote(self, title="Edited vote", target="/vote/%d/editedit" % vote.pk)
        dump_page(response.content)
        self.assertRedirects(response, '/vote/%d/edit' % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Edited vote")

    def test_editcurrentvote(self):
        create_vote_manually(current=True)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d/edit' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Vote must not have run to be edited")

    def test_viewcurrentvote(self):
        vote = create_vote_manually(current=True)
        response = self.client.get('/vote/%d' % vote.pk,)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You have not yet cast a vote.")

    def test_viewpastvote(self):
        create_vote_manually(past=True)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The voting period ended")
        response = self.client.get('/vote/%d/edit' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Vote must not have run to be edited")

    def test_viewfuturevote(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Voting has not yet opened")

    def test_viewvote(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test vote")
        self.assertNotContains(response, "Magic Voodoo")

    def test_addoptionform(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        response = create_vote_option(self, vote.pk)
        self.assertRedirects(response, "/vote/%s/edit" % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Hello world voteoption")

    def test_deletevoteoptionform(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        response = create_vote_option(self, vote.pk)
        self.assertContains(response, "Hello world voteoption")
        response = delete_vote_option(self, vote.pk)
        self.assertRedirects(response, "/vote/%s/edit" % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertNotContains(response, "Hello world voteoption")

    def test_editoptionform(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        response = edit_vote_option(self, vote.pk)
        self.assertRedirects(response, "/vote/%s/edit" % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Hello world voteoption edited")

    def test_addoptionform_multiple(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        response = create_vote_option(self, vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world voteoption")
        response = create_vote_option2(self, vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world voteoption")
        self.assertContains(response, "Hello world 2 voteoption")

    def test_editoptionform_multiple(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        response = edit_vote_option(self, vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world voteoption edited")
        self.assertContains(response, "Hello world 2 voteoption")
        response = edit_vote_option2(self, vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello world voteoption edited")
        self.assertContains(response, "Hello world 2 voteoption edited")

    def test_viewvoteresult(self):
        member = create_other_member(self)
        create_vote_manually(self, owner=member)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d/result' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You can only view results for your own votes.")

    def test_votevote(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        # We can't add vote on current test
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        set_vote_current(vote)
        response = vote_vote(self, vote.pk, correct=True)
        self.assertRedirects(response, '/vote/%d' % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Your vote is as follows:")

    def test_votevote_incorrect(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        # We can't add vote on current test
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        set_vote_current(vote)
        response = vote_vote(self, vote.pk, correct=False)
        self.assertRedirects(response, '/vote/%d' % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Invalid vote option Z")

# There are 4 views in the application:
# - Non logged-in
# - Non-contributing member
# - Contributing member (can vote and see votes)
# - Application manager (can manage applications and votes)
# Besides of that, member can have vote creation rights (which should probably
# only be attributed to managers)

import datetime

from django.test import Client, TestCase, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import auth

from membersapp.app.models import Members, Applications, VoteElection, VoteVote


member = None
default_name = 'testuser'
manager = None
error_application_manager = "This page is only accessible to application managers."
error_contrib_member = "This page is only accessible to contributing members."


# To dump a page to test.html, use:
# dump_page(response)
def dump_page(response):
    with open('test.html', 'w') as f:
        print(response.content.decode('UTF-8'), file=f)


def create_member(manager=False, contrib=False):
    global member
    email = 'test@spi-inc.org'
    user = User(email=email)
    member = Members(memid=user, name=default_name, email=email, ismanager=manager, iscontrib=contrib, createvote=manager)
    user.save()
    member.save()


def create_other_member(manager=False, contrib=False, name='Other User', email='other_user@spi-inc.org'):
    user = User(username=name, email=email)
    member = Members(memid=user, name=name, email=email, ismanager=manager, iscontrib=contrib, createvote=manager)
    user.save()
    member.save()
    return member


def create_manager():
    global manager
    user = User(username='manager')
    manager = Members(memid=user, name='manager', email='manager@spi-inc.org', ismanager=True, createvote=True)
    user.save()
    manager.save()


def create_application_post(testcase, follow=True):
    data = {
        "contrib": "Hello world create_application_post",
        "sub_private": "on",
    }
    response = testcase.client.post("/apply/contrib", data=data, follow=follow)
    return response


def create_vote(testcase, current=False, past=False, title="Test vote", target="/vote/create", system="2"):
    if current:
        data = {
            "title": title,
            "description": "Hello world create_vote",
            "period_start": (timezone.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d"),
            "period_stop": (timezone.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
            "system": system,
            "winners": "1",
            "vote-btn": "Edit"
        }
    elif past:
        data = {
            "title": title,
            "description": "Hello world create_vote",
            "period_start": (timezone.now() + datetime.timedelta(days=-7)).strftime("%Y-%m-%d"),
            "period_stop": (timezone.now() + datetime.timedelta(days=-1)).strftime("%Y-%m-%d"),
            "system": system,
            "winners": "1",
            "vote-btn": "Edit"
        }
    else:
        data = {
            "title": title,
            "description": "Hello world create_vote",
            "period_start": (timezone.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "period_stop": (timezone.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"),
            "system": system,
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
    switch_to_other_member(testcase, switch_to_manager=True)
    response = create_vote(testcase)
    testcase.assertEqual(VoteElection.objects.count(), 1)
    vote = VoteElection.objects.all()[0]
    create_vote_option(testcase, vote.pk)
    create_vote_option2(testcase, vote.pk)
    # relog as non-manager
    switch_back(testcase)
    return vote


def switch_to_other_member(testcase, switch_to_manager=False, switch_to_contrib=False, new_manager=False):
    testcase.client.logout()
    if switch_to_manager:
        if new_manager:
            other_manager = create_other_member(manager=True)
            testcase.client.force_login(other_manager.memid)
        else:
            testcase.client.force_login(manager.memid)
    else:
        other_member = create_other_member(contrib=switch_to_contrib)
        testcase.client.force_login(other_member.memid)
        return other_member


def switch_back(testcase, logged_in=True):
    testcase.client.logout()
    if logged_in:
        testcase.client.force_login(member.memid)


def create_vote_option(testcase, voteid):
    data = {
        "option_character": "A",
        "description": "Hello world voteoption",
        "sort": 1,
        "obtn": "Add"
    }
    response = testcase.client.post("/vote/%s/editoption" % voteid, data=data, follow=True)
    return response


def create_vote_option2(testcase, voteid):
    data = {
        "option_character": "B",
        "description": "Hello world 2 voteoption",
        "sort": 2,
        "obtn": "Add"
    }
    response = testcase.client.post("/vote/%s/editoption" % voteid, data=data, follow=True)
    return response


def delete_vote_option(testcase, voteid):
    data = {
        "option_character": "A",
        "sort": 1,
        "obtn": "Delete"
    }
    response = testcase.client.post("/vote/%s/editoption" % voteid, data=data, follow=True)
    return response


def edit_vote_option(testcase, voteid):
    data = {
        "option_character": "A",
        "description": "Hello world voteoption edited",
        "sort": 1,
        "obtn": "Edit"
    }
    response = testcase.client.post("/vote/%s/editoption" % voteid, data=data, follow=True)
    return response


def edit_vote_option2(testcase, voteid):
    data = {
        "option_character": "B",
        "description": "Hello world 2 voteoption edited",
        "sort": 2,
        "obtn": "Edit"
    }
    response = testcase.client.post("/vote/%s/editoption" % voteid, data=data, follow=True)
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


def vote_vote_other_member(testcase, voteid):
    switch_to_other_member(testcase, switch_to_contrib=True)
    data = {
        "vote": "B"
    }
    response = testcase.client.post("/vote/%s/vote" % voteid, data=data, follow=True)
    switch_back(testcase)
    return response


def set_vote_current(vote):
    vote.period_start = timezone.now() + datetime.timedelta(days=-1)
    vote.period_stop = timezone.now() + datetime.timedelta(days=7)
    vote.save()


def set_vote_past(vote):
    vote.period_start = timezone.now() + datetime.timedelta(days=-7)
    vote.period_stop = timezone.now() + datetime.timedelta(days=-1)
    vote.save()


def delete_vote(testcase, voteid):
    data = {
        "vote-btn": "Delete"
    }
    response = testcase.client.post("/vote/%s/editedit" % voteid, data=data, follow=True)
    return response


def register_user(testcase):
    data = {
        "username": "testregister",
        "first_name": "test",
        "last_name": "test",
        "email": "test_register@spi-inc.org",
        "email2": "test_register@spi-inc.org"
    }
    response = testcase.client.post("/account/signup/", data=data, follow=True)
    return response


class NonLoggedInViewsTests(TestCase):
    def setUp(self):
        create_member(manager=False)
        create_manager()

    # ## No need to copy these tests in other roles
    def test_404(self):
        response = self.client.get('/nonenxistent_page/')
        self.assertEqual(response.status_code, 404)

    def test_admin(self):
        response = self.client.get('/admin/', follow=True)
        self.assertRedirects(response, '/admin/login/?next=/admin/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Django administration")
        self.assertContains(response, "Username:")

    # ## Views tests
    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the membership pages")

    def test_stats(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contrib Membership Applications")

    def test_application_view(self):
        switch_to_other_member(self)
        response = create_application_post(self)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        switch_back(self, logged_in=False)
        application = Applications.objects.all()[0]
        response = self.client.get('/application/%d' % application.pk)
        self.assertRedirects(response, '/account/login/?next=/application/%s' % application.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_updateactive(self):
        data = {
        }
        response = self.client.post("/updateactive", data=data)
        self.assertRedirects(response, '/account/login/?next=/updateactive', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_member(self):
        response = self.client.get('/member/1')
        self.assertRedirects(response, '/account/login/?next=/member/1', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_memberedit(self):
        data = {
            "sub_private": "on",
        }
        response = self.client.post("/member/edit", data=data)
        self.assertRedirects(response, '/account/login/?next=/member/edit', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_applications(self):
        for case in ['all', 'ncm', 'ca', 'cm', 'mgr']:
            response = self.client.get('/applications/%s' % case)
            self.assertRedirects(response, '/account/login/?next=/applications/%s' % case, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_application_edit(self):
        switch_to_other_member(self)
        response = create_application_post(self)
        switch_back(self, logged_in=False)
        application = Applications.objects.all()[0]
        data = {
        }
        response = self.client.post('/application/%d/edit' % application.pk, data=data)
        self.assertRedirects(response, '/account/login/?next=/application/%d/edit' % application.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_apply(self):
        response = create_application_post(self, follow=False)
        self.assertRedirects(response, '/account/login/?next=/apply/contrib', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertEqual(Applications.objects.count(), 0)

    def tests_vote_redirect(self):
        create_vote_manually(self)
        vote = VoteElection.objects.all()[0]
        for case in ['/votes', '/vote/create', '/vote/%d' % vote.pk, '/vote/%d/edit' % vote.pk, '/vote/%d/editedit' % vote.pk, '/vote/%d/editoption' % vote.pk, '/vote/%d/vote' % vote.pk, '/vote/%d/result' % vote.pk]:
            response = self.client.get(case)
            self.assertRedirects(response, '/account/login/?next=%s' % case, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_privatesubs(self):
        user1 = User(username="isprivate", email="isprivate@spi-inc.org")
        user2 = User(username="noprivate", email='noprivate@spi-inc.org')
        member_private = Members(memid=user1, name="isprivate", email='isprivate@spi-inc.org', sub_private=True, iscontrib=True)
        member_noprivate = Members(memid=user2, name="noprivate", email='noprivate@spi-inc.org', sub_private=False, iscontrib=True)
        user1.save()
        user2.save()
        member_private.save()
        member_noprivate.save()
        response = self.client.get('/privatesubs')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "isprivate")
        self.assertNotContains(response, "noprivate")

    @override_settings(NOCAPTCHA=True)
    def test_register(self):
        response = register_user(self)
        dump_page(response)
        self.assertRedirects(response, '/account/signup/complete/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Account created")
        assert User.objects.filter(username="testregister").exists()


# Non-contrib member
class LoggedInViewsTest(TestCase):
    def setUp(self):
        create_member(manager=False)
        create_manager()
        self.client.force_login(member.memid)

    def test_logout(self):
        user = auth.get_user(self.client)
        assert user.is_authenticated
        response = self.client.get('/account/logout', follow=True)
        self.assertRedirects(response, '/', status_code=301, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, "Welcome to the membership pages")

    def test_index_loggedin(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Membership status for %s" % default_name)
        self.assertContains(response, "Apply</a> for contributing membership")

    def test_stats(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contrib Membership Applications")

    def test_application_view(self):
        response = create_application_post(self)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        application = Applications.objects.filter(member=member)[0]
        response = self.client.get('/application/%d' % application.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Application #%d status" % application.pk)
        self.assertContains(response, "Member Name</td><td>%s" % default_name)

    def test_application_other_view(self):
        switch_to_other_member(self)
        response = create_application_post(self)
        switch_back(self)
        application = Applications.objects.all()[0]
        response = self.client.get('/application/%d' % application.pk)
        self.assertContains(response, error_application_manager)

    def test_updateactive(self):
        data = {
        }
        response = self.client.post("/updateactive", data=data)
        user = Members.object.get(pk=member)  # get updated user
        self.assertEqual(user.lastactive, datetime.date.today())
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_member(self):
        response = self.client.get('/member/%d' % member.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, error_application_manager)

    def test_memberedit(self):
        data = {
            "sub_private": "on",
        }
        response = self.client.post("/member/edit", data=data)
        user = Members.object.get(pk=member)  # get updated user
        self.assertEqual(user.sub_private, True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_applications(self):
        for case in ['all', 'ncm', 'ca', 'cm', 'mgr']:
            response = self.client.get('/applications/%s' % case)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, error_application_manager)

    def test_application_edit(self):
        response = create_application_post(self)
        application = Applications.objects.all()[0]
        data = {
        }
        response = self.client.post('/application/%d/edit' % application.pk, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, error_application_manager)

    def test_apply(self):
        response = create_application_post(self)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertEqual(Applications.objects.count(), 1)

    def test_apply_twice(self):
        response = create_application_post(self)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertEqual(Applications.objects.count(), 1)
        response = create_application_post(self)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, 'You already have an outstanding SPI contributing')

    def tests_vote_noncontrib_contrib_error(self):
        create_vote_manually(self)
        vote = VoteElection.objects.all()[0]
        for case in ['/votes', '/vote/%d' % vote.pk, '/vote/%d/vote' % vote.pk]:
            response = self.client.get(case)
            self.assertContains(response, error_contrib_member)

    def tests_vote_noncontrib_not_allowed_error(self):
        create_vote_manually(self)
        vote = VoteElection.objects.all()[0]
        for case in ['/vote/%d/edit' % vote.pk, '/vote/%d/editoption' % vote.pk]:
            response = self.client.get(case, follow=True)
            self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
            self.assertContains(response, "You are not allowed to create new votes")

    def test_votes(self):
        response = self.client.get('/votes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, error_contrib_member)

    def test_vote_create(self):
        response = self.client.get('/vote/create', follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, "You are not allowed to create new votes")

    def test_vote_edit_nonmanager(self):
        vote = create_vote_with_manager(self)
        response = create_vote(self, title="Edited vote", target="/vote/%d/editedit" % vote.pk)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertNotContains(response, "Edited vote")
        self.assertContains(response, "You are not allowed to create new votes")

    def test_viewvoteresult_incorrect(self):
        member = create_other_member()
        create_vote_manually(past=True, owner=member)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d/result' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "You can only view results for your own votes.")

    # Only managers should get vote creation rights, so we'll leave the rest of
    # voting results tests here


class ContribUserTest(TestCase):
    def setUp(self):
        create_member(manager=False, contrib=True)
        create_manager()
        self.client.force_login(member.memid)

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Membership status for")
        self.assertContains(response, "Yes")

    def test_stats(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contrib Membership Applications")

    def test_application_view(self):
        application = Applications(member=member)
        application.save()
        response = self.client.get('/application/%d' % application.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Application #%d status" % application.pk)
        self.assertContains(response, "Member Name</td><td>%s" % default_name)

    def test_application_other_view(self):
        switch_to_other_member(self)
        response = create_application_post(self)
        switch_back(self)
        application = Applications.objects.all()[0]
        response = self.client.get('/application/%d' % application.pk)
        self.assertContains(response, error_application_manager)

    def test_updateactive(self):
        data = {
        }
        response = self.client.post("/updateactive", data=data)
        user = Members.object.get(pk=member)  # get updated user
        self.assertEqual(user.lastactive, datetime.date.today())
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_member(self):
        response = self.client.get('/member/%d' % member.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, error_application_manager)

    def test_memberedit(self):
        data = {
            "sub_private": "on",
        }
        response = self.client.post("/member/edit", data=data)
        user = Members.object.get(pk=member)  # get updated user
        self.assertEqual(user.sub_private, True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_applications(self):
        for case in ['all', 'ncm', 'ca', 'cm', 'mgr']:
            response = self.client.get('/applications/%s' % case)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, error_application_manager)

    def test_new_application(self):
        response = create_application_post(self)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, "You are already an SPI contributing member")

    def test_votes(self):
        create_vote_manually(current=True)
        response = self.client.get('/votes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the election pages of Software in the Public Interest, Inc.")
        self.assertContains(response, "Test vote")

    def test_vote_create(self):
        response = self.client.get('/vote/create', follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, "You are not allowed to create new votes")

    def test_viewcurrentvote(self):
        vote = create_vote_with_manager(self)
        set_vote_current(vote)
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You have not yet cast a vote.")
        self.assertContains(response, "Test vote")
        self.assertNotContains(response, "Magic Voodoo")

    def test_viewpastvote(self):
        vote = create_vote_with_manager(self)
        set_vote_past(vote)
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The voting period ended")

    def test_viewfuturevote(self):
        vote = create_vote_with_manager(self)
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Voting has not yet opened")

    def test_viewvoteedit(self):
        vote = create_vote_with_manager(self)
        response = self.client.get('/vote/%d/edit' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "You are not allowed to create new votes")

    def test_vote_edit(self):
        vote = create_vote_with_manager(self)
        response = create_vote(self, title="Edited vote", target="/vote/%d/editedit" % vote.pk)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, "You are not allowed to create new votes")

    def test_editoptionform(self):
        vote = create_vote_with_manager(self)
        response = edit_vote_option(self, vote.pk)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, "You are not allowed to create new votes")

    def test_votevote_not_running(self):
        vote = create_vote_with_manager(self)
        response = vote_vote(self, vote.pk, correct=True)
        self.assertRedirects(response, '/vote/%d' % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Vote is not currently running")
        self.assertEqual(VoteVote.objects.count(), 0)

    def test_votevote(self):
        vote = create_vote_with_manager(self)
        set_vote_current(vote)
        response = vote_vote(self, vote.pk, correct=True)
        self.assertRedirects(response, '/vote/%d' % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Your vote is as follows:")

    def test_votevote_lastactive(self):
        global member
        vote = create_vote_with_manager(self)
        set_vote_current(vote)
        member.lastactive = None
        member.save()
        member = Members.object.get(pk=member.memid)
        self.assertEqual(member.lastactive, None)
        response = vote_vote(self, vote.pk, correct=True)
        member = Members.object.get(pk=member.memid)
        self.assertEqual(member.lastactive, datetime.date.today())

    def test_votevote_incorrect(self):
        vote = create_vote_with_manager(self)
        set_vote_current(vote)
        response = vote_vote(self, vote.pk, correct=False)
        self.assertRedirects(response, '/vote/%d' % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Invalid vote option Z")

    def test_viewvoteresult_incorrect(self):
        member = create_other_member()
        create_vote_manually(past=True, owner=member)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d/result' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "You can only view results for your own votes.")

    # Only managers should get vote creation rights, so we'll leave the rest of
    # voting results tests here


class ManagerTest(TestCase):
    def setUp(self):
        create_member(manager=True, contrib=True)
        self.client.force_login(member.memid)

    # Note: this test cannot work because we have to bypass pgweb auth using
    # force_login()
    # def test_admin_staff(self):
    #    member.is_staff = True
    #    member.is_superuser = True
    #    member.save()
    #    response = self.client.get('/admin/', follow=True)
    #    self.assertContains(response, "Site administration")

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Membership status for")
        self.assertContains(response, "All Applications")

    def test_stats(self):
        response = self.client.get('/stats/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contrib Membership Applications")
        self.assertContains(response, "All Applications")

    def test_application_unknown(self):
        response = self.client.get('/application/1337')
        self.assertEqual(response.status_code, 404)

    def test_application_view(self):
        other_member = create_other_member()
        application = Applications(member=other_member)
        application.save()
        response = self.client.get('/application/%d' % application.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Application #%d status" % application.pk)
        self.assertContains(response, "Member Name</td><td>%s" % "Other User")

    def test_updateactive(self):
        data = {
        }
        response = self.client.post("/updateactive", data=data)
        user = Members.object.get(pk=member)  # get updated user
        self.assertEqual(user.lastactive, datetime.date.today())
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    def test_member(self):
        response = self.client.get('/member/%d' % member.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Membership status for %s" % default_name)

    def test_memberedit(self):
        data = {
            "sub_private": "on",
        }
        response = self.client.post("/member/edit", data=data)
        user = Members.object.get(pk=member)  # get updated user
        self.assertEqual(user.sub_private, True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)

    # applications/<str:listtype> tests are in the next class (with full workflow)

    def test_applications_wronglisttype(self):
        response = self.client.get('/applications/foo', follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Unknown application type!")

    def test_applications_emptylist(self):
        response = self.client.get('/applications/cm')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Unknown application type!")

    def test_application_edit(self):
        other_member = switch_to_other_member(self)
        response = create_application_post(self)
        switch_back(self)
        application = Applications.objects.all()[0]
        data = {
            "contrib": "sdfs",
            "manager": member.memid_id,
            "manager_date": timezone.now().strftime("%Y-%m-%d"),
            "comment": "Test+approve",
            "approve": "true",
            "approve_date": timezone.now().strftime("%Y-%m-%d")
        }
        response = self.client.post('/application/%d/edit' % application.pk, data=data, follow=True)
        application = Applications.objects.all()[0]
        self.assertRedirects(response, '/application/%d' % application.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, "selected>Yes")
        self.assertContains(response, "Applicant become a Contributing member, emailing them.")
        self.assertEqual(application.approve, True)

    def test_application_edit_reject(self):
        other_member = switch_to_other_member(self)
        response = create_application_post(self)
        switch_back(self)
        application = Applications.objects.all()[0]
        data = {
            "contrib": "sdfs",
            "manager": member.memid_id,
            "manager_date": timezone.now().strftime("%Y-%m-%d"),
            "comment": "Test+approve",
            "approve": "false",
            "approve_date": timezone.now().strftime("%Y-%m-%d")
        }
        response = self.client.post('/application/%d/edit' % application.pk, data=data, follow=True)
        application = Applications.objects.all()[0]
        self.assertRedirects(response, '/application/%d' % application.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, "selected>No")
        self.assertNotContains(response, "Applicant become a Contributing member, emailing them.")
        self.assertEqual(application.approve, False)

    def test_apply(self):
        response = create_application_post(self)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=False)
        self.assertContains(response, "You are already an SPI contributing member")

    def test_votes(self):
        response = self.client.get('/votes')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to the election pages of Software in the Public Interest, Inc.")
        self.assertContains(response, "All Applications")

    def test_votecreate(self):
        response = create_vote(self)
        self.assertEqual(VoteElection.objects.count(), 1)
        vote = VoteElection.objects.all()[0]
        self.assertRedirects(response, '/vote/%d/edit' % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        response = self.client.get('/')
        self.assertContains(response, "Your votes")
        self.assertContains(response, "Test vote")

    def test_votecreate_norights(self):
        member.createvote = False
        member.save()
        response = create_vote(self)
        self.assertEqual(VoteElection.objects.count(), 0)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "You are not allowed to create new votes")

    def test_vote_edit(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        response = create_vote(self, title="Edited vote", target="/vote/%d/editedit" % vote.pk)
        self.assertRedirects(response, '/vote/%d/edit' % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Edited vote")

    def test_vote_delete(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        response = delete_vote(self, vote.pk)
        self.assertEqual(VoteElection.objects.count(), 0)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Vote deleted")

    def test_editcurrentvote(self):
        create_vote_manually(current=True)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d/edit' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Vote must not have run to be edited")

    def test_viewvotenotenoughoptions(self):
        vote = create_vote_manually(current=True)
        response = self.client.get('/vote/%d' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Error: vote does not have enough options to run.")

    def test_viewcurrentvote(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        set_vote_current(vote)
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You have not yet cast a vote.")
        self.assertContains(response, "Test vote")
        self.assertNotContains(response, "Magic Voodoo")

    def test_viewpastvote(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        set_vote_past(vote)
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The voting period ended")

    def test_viewfuturevote(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        response = self.client.get('/vote/%d' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Voting has not yet opened")

    def test_viewvoteedit(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        response = self.client.get('/vote/%d/edit' % vote.pk)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Vote")

    def test_viewvoteedit_current_vote(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        set_vote_current(vote)
        response = self.client.get('/vote/%d/edit' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Vote must not have run to be edited")

    def test_viewvoteedit_past_vote(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        set_vote_past(vote)
        response = self.client.get('/vote/%d/edit' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Vote must not have run to be edited")

    # view other people's vote
    def test_viewvotes_other_managers(self):
        switch_to_other_member(self, switch_to_manager=True, new_manager=True)
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        switch_back(self)
        response = self.client.get('/vote/%d' % vote.pk, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Voting has not yet opened")

    def test_editvotes_other_managers(self):
        switch_to_other_member(self, switch_to_manager=True, new_manager=True)
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        create_vote_option(self, vote.pk)
        create_vote_option2(self, vote.pk)
        switch_back(self)
        for case in ['/vote/%d/edit' % vote.pk, '/vote/%d/editedit' % vote.pk, '/vote/%d/editoption' % vote.pk]:
            response = self.client.get(case, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "You can only edit your own votes.")

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
        self.assertRedirects(response, "/vote/%s/edit" % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Hello world voteoption")
        response = create_vote_option2(self, vote.pk)
        self.assertRedirects(response, "/vote/%s/edit" % vote.pk, status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
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

    def test_votes_404(self):
        for target in ['/vote/1337', '/vote/1337/edit', 'vote/1337/result']:
            response = self.client.get(target)
            self.assertEqual(response.status_code, 404)
        for target in ['/vote/1337/editedit', '/vote/1337/editoption', 'vote/1337/vote']:
            response = self.client.post(target)
            self.assertEqual(response.status_code, 404)

    def test_viewvoteresult_incorrect(self):
        member = create_other_member()
        create_vote_manually(past=True, owner=member)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d/result' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "You can only view results for your own votes.")

    def test_viewvoteresult_unfinished(self):
        create_vote(self)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d/result' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Vote must be finished to view results.")

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

    def test_viewvoteresult_no_option(self):
        create_vote_manually(past=True)
        vote = VoteElection.objects.all()[0]
        response = self.client.get('/vote/%d/result' % vote.pk, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200, msg_prefix='', fetch_redirect_response=True)
        self.assertContains(response, "Votes must have at least 2 candidates to run.")

    def test_viewvoteresult_STV(self):
        create_vote(self, system="2")
        vote = VoteElection.objects.all()[0]
        response = create_vote_option(self, vote.pk)
        response = create_vote_option2(self, vote.pk)
        set_vote_current(vote)
        response = vote_vote(self, vote.pk, correct=True)
        response = vote_vote_other_member(self, vote.pk)
        set_vote_past(vote)
        response = self.client.get('/vote/%d/result' % vote.pk)
        self.assertEqual(response.status_code, 200)

    def test_viewvoteresult_Condorcet(self):
        create_vote(self, system="0")
        vote = VoteElection.objects.all()[0]
        response = create_vote_option(self, vote.pk)
        response = create_vote_option2(self, vote.pk)
        set_vote_current(vote)
        response = vote_vote(self, vote.pk, correct=True)
        response = vote_vote_other_member(self, vote.pk)
        set_vote_past(vote)
        response = self.client.get('/vote/%d/result' % vote.pk)
        self.assertEqual(response.status_code, 200)

    def test_viewvoteresult_Condorcet2(self):
        create_vote(self, system="1")
        vote = VoteElection.objects.all()[0]
        response = create_vote_option(self, vote.pk)
        response = create_vote_option2(self, vote.pk)
        set_vote_current(vote)
        response = vote_vote(self, vote.pk, correct=True)
        response = vote_vote_other_member(self, vote.pk)
        set_vote_past(vote)
        response = self.client.get('/vote/%d/result' % vote.pk)
        self.assertEqual(response.status_code, 200)


class ApplicationWorkflowTests(TestCase):
    def setUp(self):
        create_member(manager=True, contrib=True)
        # Manager is already contrib, so we can't create an application using POST
        Applications(member=member, contribapp=True, approve=True).save()
        member_noncontrib = create_other_member(contrib=False, name='Other User noncontrib')
        # This application is created upon importing user from pgweb
        Applications(member=member_noncontrib, contribapp=False).save()
        self.client.force_login(member_noncontrib.memid)
        member_contrib_pending = create_other_member(contrib=False, name='Other User pending contrib', email='other_user_pending_contrib@spi-inc.org')
        self.client.force_login(member_contrib_pending.memid)
        create_application_post(self)
        member_contrib = create_other_member(contrib=False, name='Other User contrib', email='other_user_contrib@spi-inc.org')
        self.client.force_login(member_contrib.memid)
        create_application_post(self)
        switch_back(self)
        application = Applications.object.get(member=member_contrib)
        data = {
            "contrib": "sdfs",
            "manager": member.memid_id,
            "manager_date": timezone.now().strftime("%Y-%m-%d"),
            "comment": "Test+approve",
            "approve": "true",
            "approve_date": timezone.now().strftime("%Y-%m-%d")
        }
        response = self.client.post('/application/%d/edit' % application.pk, data=data, follow=True)

    def test_applications_all(self):
        response = self.client.get('/applications/all')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page contains a list of ALL membership records")
        self.assertContains(response, "All Applications")
        self.assertContains(response, default_name)
        self.assertContains(response, "Other User pending contrib")
        self.assertContains(response, "Other User noncontrib")
        self.assertContains(response, "Other User contrib")

    def test_applications_nca(self):
        response = self.client.get('/applications/nca')
        dump_page(response)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page contains a list of all people who have applied for non-contributing\nmembership but have not completed the email verification step.")
        self.assertContains(response, "All Applications")
        self.assertNotContains(response, default_name)
        self.assertNotContains(response, "Other User noncontrib")
        self.assertNotContains(response, "Other User pending contrib")
        self.assertNotContains(response, "Other User contrib")

    def test_applications_cnm(self):
        response = self.client.get('/applications/ncm')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page lists all members who have non-contributing status.")
        self.assertContains(response, "All Applications")
        self.assertNotContains(response, default_name)
        self.assertContains(response, "Other User noncontrib")
        self.assertNotContains(response, "Other User pending contrib")
        self.assertNotContains(response, "Other User contrib")

    def test_applications_ca(self):
        response = self.client.get('/applications/ca')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page lists all non-contributing members who have filed a contributing")
        self.assertContains(response, "All Applications")
        self.assertNotContains(response, default_name)
        self.assertContains(response, "Other User pending contrib")
        self.assertNotContains(response, "Other User noncontrib")
        self.assertNotContains(response, "Other User contrib")

    def test_applications_cm(self):
        response = self.client.get('/applications/cm')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page lists all active contributing members in SPI.")
        self.assertContains(response, "All Applications")
        self.assertContains(response, default_name)
        self.assertNotContains(response, "Other User pending contrib")
        self.assertNotContains(response, "Other User noncontrib")
        self.assertContains(response, "Other User contrib")

    def test_applications_mgr(self):
        response = self.client.get('/applications/mgr')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This page lists all members who are application managers.")
        self.assertContains(response, "All Applications")
        self.assertContains(response, default_name)
        self.assertNotContains(response, "Other User pending contrib")
        self.assertNotContains(response, "Other User noncontrib")
        self.assertNotContains(response, "Other User contrib")

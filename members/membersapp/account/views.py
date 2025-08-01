from django.contrib.auth.models import User
from django.contrib.auth import login as django_login
import django.contrib.auth.views as authviews
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from membersapp.account.util.decorators import login_required, script_sources, frame_sources, content_sources, queryparams
from django.views.decorators.csrf import csrf_exempt
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import logout as django_logout
from django.conf import settings
from django.db import transaction, connection
from django.db.models import Q, Prefetch
from django.shortcuts import render
from django.utils import timezone
from django.contrib import messages

import base64
import urllib.parse
from Cryptodome.Cipher import AES
from Cryptodome import Random
import time
import json
from datetime import datetime, timedelta, date
import itertools
import hmac

from membersapp.account.util.misc import send_template_mail, generate_random_token, get_client_ip
from membersapp.account.util.helpers import HttpSimpleResponse
from membersapp.account.util.propagate import send_change_to_apps

from membersapp.app.utils import get_current_user
from membersapp.app.models import Members, Applications

from .models import CommunityAuthSite, CommunityAuthConsent, SecondaryEmail
from .forms import PgwebAuthenticationForm, ConfirmSubmitForm
from .forms import CommunityAuthConsentForm
from .forms import SignupForm
from .forms import UserForm
from .forms import AddEmailForm, PgwebPasswordResetForm, MembersdjangoSetPasswordForm

import logging

from membersapp.account.util.mail import send_simple_mail

log = logging.getLogger(__name__)


objtypes = {
}


@login_required
@transaction.atomic
@script_sources('https://www.google.com/recaptcha/')
@script_sources('https://www.gstatic.com/recaptcha/')
@frame_sources('https://www.google.com/')
def profile(request):
    # We always have the user, but not always the profile. And we need a bit
    # of a hack around the normal forms code since we have two different
    # models on a single form.
    (profile, created) = Members.objects.get_or_create(pk=request.user.pk)

    # Don't allow users whose accounts were created via oauth to change
    # their email, since that would kill the connection between the
    # accounts.
    can_change_email = True

    # We may have a contributor record - and we only show that part of the
    # form if we have it for this user.
    contrib = None

    contribform = None

    secondaryaddresses = SecondaryEmail.objects.filter(user=request.user)

    if request.method == 'POST':
        # Process this form
        userform = UserForm(can_change_email, secondaryaddresses, data=request.POST, instance=request.user)
        secondaryemailform = AddEmailForm(request.user, get_client_ip(request), data=request.POST)

        if userform.is_valid() and secondaryemailform.is_valid() and (not contrib or contribform.is_valid()):
            user = userform.save()

            # Email takes some magic special handling, since we only allow picking of existing secondary emails, but it's
            # not a foreign key (due to how the django auth model works).
            if can_change_email and userform.cleaned_data['primaryemail'] != user.email:
                # Changed it!
                oldemail = user.email
                # Create a secondary email for the old primary one
                SecondaryEmail(user=user, email=oldemail, confirmed=True, token='').save()
                # Flip the main email
                user.email = userform.cleaned_data['primaryemail']
                user.save(update_fields=['email', ])
                # Finally remove the old secondary address, since it can`'t be both primary and secondary at the same time
                SecondaryEmail.objects.filter(user=user, email=user.email).delete()
                member = Members.objects.get(pk=user.id)
                member.email = user.email
                member.save()
                log.info("User {} changed primary email from {} to {}".format(user.username, oldemail, user.email))
                send_change_to_apps(user)
                messages.success(request, "Primary email address changed.")

            if contrib:
                contribform.save()
            if secondaryemailform.cleaned_data.get('email1', ''):
                sa = SecondaryEmail(user=request.user, email=secondaryemailform.cleaned_data['email1'], token=generate_random_token())
                sa.save()
                send_template_mail(
                    settings.ACCOUNTS_NOREPLY_FROM,
                    sa.email,
                    'Your SPI community account',
                    'email_add_email.txt',
                    {'secondaryemail': sa, 'user': request.user, }
                )

            change = False
            for k, v in request.POST.items():
                if k.startswith('deladdr_') and v == '1':
                    ii = int(k[len('deladdr_'):])
                    SecondaryEmail.objects.filter(user=request.user, id=ii).delete()
                    change = True

            if change:
                send_change_to_apps(user)
            return HttpResponseRedirect(".")
    else:
        # Generate form
        userform = UserForm(can_change_email, secondaryaddresses, instance=request.user)
        secondaryemailform = AddEmailForm(request.user, get_client_ip(request))

    user = get_current_user(request)
    return render(request, 'userprofileform.html', {
        'userform': userform,
        'secondaryemailform': secondaryemailform,
        'secondaryaddresses': secondaryaddresses,
        'secondarypending': any(not a.confirmed for a in secondaryaddresses),
        'contribform': contribform,
        'user': user,
        'recaptcha': True,
    })


@login_required
@transaction.atomic
def confirm_add_email(request, tokenhash):
    addr = get_object_or_404(SecondaryEmail, user=request.user, token=tokenhash)

    # Valid token found, so mark the address as confirmed.
    addr.confirmed = True
    addr.token = ''
    addr.save()
    send_change_to_apps(request.user)
    return HttpResponseRedirect('/account/profile/')


def login(request):
    return authviews.LoginView.as_view(template_name='login.html',
                                       authentication_form=PgwebAuthenticationForm,
                                       extra_context={
                                       })(request)


def logout(request):
    return authviews.logout_then_login(request, login_url='/')


def changepwd(request):
    log.info("Initiating password change from {0}".format(get_client_ip(request)))
    return authviews.PasswordChangeView.as_view(template_name='password_change.html',
                                                success_url='/account/changepwd/done/')(request)


def resetpwd(request):
    # Basic django password reset feature is completely broken. For example, it does not support
    # resetting passwords for users with "old hashes", which means they have no way to ever
    # recover. So implement our own, since it's quite the trivial feature.
    if request.method == "POST":
        try:
            u = User.objects.get(email__iexact=request.POST['email'])
        except User.DoesNotExist:
            log.info("Attempting to reset password of {0}, user not found".format(request.POST['email']))
            return HttpResponseRedirect('/account/reset/done/')

        form = PgwebPasswordResetForm(data=request.POST)
        if form.is_valid():
            log.info("Initiating password set from {0} for {1}".format(get_client_ip(request), form.cleaned_data['email']))
            token = default_token_generator.make_token(u)
            send_template_mail(
                settings.ACCOUNTS_NOREPLY_FROM,
                u.email,
                'Password reset for your SPI account',
                'password_reset_email.txt',
                {
                    'user': u,
                    'uid': urlsafe_base64_encode(force_bytes(u.pk)),
                    'token': token,
                },
            )
            return HttpResponseRedirect('/account/reset/done/')
    else:
        form = PgwebPasswordResetForm()

    return render(request, 'password_reset.html', {
        'form': form,
    })


def change_done(request):
    log.info("Password change done from {0}".format(get_client_ip(request)))
    return authviews.PasswordChangeDoneView.as_view(template_name='password_change_done.html')(request)


def reset_done(request):
    log.info("Password reset done from {0}".format(get_client_ip(request)))
    return authviews.PasswordResetDoneView.as_view(template_name='password_reset_done.html')(request)


def reset_confirm(request, uidb64, token):
    log.info("Confirming password reset for uidb {0}, token {1} from {2}".format(uidb64, token, get_client_ip(request)))
    return authviews.PasswordResetConfirmView.as_view(form_class=MembersdjangoSetPasswordForm,
                                                      template_name='password_reset_confirm.html',
                                                      success_url='/account/reset/complete/')(
                                                          request, uidb64=uidb64, token=token)


def reset_complete(request):
    log.info("Password reset completed for user from {0}".format(get_client_ip(request)))
    return authviews.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html')(request)


@script_sources('https://www.google.com/recaptcha/')
@script_sources('https://www.gstatic.com/recaptcha/')
@frame_sources('https://www.google.com/')
def signup(request):
    if request.user.is_authenticated:
        return HttpSimpleResponse(request, "Account error", "You must log out before you can sign up for a new account")

    if request.method == 'POST':
        # Attempt to create user then, eh?
        form = SignupForm(get_client_ip(request), data=request.POST)
        if form.is_valid():
            # Attempt to create the user here
            # XXX: Do we need to validate something else?
            log.info("Creating user for {0} from {1}".format(form.cleaned_data['username'], get_client_ip(request)))

            email = form.cleaned_data['email'].lower()
            user = User.objects.create_user(form.cleaned_data['username'].lower(), email, last_login=timezone.now())
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']

            # generate a random value for password. It won't be possible to log in with it, but
            # it creates more entropy for the token generator (I think).
            user.password = generate_random_token()
            user.save()

            # Create Member and Application
            member = Members(pk=user.pk,
                             name=user.first_name + ' ' + user.last_name,
                             email=email,
                             )
            member.save()

            app = Applications(member=member,
                               appdate=date.today(),
                               lastchange=date.today(),
                               contribapp=False,
                               contrib=False)
            app.save()

            # Now generate a token
            token = default_token_generator.make_token(user)
            log.info("Generated token {0} for user {1} from {2}".format(token, form.cleaned_data['username'], get_client_ip(request)))

            # Generate an outgoing email
            send_template_mail(settings.ACCOUNTS_NOREPLY_FROM,
                               form.cleaned_data['email'],
                               'Your new SPI community account',
                               'new_account_email.txt',
                               {'uid': urlsafe_base64_encode(force_bytes(user.id)), 'token': token, 'user': user}
                               )

            application = Applications.objects.get(member=user.pk)
            application.emailcheck_date = datetime.today()
            application.save()
            return HttpResponseRedirect('/account/signup/complete/')
    else:
        form = SignupForm(get_client_ip(request))

    return render(request, 'base/form.html', {
        'form': form,
        'formitemtype': 'Account',
        'form_intro': """
To sign up for a free community account, enter your preferred userid and email address.
Note that a community account is only needed if you want to submit information - all
content is available for reading without an account. A confirmation email will be sent
to the specified address, and once confirmed a password for the new account can be specified.
""",
        'savebutton': 'Sign up',
        'operation': 'New',
        'recaptcha': True,
    })


def signup_complete(request):
    return render(request, 'signup_complete.html', {
    })


####
# Community authentication endpoint
####
@queryparams('d', 'su')
def communityauth(request, siteid):
    # Get whatever site the user is trying to log in to.
    site = get_object_or_404(CommunityAuthSite, pk=siteid)

    # "suburl" - old style way of passing parameters
    # deprecated - will be removed once all sites have migrated
    if 'su' in request.GET:
        su = request.GET['su']
        if not su.startswith('/'):
            su = None
    else:
        su = None

    # "data" - new style way of passing parameter, where we only
    # care that it's characters are what's in base64.
    if 'd' in request.GET:
        d = request.GET['d']
        if d != urllib.parse.quote_plus(d, '=$'):
            # Invalid character, so drop it
            d = None
    else:
        d = None

    if d:
        urldata = "?d=%s" % d
    elif su:
        urldata = "?su=%s" % su
    else:
        urldata = ""

    # Verify if the user is authenticated, and if he/she is not, generate
    # a login form that has information about which site is being logged
    # in to, and basic information about how the community login system
    # works.
    if not request.user.is_authenticated:
        if request.method == "POST" and 'next' in request.POST and 'this_is_the_login_form' in request.POST:
            # This is a postback of the login form. So pick the next filed
            # from that one, so we keep it across invalid password entries.
            nexturl = request.POST['next']
        else:
            nexturl = '/account/auth/%s/%s' % (siteid, urldata)
        return authviews.LoginView.as_view(
            template_name='login.html',
            authentication_form=PgwebAuthenticationForm,
            extra_context={
                'sitename': site.name,
                'next': nexturl,
            },
        )(request)

    # When we reach this point, the user *has* already been authenticated.
    # The request variable "su" *may* contain a suburl and should in that
    # case be passed along to the site we're authenticating for. And of
    # course, we fill a structure with information about the user.

    if request.user.first_name == '' or request.user.last_name == '' or request.user.email == '':
        return render(request, 'communityauth_noinfo.html', {
        })

    # Check for cooloff period
    if site.cooloff_hours > 0:
        if (datetime.now() - request.user.date_joined) < timedelta(hours=site.cooloff_hours):
            log.warning("User {0} tried to log in to {1} before cooloff period ended.".format(
                request.user.username, site.name))
            return render(request, 'communityauth_cooloff.html', {
                'site': site,
            })

    if site.org.require_consent:
        if not CommunityAuthConsent.objects.filter(org=site.org, user=request.user).exists():
            return HttpResponseRedirect('/account/auth/{0}/consent/?{1}'.format(siteid,
                                                                                urllib.parse.urlencode({'next': '/account/auth/{0}/{1}'.format(siteid, urldata)})))

    # Record the login as the last login to this site. Django doesn't support tables with
    # multi-column PK, so we have to do this in a raw query.
    with connection.cursor() as curs:
        curs.execute("INSERT INTO account_communityauthlastlogin (user_id, site_id, lastlogin, logincount) VALUES (%(userid)s, %(siteid)s, CURRENT_TIMESTAMP, 1) ON CONFLICT (user_id, site_id) DO UPDATE SET lastlogin=CURRENT_TIMESTAMP, logincount=account_communityauthlastlogin.logincount+1", {
            'userid': request.user.id,
            'siteid': site.id,
        })

    info = {
        'u': request.user.username.encode('utf-8'),
        'f': request.user.first_name.encode('utf-8'),
        'l': request.user.last_name.encode('utf-8'),
        'e': request.user.email.encode('utf-8'),
        'se': ','.join([a.email for a in SecondaryEmail.objects.filter(user=request.user, confirmed=True).order_by('email')]).encode('utf8'),
        's': Members.objects.get(pk=request.user.pk).get_status.encode('utf-8'),
    }
    if d:
        info['d'] = d.encode('utf-8')
    elif su:
        info['su'] = su.encode('utf-8')

    # Turn this into an URL. Make sure the timestamp is always first, that makes
    # the first block more random..
    s = "t=%s&%s" % (int(time.time()), urllib.parse.urlencode(info))

    # Encrypt it with the shared key (and IV!)
    r = Random.new()
    iv = r.read(16)  # Always 16 bytes for AES
    encryptor = AES.new(base64.b64decode(site.cryptkey), AES.MODE_CBC, iv)
    cipher = encryptor.encrypt(s.encode('ascii') + b' ' * (16 - (len(s) % 16)))  # Pad to even 16 bytes

    # Generate redirect
    return HttpResponseRedirect("%s?i=%s&d=%s" % (
        site.redirecturl,
        base64.b64encode(iv, b"-_").decode('ascii'),
        base64.b64encode(cipher, b"-_").decode('ascii'),
    ))


def communityauth_logout(request, siteid):
    # Get whatever site the user is trying to log in to.
    site = get_object_or_404(CommunityAuthSite, pk=siteid)

    if request.user.is_authenticated:
        django_logout(request)

    # Redirect user back to the specified suburl
    return HttpResponseRedirect("%s?s=logout" % site.redirecturl)


@login_required
@queryparams('next')
def communityauth_consent(request, siteid):
    org = get_object_or_404(CommunityAuthSite, id=siteid).org
    if request.method == 'POST':
        form = CommunityAuthConsentForm(org.orgname, data=request.POST)
        if form.is_valid():
            CommunityAuthConsent.objects.get_or_create(user=request.user, org=org,
                                                       defaults={'consentgiven': datetime.now()},
                                                       )
            return HttpResponseRedirect(form.cleaned_data['next'])
    else:
        form = CommunityAuthConsentForm(org.orgname, initial={'next': request.GET.get('next', '')})

    return render(request, 'base/form.html', {
        'form': form,
        'operation': 'Authentication',
        'form_intro': 'The site you are about to log into is run by {0}. If you choose to proceed with this authentication, your name and email address will be shared with <em>{1}</em>.</p><p>Please confirm that you consent to this sharing.'.format(org.orgname, org.orgname),
        'savebutton': 'Proceed with login',
    })


def _encrypt_site_response(site, s):
    # Encrypt it with the shared key (and IV!)
    r = Random.new()
    iv = r.read(16)  # Always 16 bytes for AES
    encryptor = AES.new(base64.b64decode(site.cryptkey), AES.MODE_CBC, iv)
    cipher = encryptor.encrypt(s.encode('ascii') + b' ' * (16 - (len(s) % 16)))  # Pad to even 16 bytes

    # Base64-encode the response, just to be consistent
    return "%s&%s" % (
        base64.b64encode(iv, b'-_').decode('ascii'),
        base64.b64encode(cipher, b'-_').decode('ascii'),
    )


@queryparams('s', 'e', 'n', 'u')
def communityauth_search(request, siteid):
    # Perform a search for users. The response will be encrypted with the site
    # key to prevent abuse, therefor we need the site.
    site = get_object_or_404(CommunityAuthSite, pk=siteid)

    q = Q(is_active=True)
    if 's' in request.GET and request.GET['s']:
        # General search term, match both name and email
        q = q & (Q(email__icontains=request.GET['s']) | Q(first_name__icontains=request.GET['s']) | Q(last_name__icontains=request.GET['s']))
    elif 'e' in request.GET and request.GET['e']:
        q = q & Q(email__icontains=request.GET['e'])
    elif 'n' in request.GET and request.GET['n']:
        q = q & (Q(first_name__icontains=request.GET['n']) | Q(last_name__icontains=request.GET['n']))
    elif 'u' in request.GET and request.GET['u']:
        q = q & Q(username=request.GET['u'])
    else:
        raise Http404('No search term specified')

    users = User.objects.prefetch_related(Prefetch('secondaryemail_set', queryset=SecondaryEmail.objects.filter(confirmed=True))).filter(q)

    j = json.dumps([{
        'u': u.username,
        'e': u.email,
        'f': u.first_name,
        'l': u.last_name,
        'se': [a.email for a in u.secondaryemail_set.all()],
    } for u in users])

    return HttpResponse(_encrypt_site_response(site, j))


@csrf_exempt
def communityauth_subscribe(request, siteid):
    if 'X-pgauth-sig' not in request.headers:
        return HttpResponse("Missing signature header!", status=400)

    try:
        sig = base64.b64decode(request.headers['X-pgauth-sig'])
    except Exception:
        return HttpResponse("Invalid signature header!", status=400)

    site = get_object_or_404(CommunityAuthSite, pk=siteid)

    h = hmac.digest(
        base64.b64decode(site.cryptkey),
        msg=request.body,
        digest='sha512',
    )
    if not hmac.compare_digest(h, sig):
        return HttpResponse("Invalid signature!", status=401)

    try:
        j = json.loads(request.body)
    except Exception:
        return HttpResponse("Invalid JSON!", status=400)

    if 'u' not in j:
        return HttpResponse("Missing parameter", status=400)

    u = get_object_or_404(User, username=j['u'])

    with connection.cursor() as curs:
        # We handle the subscription by recording a fake login on this site
        curs.execute("INSERT INTO account_communityauthlastlogin (user_id, site_id, lastlogin, logincount) VALUES (%(userid)s, %(siteid)s, CURRENT_TIMESTAMP, 1) ON CONFLICT (user_id, site_id) DO UPDATE SET lastlogin=CURRENT_TIMESTAMP, logincount=account_communityauthlastlogin.logincount+1", {
            'userid': u.id,
            'siteid': site.id,
        })

        # And when we've done that, we also trigger a sync on this particular site
        curs.execute("INSERT INTO account_communityauthchangelog (user_id, site_id, changedat) VALUES (%(userid)s, %(siteid)s, CURRENT_TIMESTAMP) ON CONFLICT (user_id, site_id) DO UPDATE SET changedat=greatest(account_communityauthchangelog.changedat, CURRENT_TIMESTAMP)", {
            'userid': u.id,
            'siteid': site.id,
        })

    return HttpResponse(status=201)

from django.db import connection
from django.conf import settings

from Cryptodome.Hash import SHA256
from Cryptodome import Random

from membersapp.account.util.mail import send_simple_mail
from membersapp.account.util.helpers import template_to_string
import re


def send_template_mail(sender, receiver, subject, templatename, templateattr={}, usergenerated=False, cc=None, replyto=None, receivername=None, sendername=None, messageid=None, suppress_auto_replies=True, is_auto_reply=False):
    d = {
        'link_root': settings.SITE_ROOT,
    }
    d.update(templateattr)
    send_simple_mail(
        sender, receiver, subject,
        template_to_string(templatename, d),
        usergenerated=usergenerated, cc=cc, replyto=replyto,
        receivername=receivername, sendername=sendername,
        messageid=messageid,
        suppress_auto_replies=suppress_auto_replies,
        is_auto_reply=is_auto_reply,
    )


def get_client_ip(request):
    """
    Get the IP of the client. If the client is served through our Varnish caches,
    or behind one of our SSL proxies, make sure to get the *actual* client IP,
    and not the IP of the cache/proxy.
    """
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        # There is a x-forwarded-for header, so trust it but only if the actual connection
        # is coming in from one of our frontends.
        if request.META['REMOTE_ADDR'] in settings.FRONTEND_SERVERS:
            return request.META['HTTP_X_FORWARDED_FOR']

    # Else fall back and return the actual IP of the connection
    return request.META['REMOTE_ADDR']


def generate_random_token():
    """
    Generate a random token of 64 characters. This token will be
    generated using a strong random number, and then hex encoded to make
    sure all characters are safe to put in emails and URLs.
    """
    s = SHA256.new()
    r = Random.new()
    s.update(r.read(250))
    return s.hexdigest()

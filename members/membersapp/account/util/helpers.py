from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.template.loader import get_template
from django.conf import settings

import io
import difflib

from membersapp.account.util.mail import send_simple_mail


def template_to_string(templatename, attrs={}):
    return get_template(templatename).render(attrs)


def HttpServerError(request, msg):
    r = render(request, 'errors/500.html', {
        'message': msg,
    })
    r.status_code = 500
    return r


def HttpSimpleResponse(request, title, msg):
    return render(request, 'simple.html', {
        'title': title,
        'message': msg,
    })

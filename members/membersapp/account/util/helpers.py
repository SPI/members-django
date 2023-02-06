from django.shortcuts import render, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.template.loader import get_template
import django.utils.xmlutils
from django.conf import settings

from membersapp.account.util.contexts import render_pgweb

import io
import difflib

from membersapp.account.mailqueue.util import send_simple_mail


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


class PgXmlHelper(django.utils.xmlutils.SimplerXMLGenerator):
    def __init__(self, outstream, skipempty=False):
        django.utils.xmlutils.SimplerXMLGenerator.__init__(self, outstream, 'utf-8')
        self.skipempty = skipempty

    def add_xml_element(self, name, value):
        if self.skipempty and value == '':
            return
        self.startElement(name, {})
        self.characters(value)
        self.endElement(name)

import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.contrib.auth.decorators import login_required

from membersapp.app.stats import get_stats
from membersapp.app.votes import get_votes
from membersapp.app.applications import *
from .models import Members, Applications


def index(request):
    if not request.user.is_authenticated:
        template = loader.get_template('index.html')
        context = {}
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('status.html')
        user, _ = Members.object.get_or_create(name=request.user)
        context = {
            'votes': get_votes(request.user, active=True),
            'votes2': get_votes(request.user, owner=request.user),
            'applications': get_applications_by_user(user),
            'applicants': get_applications(user),
            'user': user
        }
        return HttpResponse(template.render(context, request))


def application(request, appid):
    if not request.user.is_authenticated:
        context = {}
        template = loader.get_template('index.html')
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('application.html')
        application = get_object_or_404(Applications, appid=appid)
        member = Members.object.get(memid=application.member_id)
        context = {
            'application': application,
            'member': member
        }
        return HttpResponse(template.render(context, request))


def updateactive(request):
    """Update a users most recently active date and redirect to main page"""
    user = get_current_user(request)
    user.lastactive = datetime.date.today()
    user.save()
    return HttpResponseRedirect("/")


def showstats(request):
    """Handler for showing membership statistics"""
    stats = get_stats()
    print(stats)

    return render(request, 'stats.html', {'stats': stats})

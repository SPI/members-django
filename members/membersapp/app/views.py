import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse

from membersapp.app.stats import get_stats
from membersapp.app.votes import get_votes
from membersapp.app.applications import *
from .models import Members, Applications
from .forms import *


def index(request):
    if not request.user.is_authenticated:
        template = loader.get_template('index.html')
        context = {}
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('status.html')
        user = get_current_user(request)
        form = MemberForm(instance=user)
        context = {
            'votes': get_votes(request.user, active=True),
            'votes2': get_votes(request.user, owner=request.user),
            'applications': get_applications_by_user(user),
            'applicants': get_applications(user),
            'user': user,
            'form': form
        }
        return HttpResponse(template.render(context, request))


@login_required
def application(request, appid):
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


@login_required
def memberedit(request):
    if request.method == 'POST':
        user = get_current_user(request)
        form = MemberForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
    return HttpResponseRedirect(reverse('index'))


class MemberEditView(LoginRequiredMixin, UpdateView):
    model = Members
    fields = ['sub_private']

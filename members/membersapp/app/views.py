import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.db.models import Q

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
    user = get_current_user(request)
    memberform = MemberForm(instance=member)
    applicationform = ApplicationForm(instance=application)
    context = {
        'application': application,
        'member': member,
        'user': user,
        'memberform': memberform,
        'applicationform': applicationform
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
    user = get_current_user(request)
    return render(request, 'stats.html', {'stats': stats, 'user': user})


def showapplications(request, listtype):
    template = loader.get_template('applications.html')
    if listtype == 'ncm':
        applications = Applications.objects.filter(Q(member__iscontrib=False) & (Q(contribapp=False) | Q(contribapp__isnull=True)))
    elif listtype == 'ca':
        applications = Applications.objects.filter(Q(approve__isnull=True) & Q(contribapp=True))
    elif listtype == 'cm':
        applications = Applications.objects.filter(Q(member__iscontrib=True) & Q(contribapp=True))
    elif listtype == 'mgr':
        applications = Applications.objects.filter(Q(member__ismanager=True) & Q(contribapp=True))
    else:
        applications = Applications.objects.all()
    sorted_applications = applications.order_by('appid')
    user = get_current_user(request)
    context = {
        'applicants': sorted_applications,
        'listtype': listtype,
        'user': user
    }
    return HttpResponse(template.render(context, request))


@login_required
def showmember(request, memid):
    # todo: check manager privileges
    template = loader.get_template('member.html')
    member = Members.object.get(pk=memid)
    user = get_current_user(request)
    context = {
        'user': user,
        'member': member,
        'applications': get_applications_by_user(member)
    }
    return HttpResponse(template.render(context, request))


@login_required
def memberedit(request):
    if request.method == 'POST':
        user = get_current_user(request)
        form = MemberForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
    return HttpResponseRedirect(reverse('index'))


@login_required
def applicationedit(request, appid):
    # todo: check edit privileges
    if request.method == 'POST':
        application = Applications.objects.get(pk=appid)
        memberform = MemberForm(request.POST, instance=application.member)
        applicationform = ApplicationForm(request.POST, instance=application)
        if memberform.is_valid() and applicationform.is_valid():
            memberform.save()
            applicationform.save()
    return HttpResponseRedirect(reverse('application', args=[appid]))


class MemberEditView(LoginRequiredMixin, UpdateView):
    model = Members
    fields = ['sub_private']

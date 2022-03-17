from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.decorators import login_required

from members.app.stats import get_stats


def index(request):
    template = loader.get_template('base.html')
    context = {}
    return HttpResponse(template.render(context, request))


def showstats(request):
    """Handler for showing membership statistics"""
    stats = get_stats()
    print(stats)

    return render(request, 'stats.html', {'stats': stats})

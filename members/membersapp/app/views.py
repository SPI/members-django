from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.decorators import login_required

from membersapp.app.stats import get_stats
from membersapp.app.votes import get_votes
from membersapp.app.applications import get_applications

def index(request):
    if not request.user.is_authenticated:
        template = loader.get_template('index.html')
        context = {}
        return HttpResponse(template.render(context, request))
    else:
        template = loader.get_template('status.html')
        context = {
            'votes': get_votes(request.user, active=True),
            'votes2': get_votes(request.user, owner=request.user),
            'applications': get_applications(request.user)
        }
        return HttpResponse(template.render(context, request))


def showstats(request):
    """Handler for showing membership statistics"""
    stats = get_stats()
    print(stats)

    return render(request, 'stats.html', {'stats': stats})

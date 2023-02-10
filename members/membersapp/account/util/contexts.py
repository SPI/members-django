from django.shortcuts import render


def render_pgweb(request, section, template, context):
    context['navmenu'] = {}
    return render(request, template, context)

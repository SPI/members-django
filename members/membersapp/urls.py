"""members URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import url, include
from django.urls import path
from django.contrib.auth.decorators import login_required

from membersapp.app import views
import membersapp.auth

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('stats/', views.showstats, name='stats'),
    path('application/<int:appid>', views.application, name='application'),
    path('updateactive', views.updateactive, name='updateactive'),
    path('member/<int:memid>', views.showmember, name='member'),
    path('member/edit', views.memberedit, name='memberedit'),
    path('applications/<str:listtype>', views.showapplications, name='applications'),
    path('application/<int:appid>/edit', views.applicationedit, name='applicationedit'),
    path('apply/contrib', views.contribapplication, name='contribapplication'),
    path('votes', views.showvotes, name='votes'),
    path('vote/<int:ref>', views.showvote, name='vote'),
    path('vote/create', views.votecreate, name='votecreate'),
    path('vote/<int:ref>/edit', views.voteedit, name='voteedit'),

    # Auth system integration
    url(r'^(?:accounts/)?login/?$', membersapp.auth.login),
    url(r'^(?:accounts/)?logout/?$', membersapp.auth.logout),
    url(r'^auth_receive/$', membersapp.auth.auth_receive),
    url(r'^auth_api/$', membersapp.auth.auth_api),

]

handler404 = 'membersapp.app.views.handler404'

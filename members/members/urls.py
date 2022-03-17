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

from members.app import views
import members.auth

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('stats/', views.showstats, name='stats'),

    # Auth system integration
    url(r'^(?:accounts/)?login/?$', members.auth.login),
    url(r'^(?:accounts/)?logout/?$', members.auth.logout),
    url(r'^auth_receive/$', members.auth.auth_receive),
    url(r'^auth_api/$', members.auth.auth_api),

]
#    url(r'^$', include('app.urls')),

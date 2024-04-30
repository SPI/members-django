from django.urls import path, re_path
from django.conf import settings

import membersapp.account.views

urlpatterns = [
    # Community authenticatoin
    re_path(r'^auth/(\d+)/$', membersapp.account.views.communityauth),
    re_path(r'^auth/(\d+)/logout/$', membersapp.account.views.communityauth_logout),
    re_path(r'^auth/(\d+)/consent/$', membersapp.account.views.communityauth_consent),
    re_path(r'^auth/(\d+)/search/$', membersapp.account.views.communityauth_search),
    re_path(r'^auth/(\d+)/subscribe/$', membersapp.account.views.communityauth_subscribe),

    # Profile
    path('profile/', membersapp.account.views.profile),
    re_path(r'^profile/add_email/([0-9a-f]+)/$', membersapp.account.views.confirm_add_email),

    # Log in, logout, change password etc
    path('login/', membersapp.account.views.login),
    path('logout/', membersapp.account.views.logout),
    path('changepwd/', membersapp.account.views.changepwd),
    path('changepwd/done/', membersapp.account.views.change_done),
    path('reset/', membersapp.account.views.resetpwd),
    path('reset/done/', membersapp.account.views.reset_done),
    re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)-(?P<token>[0-9A-Za-z]+-[0-9A-Za-z]+)/$', membersapp.account.views.reset_confirm),
    path('reset/complete/', membersapp.account.views.reset_complete),
    path('signup/', membersapp.account.views.signup),
    path('signup/complete/', membersapp.account.views.signup_complete),
]

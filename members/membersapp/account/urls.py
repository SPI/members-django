from django.conf.urls import url
from django.conf import settings

import membersapp.account.views

urlpatterns = [
    # Community authenticatoin
    url(r'^auth/(\d+)/$', membersapp.account.views.communityauth),
    url(r'^auth/(\d+)/logout/$', membersapp.account.views.communityauth_logout),
    url(r'^auth/(\d+)/consent/$', membersapp.account.views.communityauth_consent),
    url(r'^auth/(\d+)/search/$', membersapp.account.views.communityauth_search),
    url(r'^auth/(\d+)/subscribe/$', membersapp.account.views.communityauth_subscribe),

    # Profile
    url(r'^profile/$', membersapp.account.views.profile),
    url(r'^profile/add_email/([0-9a-f]+)/$', membersapp.account.views.confirm_add_email),

    # Log in, logout, change password etc
    url(r'^login/$', membersapp.account.views.login),
    url(r'^logout/$', membersapp.account.views.logout),
    url(r'^changepwd/$', membersapp.account.views.changepwd),
    url(r'^changepwd/done/$', membersapp.account.views.change_done),
    url(r'^reset/$', membersapp.account.views.resetpwd),
    url(r'^reset/done/$', membersapp.account.views.reset_done),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)-(?P<token>[0-9A-Za-z]+-[0-9A-Za-z]+)/$', membersapp.account.views.reset_confirm),
    url(r'^reset/complete/$', membersapp.account.views.reset_complete),
    url(r'^signup/$', membersapp.account.views.signup),
    url(r'^signup/complete/$', membersapp.account.views.signup_complete),
]

from django.conf import settings


def settings_pgauth(request):
    return {
        'PGAUTH_SIGNUP': settings.PGAUTH_SIGNUP,
        'PGAUTH_CHANGEPASSWD': settings.PGAUTH_CHANGEPASSWD,
        'PGAUTH_ROOT': settings.PGAUTH_ROOT,
        'LOGIN_URL': settings.LOGIN_URL,
        'LOGOUT_URL': settings.LOGOUT_URL
    }

from django.conf import settings


def settings_pgauth(request):
    return {
        'LOGIN_URL': settings.LOGIN_URL,
        'LOGOUT_URL': settings.LOGOUT_URL,
        'SIGNUP_URL': settings.SIGNUP_URL,
        'CHANGEPASSWD_URL': settings.CHANGEPASSWD_URL,
        'RESETPASSWD_URL': settings.RESETPASSWD_URL,
        'ACCOUNT_URL': settings.ACCOUNT_URL
    }

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import REDIRECT_FIELD_NAME, authenticate, login as auth_login
from django.shortcuts import redirect, resolve_url
from django.utils.http import is_safe_url

DEBUG_USERNAME = 'webmaster'

class DebugUserBackend(object):
    def authenticate(self):
        try:
            return User.objects.get(username=DEBUG_USERNAME)
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

def login(request, redirect_field_name=REDIRECT_FIELD_NAME):
    redirect_to = request.POST.get(redirect_field_name,
                                   request.GET.get(redirect_field_name, ''))
    user = authenticate()
    # Ensure the user-originating redirection url is safe.
    if not is_safe_url(url=redirect_to, host=request.get_host()):
        redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)
    auth_login(request, user)
    return redirect(redirect_to)

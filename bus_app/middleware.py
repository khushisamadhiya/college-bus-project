# your_app/middleware.py
from django.shortcuts import redirect
from django.conf import settings
import re

# ✅ Add all URLs you want to exempt from login here
EXEMPT_URLS = [
    re.compile(settings.LOGIN_URL.lstrip('/')),  # /login/
    re.compile('student-form/?$'),
    re.compile('api/get-schools/?$'),
    re.compile('api/get-routes/?$'),
    re.compile('api/get-programs/?$'),
    re.compile('api/get-stoppages/?$'),
    re.compile('api/register-student/?$'),
    re.compile('success/?$'),
    re.compile('about/?$'),
    re.compile('thank-you/?$'),
    re.compile('choice/?$'),
    re.compile('feedback/?$'),
    re.compile('all-feedbacks/?$'),
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info.lstrip('/')

        # ✅ If not logged in and URL is not in exempt list, redirect to login
        if not request.user.is_authenticated:
            if not any(url.match(path) for url in EXEMPT_URLS):
                return redirect(settings.LOGIN_URL)

        return self.get_response(request)

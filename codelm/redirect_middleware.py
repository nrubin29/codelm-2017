from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils import timezone

ok_paths = (
    '/api/logout'
)


class CompetitionRedirectMiddleware:
    """
    Middleware that redirects users to the ending page once their time is up.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        if request.path not in ok_paths and request.user.is_authenticated:
            if request.user.team.did_end:
                return HttpResponseRedirect(resolve_url('index'))

        return self.get_response(request)

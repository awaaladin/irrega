"""Tiny in-memory rate limiter for auth and write endpoints (swap for Redis in production)."""
import time
from collections import defaultdict, deque

from django.http import HttpResponse

LIMITS = {"/accounts/login/": (10, 60), "/accounts/register/": (10, 60), "/api/ask/": (30, 60)}
_hits = defaultdict(deque)


class SimpleRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rule = LIMITS.get(request.path)
        if rule and request.method == "POST":
            limit, window = rule
            key = (request.path, request.META.get("REMOTE_ADDR", ""))
            q = _hits[key]
            now = time.monotonic()
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return HttpResponse("Too many attempts. Please wait a minute and try again.", status=429)
            q.append(now)
        return self.get_response(request)

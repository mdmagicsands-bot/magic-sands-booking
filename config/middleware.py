"""Early /health/ response for Railway probes (before SSL redirect / host checks)."""

from django.conf import settings
from django.http import JsonResponse


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path in {"/health", "/health/"}:
            service = (
                "magic-sands-marketing" if settings.MARKETING_ONLY else "magic-sands-booking"
            )
            return JsonResponse(
                {
                    "status": "ok",
                    "service": service,
                    "profile": settings.SITE_PROFILE,
                }
            )
        return self.get_response(request)

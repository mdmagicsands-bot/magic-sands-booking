from django.conf import settings
from django.http import JsonResponse


def health(_request):
    service = "magic-sands-marketing" if settings.MARKETING_ONLY else "magic-sands-booking"
    return JsonResponse(
        {
            "status": "ok",
            "service": service,
            "profile": settings.SITE_PROFILE,
        }
    )

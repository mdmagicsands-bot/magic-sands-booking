"""Send booking traffic to the separate booking site when marketing runs alone."""

from django.conf import settings
from django.http import HttpResponseRedirect


def redirect_to_booking_site(request, path: str = ""):
    base = settings.PUBLIC_BOOKING_URL.rstrip("/")
    target = f"{base}{path or request.path}"
    query = request.META.get("QUERY_STRING", "").strip()
    if query:
        target = f"{target}?{query}"
    return HttpResponseRedirect(target)

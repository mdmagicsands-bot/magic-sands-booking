from django.conf import settings
from django.urls import NoReverseMatch, reverse

from marketing.content import MEDIA, marketing_page_url

from .menu import GUEST_MENU
from .models import GuestProfile


def _booking_page_url(request, url_name: str, path: str) -> str:
    """Absolute URL on the booking app (Railway/local), not the Hostinger marketing site."""
    try:
        return request.build_absolute_uri(reverse(url_name))
    except NoReverseMatch:
        base = getattr(settings, "PUBLIC_BOOKING_URL", "http://127.0.0.1:8001").rstrip("/")
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{base}{path}"


def guest_portal_nav(request):
    path = request.path or ""
    if not (path.startswith("/partner/") or path.startswith("/account/")):
        return {}

    current = ""
    if getattr(request, "resolver_match", None):
        current = request.resolver_match.url_name or ""

    items = []
    for entry in GUEST_MENU:
        children = []
        for child in entry.get("children") or []:
            try:
                href = reverse(child["url_name"])
            except NoReverseMatch:
                continue
            children.append(
                {
                    "label": child["label"],
                    "href": href,
                    "active": current in (child.get("match") or []),
                }
            )

        href = "#"
        if entry.get("url_name"):
            try:
                href = reverse(entry["url_name"])
            except NoReverseMatch:
                href = "#"
        elif children:
            href = children[0]["href"]

        match = entry.get("match") or []
        active = current in match or any(c["active"] for c in children)
        items.append(
            {
                "label": entry["label"],
                "href": href,
                "active": active,
                "children": children,
                "placeholder": bool(entry.get("placeholder")),
            }
        )

    profile = None
    display_name = ""
    partner_credit = {
        "limit": "0.00",
        "available": "0.00",
        "used": "0.00",
        "currency": "USD",
    }
    if request.user.is_authenticated:
        if not request.user.is_staff:
            profile = GuestProfile.objects.filter(user=request.user).first()
            if profile:
                partner_credit = profile.credit_summary()
        display_name = (
            (profile.display_name if profile else "")
            or request.user.get_full_name().strip()
            or request.user.get_username()
        )

    return {
        "guest_nav_items": items,
        "guest_menu_groups": [],  # legacy key kept for older templates
        "partner_logo_url": MEDIA.get("logo", ""),
        "partner_display_name": display_name,
        "partner_location": "United Arab Emirates",
        "partner_credit": partner_credit,
        "marketing_site_links": {
            "home": marketing_page_url("/"),
            "about": marketing_page_url("/about"),
            "contact": marketing_page_url("/contact"),
            "privacy": _booking_page_url(request, "privacy_policy", "/privacy-policy/"),
            "terms": marketing_page_url("/contact") + "?topic=terms",
        },
    }

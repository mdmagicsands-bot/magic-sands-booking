from django.urls import NoReverseMatch, reverse

from .menu import MENU_GROUPS


def booking_admin_nav(request):
    """Build sidebar nav for booking admin pages."""
    path = request.path or ""
    if not path.startswith("/admin/"):
        return {}
    # Exclude hub + login + marketing CMS + logout
    skip_prefixes = (
        "/admin/login",
        "/admin/logout",
        "/admin/marketing",
    )
    if path.rstrip("/") == "/admin" or any(path.startswith(p) for p in skip_prefixes):
        return {}

    current = ""
    if getattr(request, "resolver_match", None):
        current = request.resolver_match.url_name or ""

    groups = []
    for group in MENU_GROUPS:
        items = []
        for item in group["items"]:
            href = item.get("href")
            if not href:
                try:
                    href = reverse(item["url_name"])
                except NoReverseMatch:
                    continue
                query = item.get("query") or ""
                href = f"{href}{query}"
            active = current in (item.get("match") or [])
            items.append(
                {
                    "label": item["label"],
                    "href": href,
                    "active": active,
                    "external": bool(item.get("external")),
                }
            )
        if items:
            groups.append(
                {
                    "label": group["label"],
                    "items": items,
                    "open": any(i["active"] for i in items),
                }
            )
    return {"booking_menu_groups": groups}

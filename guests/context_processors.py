from django.urls import NoReverseMatch, reverse

from .menu import GUEST_MENU


def guest_portal_nav(request):
    path = request.path or ""
    if not path.startswith("/account/"):
        return {}

    current = ""
    if getattr(request, "resolver_match", None):
        current = request.resolver_match.url_name or ""

    groups = []
    for group in GUEST_MENU:
        items = []
        for item in group["items"]:
            try:
                href = reverse(item["url_name"])
            except NoReverseMatch:
                continue
            items.append(
                {
                    "label": item["label"],
                    "href": href,
                    "active": current in (item.get("match") or []),
                }
            )
        if items:
            groups.append({"label": group["label"], "items": items})
    return {"guest_menu_groups": groups}

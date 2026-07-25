from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from . import content


def _ctx(**extra):
    data = {
        "brand": content.BRAND,
        "brand_full": content.BRAND_FULL,
        "tagline": content.TAGLINE,
        "destinations": content.DESTINATIONS,
        "offices": content.OFFICES,
    }
    data.update(extra)
    return data


@require_GET
def home(request):
    return render(
        request,
        "marketing/home.html",
        _ctx(
            hero=content.HERO,
            about_blurb=content.ABOUT_BLURB,
            services=content.SERVICES[:4],
            stats=content.STATS,
            testimonials=content.TESTIMONIALS,
        ),
    )


@require_GET
def about(request):
    return render(
        request,
        "marketing/about.html",
        _ctx(about_blurb=content.ABOUT_BLURB, stats=content.STATS),
    )


@require_GET
def services(request):
    return render(
        request,
        "marketing/services.html",
        _ctx(services=content.SERVICES),
    )


@require_GET
def destinations(request):
    return render(request, "marketing/destinations.html", _ctx())


@require_GET
def destination_detail(request, slug: str):
    match = next((d for d in content.DESTINATIONS if d["slug"] == slug), None)
    if not match:
        return redirect("destinations")
    return render(
        request,
        "marketing/destination_detail.html",
        _ctx(destination=match),
    )


@require_GET
def testimonials(request):
    return render(
        request,
        "marketing/testimonials.html",
        _ctx(testimonials=content.TESTIMONIALS),
    )


@require_http_methods(["GET", "POST"])
def contact(request):
    sent = False
    if request.method == "POST":
        # v1: capture locally via messages UX; wire email/CRM later on Railway
        sent = True
    return render(
        request,
        "marketing/contact.html",
        _ctx(sent=sent),
    )

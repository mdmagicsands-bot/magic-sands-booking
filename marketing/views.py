from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from . import catalog, content
from .models import ContactMessage


def _ctx(**extra):
    settings_data = catalog.get_settings()
    data = {
        "brand": settings_data["brand"],
        "brand_full": settings_data["brand_full"],
        "tagline": settings_data["tagline"],
        "destinations": catalog.get_destinations(),
        "offices": catalog.get_offices(),
        "media": content.MEDIA,
        "social": content.SOCIAL,
        "site_url": content.SITE_URL,
    }
    data.update(extra)
    return data


@require_GET
def home(request):
    settings_data = catalog.get_settings()
    return render(
        request,
        "marketing/home.html",
        _ctx(
            hero=settings_data["hero"],
            hero_banners=content.HERO_BANNERS,
            about_blurb=settings_data["about_blurb"],
            elevating=settings_data["elevating"],
            services=catalog.get_services(),
            why_choose=catalog.get_why_choose(),
            partners=content.PARTNERS,
            testimonials=catalog.get_testimonials(limit=6),
        ),
    )


@require_GET
def about(request):
    settings_data = catalog.get_settings()
    return render(
        request,
        "marketing/about.html",
        _ctx(
            about_page=settings_data["about_page"],
            differentiators=content.DIFFERENTIATORS,
            values=content.VALUES,
        ),
    )


@require_GET
def services(request):
    return render(
        request,
        "marketing/services.html",
        _ctx(services=catalog.get_services()),
    )


@require_GET
def destinations(request):
    return render(request, "marketing/destinations.html", _ctx())


@require_GET
def destination_detail(request, slug: str):
    match = next((d for d in catalog.get_destinations() if d["slug"] == slug), None)
    if not match:
        return redirect("destinations")
    return render(
        request,
        "marketing/destination_detail.html",
        _ctx(destination=match, services=catalog.get_services()[:3]),
    )


@require_GET
def testimonials(request):
    return render(
        request,
        "marketing/testimonials.html",
        _ctx(testimonials=catalog.get_testimonials()),
    )


@require_http_methods(["GET", "POST"])
def contact(request):
    sent = False
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        company = (request.POST.get("company") or "").strip()
        message = (request.POST.get("message") or "").strip()
        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                company=company,
                message=message,
            )
            sent = True
    return render(
        request,
        "marketing/contact.html",
        _ctx(sent=sent),
    )

from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from . import catalog, content
from .assets import resolve_ms_url
from .legal_content import PRIVACY_POLICY
from .live_content import HERO_SLIDES, HOME_SERVICES, MEET_US, PARTNER_LOGOS, VIDEO
from .models import ContactMessage, Testimonial


def _ctx(**extra):
    settings_data = catalog.get_settings()
    data = {
        "brand": settings_data["brand"],
        "brand_full": settings_data["brand_full"],
        "tagline": settings_data["tagline"],
        "destinations": catalog.get_destinations(),
        "offices": catalog.get_offices(),
        "media": {key: resolve_ms_url(url) for key, url in content.MEDIA.items()},
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
            hero_slides=HERO_SLIDES,
            hero_banners=content.HERO_BANNERS,
            about_blurb=settings_data["about_blurb"],
            elevating=settings_data["elevating"],
            home_services=HOME_SERVICES,
            services=catalog.get_services(),
            why_choose=catalog.get_why_choose(),
            partner_logos=PARTNER_LOGOS,
            partners=content.PARTNERS,
            meet_us=MEET_US,
            video=VIDEO,
            testimonials=catalog.get_testimonials(limit=4),
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
            header_color=True,
        ),
    )


@require_GET
def services(request):
    return render(
        request,
        "marketing/services.html",
        _ctx(services=catalog.get_services(), header_color=True),
    )


@require_GET
def destinations(request):
    return render(request, "marketing/destinations.html", _ctx(header_color=True))


@require_GET
def destination_detail(request, slug: str):
    destinations = catalog.get_destinations()
    match = next((d for d in destinations if d["slug"] == slug), None)
    if not match:
        return redirect("destinations")
    dest_index = next((i + 1 for i, d in enumerate(destinations) if d["slug"] == slug), 1)
    return render(
        request,
        "marketing/destination_detail.html",
        _ctx(destination=match, services=catalog.get_services()[:3], header_color=True),
    )


@require_GET
def testimonials(request):
    return render(
        request,
        "marketing/testimonials.html",
        _ctx(testimonials=catalog.get_testimonials(), header_color=True),
    )


@require_http_methods(["GET", "POST"])
def submit_your_review(request):
    """Public feedback form — creates an unpublished testimonial for staff approval."""
    from django.contrib import messages

    from .forms import PublicReviewForm

    form = PublicReviewForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        name = f"{data['fname'].strip()} {data['lname'].strip()}".strip()
        obj = Testimonial(
            name=name,
            email=(data.get("email") or "").strip(),
            quote=data["content"].strip(),
            rating=int(data["rating"]),
            date_from=data["fdate"],
            date_to=data["tdate"],
            is_published=False,
            sort_order=9999,
            image=data.get("image"),
        )
        obj.sync_role_from_dates()
        obj.save()
        messages.success(request, "Thank you for your review!")
        return redirect("submit_your_review")

    return render(
        request,
        "marketing/submit_your_review.html",
        _ctx(form=form, header_color=True),
    )


@require_GET
def privacy_policy(request):
    return render(
        request,
        "marketing/privacy_policy.html",
        _ctx(privacy=PRIVACY_POLICY, header_color=True),
    )


@require_http_methods(["GET", "POST"])
def contact(request):
    sent = False
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email_r") or request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        message = (request.POST.get("message") or "").strip()
        honeypot = (request.POST.get("email") or "").strip()
        if honeypot:
            email = ""
        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                company=phone,
                message=message,
            )
            sent = True
    return render(
        request,
        "marketing/contact.html",
        _ctx(
            sent=sent,
            header_color=True,
            contact_banner=resolve_ms_url(
                "https://www.magicsandsdmc.com/assets/images/c-banner.jpg",
                default="https://www.magicsandsdmc.com/assets/images/c-banner.jpg",
            ),
            contact_map_embed=content.CONTACT_MAP_EMBED,
        ),
    )

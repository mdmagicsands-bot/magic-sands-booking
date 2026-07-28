"""Resolve public marketing content from the CMS database, with static fallbacks."""

from . import content
from .assets import ms, resolve_ms_url
from .models import (
    Destination,
    MarketingSettings,
    Office,
    Service,
    Testimonial,
    WhyChooseItem,
)

_TESTIMONIAL_DEFAULT = ms("uploads/testimonial/default.png")
_TESTIMONIAL_BY_NAME = {t["name"].lower(): t for t in content.TESTIMONIALS}


def _resolve_testimonial_row(row, *, fallback=None):
    fb = fallback or {}
    if isinstance(row, dict):
        quote = row.get("quote", "")
        name = row.get("name", "")
        role = row.get("role", "")
        rating = row.get("rating", 5)
        raw_image = row.get("image") or fb.get("image")
    else:
        quote = row.quote
        name = row.name
        role = row.role
        rating = fb.get("rating", 5)
        raw_image = fb.get("image")
    image = resolve_ms_url(raw_image, default=_TESTIMONIAL_DEFAULT)
    return {
        "quote": quote,
        "name": name,
        "role": role,
        "image": image,
        "rating": rating,
    }


def get_settings():
    settings_obj = MarketingSettings.objects.first()
    if not settings_obj:
        return {
            "brand": content.BRAND,
            "brand_full": content.BRAND_FULL,
            "tagline": content.TAGLINE,
            "hero": content.HERO,
            "about_blurb": content.ABOUT_BLURB,
            "elevating": content.ELEVATING,
            "about_page": content.ABOUT_PAGE,
        }

    return {
        "brand": settings_obj.brand or content.BRAND,
        "brand_full": settings_obj.brand_full or content.BRAND_FULL,
        "tagline": settings_obj.tagline or content.TAGLINE,
        "hero": {
            "brand": settings_obj.brand or content.BRAND,
            "title": settings_obj.hero_title or content.HERO["title"],
            "lede": settings_obj.hero_lede or content.HERO["lede"],
        },
        "about_blurb": settings_obj.about_blurb or content.ABOUT_BLURB,
        "elevating": {
            "title": settings_obj.elevating_title or content.ELEVATING["title"],
            "text": settings_obj.elevating_text or content.ELEVATING["text"],
        },
        "about_page": {
            "intro_title": settings_obj.about_intro_title or content.ABOUT_PAGE["intro_title"],
            "intro": settings_obj.about_intro or content.ABOUT_PAGE["intro"],
            "expertise": settings_obj.about_expertise or content.ABOUT_PAGE["expertise"],
            "story": settings_obj.about_story or content.ABOUT_PAGE["story"],
            "boutique_title": content.ABOUT_PAGE["boutique_title"],
            "boutique": settings_obj.about_boutique or content.ABOUT_PAGE["boutique"],
            "why_title": content.ABOUT_PAGE["why_title"],
            "why": settings_obj.about_why or content.ABOUT_PAGE["why"],
            "why_detail": settings_obj.about_why_detail or content.ABOUT_PAGE["why_detail"],
            "motto": settings_obj.motto or content.ABOUT_PAGE["motto"],
            "mission": settings_obj.mission or content.ABOUT_PAGE["mission"],
            "values_intro": settings_obj.values_intro or content.ABOUT_PAGE["values_intro"],
        },
    }


def get_destinations(published_only=True):
    qs = Destination.objects.all()
    if published_only:
        qs = qs.filter(is_published=True)
    rows = list(qs)
    if rows:
        data = []
        for i, d in enumerate(rows, start=1):
            card = resolve_ms_url(
                f"uploads/destination/desti{i}.jpg",
                default=resolve_ms_url(d.image_url),
            )
            detail = resolve_ms_url(
                f"uploads/destination/destination{i}_main.jpg",
                default=resolve_ms_url(d.image_url),
            )
            data.append(
                {
                    "slug": d.slug,
                    "name": d.name,
                    "short": d.short,
                    "summary": d.summary,
                    "teaser": d.teaser,
                    "image": resolve_ms_url(d.image_url, default=card),
                    "card_image": card,
                    "detail_image": detail,
                    "banner": resolve_ms_url(d.banner_url or d.image_url, default=card),
                    "accent": d.accent,
                }
            )
        return data
    return [
        {
            **d,
            "card_image": resolve_ms_url(f"uploads/destination/desti{i}.jpg", default=d["image"]),
            "detail_image": resolve_ms_url(
                f"uploads/destination/destination{i}_main.jpg", default=d["image"]
            ),
        }
        for i, d in enumerate(content.DESTINATIONS, start=1)
    ]


def get_services(published_only=True):
    qs = Service.objects.all()
    if published_only:
        qs = qs.filter(is_published=True)
    rows = list(qs)
    if rows:
        return [
            {
                "slug": s.slug,
                "title": s.title,
                "text": s.text,
                "image": resolve_ms_url(s.image_url),
            }
            for s in rows
        ]
    return content.SERVICES


def get_testimonials(published_only=True, limit=None):
    # Use Hostinger-export testimonials (with local photo paths) for the public site.
    data = [_resolve_testimonial_row(t) for t in content.TESTIMONIALS]
    return data[:limit] if limit else data


def get_offices(published_only=True):
    qs = Office.objects.all()
    if published_only:
        qs = qs.filter(is_published=True)
    rows = list(qs)
    if rows:
        return [
            {
                "label": o.label,
                "address": o.address,
                "phone": o.phone,
                "email": o.email,
                "variant": "head" if "head office" in o.label.lower() else "branch",
            }
            for o in rows
        ]
    return content.OFFICES


def get_why_choose(published_only=True):
    qs = WhyChooseItem.objects.all()
    if published_only:
        qs = qs.filter(is_published=True)
    rows = list(qs)
    if rows:
        return [
            {
                "title": w.title,
                "text": w.text,
                "icon": resolve_ms_url(w.icon_url, default=content.WHY_CHOOSE[i]["icon"] if i < len(content.WHY_CHOOSE) else ""),
            }
            for i, w in enumerate(rows)
        ]
    return content.WHY_CHOOSE

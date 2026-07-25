"""Resolve public marketing content from the CMS database, with static fallbacks."""

from . import content
from .models import (
    Destination,
    MarketingSettings,
    Office,
    Service,
    Testimonial,
    WhyChooseItem,
)


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
        return [
            {
                "slug": d.slug,
                "name": d.name,
                "short": d.short,
                "summary": d.summary,
                "teaser": d.teaser,
                "image": d.image_url,
                "banner": d.banner_url or d.image_url,
                "accent": d.accent,
            }
            for d in rows
        ]
    return content.DESTINATIONS


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
                "image": s.image_url,
            }
            for s in rows
        ]
    return content.SERVICES


def get_testimonials(published_only=True, limit=None):
    qs = Testimonial.objects.all()
    if published_only:
        qs = qs.filter(is_published=True)
    rows = list(qs)
    if rows:
        data = [{"quote": t.quote, "name": t.name, "role": t.role} for t in rows]
        return data[:limit] if limit else data
    data = content.TESTIMONIALS
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
            {"title": w.title, "text": w.text, "icon": w.icon_url}
            for w in rows
        ]
    return content.WHY_CHOOSE

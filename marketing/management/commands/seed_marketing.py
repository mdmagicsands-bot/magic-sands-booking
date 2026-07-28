from django.core.management.base import BaseCommand

from marketing import content
from marketing.models import (
    Destination,
    MarketingSettings,
    Office,
    Service,
    Testimonial,
    WhyChooseItem,
)


class Command(BaseCommand):
    help = "Seed marketing CMS tables from static content.py defaults."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing CMS rows with static defaults.",
        )

        parser.add_argument(
            "--if-empty",
            action="store_true",
            help="Skip seeding when marketing CMS rows already exist.",
        )

    def handle(self, *args, **options):
        force = options["force"]
        if options["if_empty"] and MarketingSettings.objects.exists():
            self.stdout.write("Marketing CMS already present — skipping seed_marketing.")
            return
        created = 0

        if force or not MarketingSettings.objects.exists():
            MarketingSettings.objects.all().delete()
            MarketingSettings.objects.create(
                brand=content.BRAND,
                brand_full=content.BRAND_FULL,
                tagline=content.TAGLINE,
                hero_title=content.HERO["title"],
                hero_lede=content.HERO["lede"],
                about_blurb=content.ABOUT_BLURB,
                elevating_title=content.ELEVATING["title"],
                elevating_text=content.ELEVATING["text"],
                about_intro_title=content.ABOUT_PAGE["intro_title"],
                about_intro=content.ABOUT_PAGE["intro"],
                about_expertise=content.ABOUT_PAGE["expertise"],
                about_story=content.ABOUT_PAGE["story"],
                about_boutique=content.ABOUT_PAGE["boutique"],
                about_why=content.ABOUT_PAGE["why"],
                about_why_detail=content.ABOUT_PAGE["why_detail"],
                motto=content.ABOUT_PAGE["motto"],
                mission=content.ABOUT_PAGE["mission"],
                values_intro=content.ABOUT_PAGE["values_intro"],
            )
            created += 1

        if force or not Destination.objects.exists():
            if force:
                Destination.objects.all().delete()
            for i, d in enumerate(content.DESTINATIONS):
                Destination.objects.create(
                    slug=d["slug"],
                    name=d["name"],
                    short=d["short"],
                    summary=d["summary"],
                    teaser=d.get("teaser", ""),
                    image_url=d.get("image", ""),
                    banner_url=d.get("banner", ""),
                    accent=d.get("accent", "#1b6b74"),
                    sort_order=i,
                )
                created += 1

        if force or not Service.objects.exists():
            if force:
                Service.objects.all().delete()
            for i, s in enumerate(content.SERVICES):
                Service.objects.create(
                    slug=s["slug"],
                    title=s["title"],
                    text=s["text"],
                    image_url=s.get("image", ""),
                    sort_order=i,
                )
                created += 1

        if force or not Testimonial.objects.exists():
            if force:
                Testimonial.objects.all().delete()
            for i, t in enumerate(content.TESTIMONIALS):
                Testimonial.objects.create(
                    quote=t["quote"],
                    name=t["name"],
                    role=t.get("role", ""),
                    sort_order=i,
                )
                created += 1

        if force or not Office.objects.exists():
            if force:
                Office.objects.all().delete()
            for i, o in enumerate(content.OFFICES):
                Office.objects.create(
                    label=o["label"],
                    address=o["address"],
                    phone=o.get("phone", ""),
                    email=o.get("email", ""),
                    sort_order=i,
                )
                created += 1

        if force or not WhyChooseItem.objects.exists():
            if force:
                WhyChooseItem.objects.all().delete()
            for i, w in enumerate(content.WHY_CHOOSE):
                WhyChooseItem.objects.create(
                    title=w["title"],
                    text=w["text"],
                    icon_url=w.get("icon", ""),
                    sort_order=i,
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Marketing CMS seeded ({created} writes)."))

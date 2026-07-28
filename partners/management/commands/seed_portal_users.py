from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from guests.models import GuestProfile

User = get_user_model()

ADMIN_EMAIL = "admin@magicsandsdmc.com"
ADMIN_PASSWORD = "admin123"
PARTNER_EMAIL = "demo@magicsandsdmc.com"
PARTNER_PASSWORD = "Demo123"


class Command(BaseCommand):
    help = "Seed website admin and partner demo portal users."

    def handle(self, *args, **options):
        admin_user, created = User.objects.update_or_create(
            username=ADMIN_EMAIL,
            defaults={
                "email": ADMIN_EMAIL,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "first_name": "Magic",
                "last_name": "Admin",
            },
        )
        admin_user.set_password(ADMIN_PASSWORD)
        admin_user.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} admin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}"
            )
        )

        partner_user, created = User.objects.update_or_create(
            username=PARTNER_EMAIL,
            defaults={
                "email": PARTNER_EMAIL,
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                "first_name": "Demo",
                "last_name": "Partner",
            },
        )
        partner_user.set_password(PARTNER_PASSWORD)
        partner_user.save()
        profile, _ = GuestProfile.objects.get_or_create(user=partner_user)
        profile.credit_limit = 10000
        profile.credit_used = 46.92
        profile.credit_currency = "USD"
        profile.save(update_fields=["credit_limit", "credit_used", "credit_currency", "updated_at"])
        self.stdout.write(
            self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} partner: {PARTNER_EMAIL} / {PARTNER_PASSWORD}"
            )
        )

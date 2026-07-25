from django.contrib import admin

from .models import PartnerRegistration


@admin.register(PartnerRegistration)
class PartnerRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "contact_name",
        "email",
        "country",
        "status",
        "created_at",
    )
    list_filter = ("status", "country")
    search_fields = ("company_name", "contact_name", "email", "phone")
    readonly_fields = ("created_at",)

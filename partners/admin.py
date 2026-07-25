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
        "accepted_terms",
        "created_at",
    )
    list_filter = ("status", "country", "preferred_currency", "accepted_terms")
    search_fields = (
        "company_name",
        "contact_name",
        "email",
        "telephone",
        "mobile",
        "trade_license_number",
    )
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            "Company Information",
            {
                "fields": (
                    "company_name",
                    "trade_license_number",
                    "vat_tax_number",
                    "year_established",
                    "website",
                    "company_registration_country",
                )
            },
        ),
        (
            "Office Details",
            {
                "fields": (
                    "office_address",
                    "country",
                    "city",
                    "postal_code",
                    "telephone",
                    "whatsapp",
                )
            },
        ),
        (
            "Primary Contact",
            {"fields": ("contact_name", "designation", "email", "mobile", "phone")},
        ),
        (
            "Business Details",
            {
                "fields": (
                    "markets_served",
                    "main_destinations_sold",
                    "business_types",
                    "annual_passenger_volume",
                    "preferred_currency",
                )
            },
        ),
        (
            "Documents",
            {
                "fields": (
                    "trade_license_file",
                    "passport_id_file",
                    "vat_certificate_file",
                    "company_profile_file",
                    "logo_file",
                )
            },
        ),
        (
            "Review",
            {
                "fields": (
                    "accepted_terms",
                    "message",
                    "status",
                    "notes",
                    "created_at",
                    "reviewed_at",
                )
            },
        ),
    )

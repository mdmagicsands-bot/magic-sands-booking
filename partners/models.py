from django.db import models


def partner_upload_to(instance, filename: str) -> str:
    safe_company = "".join(ch for ch in (instance.company_name or "partner") if ch.isalnum() or ch in ("-", "_"))[:40]
    return f"partner_registrations/{safe_company or 'partner'}/{filename}"


class PartnerRegistration(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending Verification"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    # Company Information
    company_name = models.CharField(max_length=255)
    trade_license_number = models.CharField(max_length=120, blank=True)
    vat_tax_number = models.CharField(max_length=120, blank=True)
    year_established = models.PositiveIntegerField(null=True, blank=True)
    website = models.URLField(blank=True)
    company_registration_country = models.CharField(max_length=120, blank=True)

    # Office Details
    office_address = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=40, blank=True)
    telephone = models.CharField(max_length=64, blank=True)
    whatsapp = models.CharField(max_length=64, blank=True)

    # Primary Contact
    contact_name = models.CharField(max_length=255)
    designation = models.CharField(max_length=160, blank=True)
    email = models.EmailField()
    mobile = models.CharField(max_length=64, blank=True)
    phone = models.CharField(max_length=64, blank=True)  # legacy alias / fallback

    # Business Details
    markets_served = models.TextField(blank=True)
    main_destinations_sold = models.TextField(blank=True)
    business_types = models.CharField(
        max_length=120,
        blank=True,
        help_text="Comma-separated: FIT, Groups, MICE",
    )
    annual_passenger_volume = models.CharField(max_length=120, blank=True)
    preferred_currency = models.CharField(max_length=20, blank=True)

    # Documents
    trade_license_file = models.FileField(upload_to=partner_upload_to, blank=True)
    passport_id_file = models.FileField(upload_to=partner_upload_to, blank=True)
    vat_certificate_file = models.FileField(upload_to=partner_upload_to, blank=True)
    company_profile_file = models.FileField(upload_to=partner_upload_to, blank=True)
    logo_file = models.FileField(upload_to=partner_upload_to, blank=True)

    # Terms + workflow
    accepted_terms = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.company_name} ({self.email}) — {self.status}"

    @property
    def business_type_list(self):
        return [p.strip() for p in (self.business_types or "").split(",") if p.strip()]

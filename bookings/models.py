from django.conf import settings
from django.db import models


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="bookings",
    )

    # LiteAPI ids
    offer_id = models.CharField(max_length=255, blank=True)
    prebook_id = models.CharField(max_length=255, blank=True, db_index=True)
    transaction_id = models.CharField(max_length=255, blank=True)
    liteapi_booking_id = models.CharField(max_length=255, blank=True, db_index=True)
    hotel_confirmation_code = models.CharField(max_length=255, blank=True)

    hotel_id = models.CharField(max_length=64, blank=True)
    hotel_name = models.CharField(max_length=255, blank=True)
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    adults = models.PositiveSmallIntegerField(default=2)

    guest_first_name = models.CharField(max_length=100)
    guest_last_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=40, blank=True)

    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, blank=True)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.PENDING_PAYMENT
    )

    raw_prebook = models.JSONField(default=dict, blank=True)
    raw_book = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        label = self.liteapi_booking_id or self.prebook_id or self.pk
        return f"{label} — {self.guest_email} ({self.status})"

    @property
    def guest_full_name(self) -> str:
        return f"{self.guest_first_name} {self.guest_last_name}".strip()

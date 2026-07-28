from django.conf import settings
from django.db import models


class GuestProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="guest_profile",
    )
    phone = models.CharField(max_length=40, blank=True)
    nationality = models.CharField(max_length=2, blank=True, default="OM")
    preferred_currency = models.CharField(max_length=8, blank=True, default="USD")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=10000)
    credit_used = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_currency = models.CharField(max_length=8, blank=True, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.user.get_username()

    @property
    def display_name(self) -> str:
        full = self.user.get_full_name().strip()
        return full or self.user.get_username()

    @property
    def credit_available(self):
        from decimal import Decimal
        return self.credit_limit - self.credit_used

    def credit_summary(self) -> dict:
        from decimal import Decimal
        available = self.credit_limit - self.credit_used
        return {
            "limit": f"{self.credit_limit:.2f}",
            "available": f"{available:.2f}",
            "used": f"{self.credit_used:.2f}",
            "currency": self.credit_currency or "USD",
            "available_decimal": available,
        }

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

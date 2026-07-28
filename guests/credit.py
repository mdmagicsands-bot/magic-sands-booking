from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.db import transaction

from guests.models import GuestProfile


class InsufficientCreditError(Exception):
    def __init__(self, available: Decimal, required: Decimal, currency: str = "USD"):
        self.available = available
        self.required = required
        self.currency = currency
        super().__init__(
            f"Insufficient credit. Available {currency} {available:.2f}, "
            f"required {currency} {required:.2f}."
        )


def _to_decimal(value) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def get_partner_profile(user) -> GuestProfile | None:
    if not user.is_authenticated or user.is_staff:
        return None
    profile, _ = GuestProfile.objects.get_or_create(user=user)
    return profile


def credit_summary_for_user(user) -> dict:
    profile = get_partner_profile(user)
    if profile is None:
        return {
            "limit": "0.00",
            "available": "0.00",
            "used": "0.00",
            "currency": "USD",
            "available_decimal": Decimal("0"),
        }
    return profile.credit_summary()


def can_charge_credit(user, amount, currency: str = "USD") -> tuple[bool, str]:
    profile = get_partner_profile(user)
    if profile is None:
        return False, "Partner account required."
    required = _to_decimal(amount)
    if required is None or required <= 0:
        return False, "Invalid booking amount."
    acct_currency = profile.credit_currency or "USD"
    if currency and currency.upper() != acct_currency.upper():
        return False, f"Booking currency {currency} does not match credit account ({acct_currency})."
    available = profile.credit_available
    if required > available:
        return False, (
            f"Insufficient credit. Available {acct_currency} {available:.2f}, "
            f"required {acct_currency} {required:.2f}."
        )
    return True, ""


@transaction.atomic
def charge_partner_credit(user, amount, currency: str = "USD") -> GuestProfile:
    profile = GuestProfile.objects.select_for_update().get(user=user)
    required = _to_decimal(amount)
    if required is None or required <= 0:
        raise InsufficientCreditError(profile.credit_available, Decimal("0"), currency)
    acct_currency = profile.credit_currency or "USD"
    if currency and currency.upper() != acct_currency.upper():
        raise InsufficientCreditError(profile.credit_available, required, acct_currency)
    available = profile.credit_limit - profile.credit_used
    if required > available:
        raise InsufficientCreditError(available, required, acct_currency)
    profile.credit_used += required
    profile.save(update_fields=["credit_used", "updated_at"])
    return profile


@transaction.atomic
def refund_partner_credit(user, amount, currency: str = "USD") -> GuestProfile | None:
    profile = get_partner_profile(user)
    if profile is None:
        return None
    profile = GuestProfile.objects.select_for_update().get(pk=profile.pk)
    required = _to_decimal(amount)
    if required is None or required <= 0:
        return profile
    profile.credit_used = max(Decimal("0"), profile.credit_used - required)
    profile.save(update_fields=["credit_used", "updated_at"])
    return profile

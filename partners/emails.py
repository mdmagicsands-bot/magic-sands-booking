"""Partner registration emails — kept in sync with booking platform helpers."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import NoReverseMatch, reverse

logger = logging.getLogger(__name__)


def _split_emails(raw: str) -> list[str]:
    return [e.strip() for e in (raw or "").split(",") if e.strip() and "@" in e.strip()]


def _notify_to() -> list[str]:
    raw = getattr(settings, "PARTNER_REGISTRATION_NOTIFY_EMAIL", "") or ""
    emails = _split_emails(raw)
    return emails or ["support@magicsandsdmc.com"]


def _notify_cc() -> list[str]:
    raw = getattr(settings, "PARTNER_REGISTRATION_NOTIFY_CC", "") or ""
    to_set = {e.lower() for e in _notify_to()}
    return [e for e in _split_emails(raw) if e.lower() not in to_set]


def _public_booking_base() -> str:
    return (getattr(settings, "PUBLIC_BOOKING_URL", "") or "http://127.0.0.1:8002").rstrip(
        "/"
    )


def _from_email() -> str:
    return getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@magicsandsdmc.com"


def send_partner_registration_emails(registration) -> dict:
    """
    Fallback if a registration is still saved on marketing.
    Primary path posts to booking and uses booking partners.emails.
    """
    result = {"admin": False, "applicant": False, "skipped": False}
    if not getattr(settings, "PARTNER_REGISTRATION_EMAILS_ENABLED", True):
        result["skipped"] = True
        return result

    company = registration.company_name
    contact = registration.contact_name
    email = registration.email
    from_email = _from_email()
    try:
        detail_path = reverse("partner_request_detail", args=[registration.pk])
        detail_url = f"{_public_booking_base()}{detail_path}"
    except NoReverseMatch:
        detail_url = f"{_public_booking_base()}/admin/partners/{registration.pk}/"

    partner_name = contact or "Partner"
    applicant_subject = "Welcome to Magic Sands DMC – Registration Received"
    applicant_text = (
        f"Dear {partner_name},\n\n"
        f"Thank you for registering with Magic Sands DMC.\n\n"
        f"We have successfully received your partner registration and our team is "
        f"currently reviewing your application. Once the verification process is "
        f"complete, you will receive another email confirming your account activation "
        f"and access to our B2B Booking Portal.\n\n"
        f"We appreciate your interest in partnering with us and look forward to "
        f"building a successful business relationship.\n\n"
        f"If you have any questions, please feel free to contact us at "
        f"support@magicsandsdmc.com.\n\n"
        f"Warm regards,\n\n"
        f"Partner Relations Team\n"
        f"Magic Sands DMC\n"
        f"Your Guide to Arabia\n"
        f"www.magicsandsdmc.com\n"
    )
    applicant_html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.6;color:#0f172a;max-width:560px">
      <p style="margin:0 0 14px">Dear {partner_name},</p>
      <p style="margin:0 0 14px">Thank you for registering with Magic Sands DMC.</p>
      <p style="margin:0 0 14px">
        We have successfully received your partner registration and our team is
        currently reviewing your application. Once the verification process is
        complete, you will receive another email confirming your account activation
        and access to our B2B Booking Portal.
      </p>
      <p style="margin:0 0 14px">
        We appreciate your interest in partnering with us and look forward to
        building a successful business relationship.
      </p>
      <p style="margin:0 0 18px">
        If you have any questions, please feel free to contact us at
        <a href="mailto:support@magicsandsdmc.com" style="color:#00667f">support@magicsandsdmc.com</a>.
      </p>
      <p style="margin:0 0 2px">Warm regards,</p>
      <p style="margin:12px 0 0">
        <strong>Partner Relations Team</strong><br>
        Magic Sands DMC<br>
        <em>Your Guide to Arabia</em><br>
        <a href="https://www.magicsandsdmc.com" style="color:#00667f">www.magicsandsdmc.com</a>
      </p>
    </div>
    """
    try:
        msg = EmailMultiAlternatives(
            applicant_subject,
            applicant_text,
            from_email,
            [email],
            reply_to=["support@magicsandsdmc.com"],
        )
        msg.attach_alternative(applicant_html, "text/html")
        msg.send(fail_silently=False)
        result["applicant"] = True
    except Exception:
        logger.exception("Failed to send partner registration thank-you email")

    to_list = _notify_to()
    cc_list = _notify_cc()
    admin_subject = f"New Partner Registration — {company}"
    admin_text = (
        f"New Partner Registration\n\n"
        f"Company: {company}\n"
        f"Status: Pending Verification\n"
        f"Contact: {contact}\n"
        f"Email: {email}\n"
        f"Mobile: {registration.mobile or registration.telephone or '—'}\n"
        f"Country: {registration.country or registration.company_registration_country or '—'}\n\n"
        f"Review:\n{detail_url}\n"
    )
    try:
        msg = EmailMultiAlternatives(
            admin_subject,
            admin_text,
            from_email,
            to_list,
            cc=cc_list or None,
        )
        msg.send(fail_silently=False)
        result["admin"] = True
    except Exception:
        logger.exception("Failed to send partner registration support notification")

    return result

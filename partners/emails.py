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

    applicant_subject = "Thank you — Magic Sands partner application received"
    applicant_text = (
        f"Dear {contact},\n\n"
        f"Thank you for registering with Magic Sands DMC.\n\n"
        f"We have received your partner application for {company}.\n"
        f"Status: Pending Verification\n\n"
        f"Our partnerships team will review your documents and contact you shortly.\n\n"
        f"Kind regards,\n"
        f"Magic Sands DMC\n"
    )
    applicant_html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.55;color:#0f172a;max-width:560px">
      <h2 style="margin:0 0 12px">Thank you for your application</h2>
      <p style="margin:0 0 10px">Dear {contact},</p>
      <p style="margin:0 0 10px">
        Thank you for registering with Magic Sands DMC. We have received your partner
        application for <strong>{company}</strong>.
      </p>
      <p style="margin:0 0 14px;color:#b45309"><strong>Status: Pending Verification</strong></p>
      <p style="margin:0">Our partnerships team will review your documents and contact you shortly.</p>
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

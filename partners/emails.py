"""Partner registration email helpers — SMTP is configured later via env."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse

logger = logging.getLogger(__name__)


def _admin_inbox() -> list[str]:
    raw = getattr(settings, "PARTNER_REGISTRATION_NOTIFY_EMAIL", "") or ""
    emails = [e.strip() for e in raw.split(",") if e.strip()]
    if emails:
        return emails
    fallback = getattr(settings, "DEFAULT_FROM_EMAIL", "") or ""
    return [fallback] if fallback and "@" in fallback else []


def _public_booking_base() -> str:
    return (getattr(settings, "PUBLIC_BOOKING_URL", "") or "http://127.0.0.1:8001").rstrip(
        "/"
    )


def send_partner_registration_emails(registration) -> dict:
    """
    Generate/send emails for a new partner registration.

    Returns a small status dict. Failures are logged and never block the submit flow.
    Configure later with EMAIL_HOST / PARTNER_REGISTRATION_NOTIFY_EMAIL.
    """
    result = {"admin": False, "applicant": False, "skipped": False}
    if not getattr(settings, "PARTNER_REGISTRATION_EMAILS_ENABLED", True):
        result["skipped"] = True
        return result

    company = registration.company_name
    contact = registration.contact_name
    email = registration.email
    detail_path = reverse("partner_request_detail", args=[registration.pk])
    detail_url = f"{_public_booking_base()}{detail_path}"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@magicsandsdmc.com")

    admin_recipients = _admin_inbox()
    admin_subject = f"New Partner Registration — {company}"
    admin_text = (
        f"New Partner Registration\n\n"
        f"Company: {company}\n"
        f"Status: Pending Verification\n"
        f"Contact: {contact}\n"
        f"Email: {email}\n"
        f"Mobile: {registration.mobile or registration.telephone or '—'}\n"
        f"Country: {registration.country or registration.company_registration_country or '—'}\n\n"
        f"Review in admin:\n{detail_url}\n"
    )
    admin_html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#12262b">
      <p style="font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#1b6b74;margin:0 0 8px">
        Step 2 · Admin notification
      </p>
      <h2 style="margin:0 0 8px">New Partner Registration</h2>
      <p style="font-size:20px;margin:0 0 6px"><strong>{company}</strong></p>
      <p style="margin:0 0 16px;color:#b45309"><strong>Pending Verification</strong></p>
      <p style="margin:0 0 4px">Contact: {contact}</p>
      <p style="margin:0 0 4px">Email: {email}</p>
      <p style="margin:0 0 16px">Mobile: {registration.mobile or registration.telephone or "—"}</p>
      <p><a href="{detail_url}">Open application in admin</a></p>
    </div>
    """

    try:
        if admin_recipients:
            msg = EmailMultiAlternatives(
                admin_subject, admin_text, from_email, admin_recipients
            )
            msg.attach_alternative(admin_html, "text/html")
            msg.send(fail_silently=False)
            result["admin"] = True
        else:
            # Still "generate" the email via Django mail backend (console/file) for later wiring.
            msg = EmailMultiAlternatives(
                admin_subject,
                admin_text
                + "\n\n[No PARTNER_REGISTRATION_NOTIFY_EMAIL configured — message generated for later SMTP setup.]\n",
                from_email,
                [from_email],
            )
            msg.attach_alternative(admin_html, "text/html")
            msg.send(fail_silently=True)
            result["admin"] = True
            logger.info(
                "Partner registration admin email generated without notify inbox configured."
            )
    except Exception:
        logger.exception("Failed to send partner registration admin email")

    applicant_subject = "We received your Magic Sands partner application"
    applicant_text = (
        f"Dear {contact},\n\n"
        f"Thank you for submitting a partner registration for {company}.\n"
        f"Status: Pending Verification\n\n"
        f"Our partnerships team will review your documents and contact you shortly.\n\n"
        f"Magic Sands DMC\n"
    )
    applicant_html = f"""
    <div style="font-family:Arial,sans-serif;line-height:1.5;color:#12262b">
      <h2 style="margin:0 0 8px">Partner Registration received</h2>
      <p style="margin:0 0 8px">Dear {contact},</p>
      <p style="margin:0 0 8px">
        Thank you for submitting a partner registration for <strong>{company}</strong>.
      </p>
      <p style="margin:0 0 16px;color:#b45309"><strong>Status: Pending Verification</strong></p>
      <p style="margin:0">Our partnerships team will review your application and contact you shortly.</p>
    </div>
    """
    try:
        msg = EmailMultiAlternatives(
            applicant_subject, applicant_text, from_email, [email]
        )
        msg.attach_alternative(applicant_html, "text/html")
        msg.send(fail_silently=False)
        result["applicant"] = True
    except Exception:
        logger.exception("Failed to send partner registration applicant email")

    return result

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from guests.credit import (
    InsufficientCreditError,
    can_charge_credit,
    charge_partner_credit,
    credit_summary_for_user,
    get_partner_profile,
    refund_partner_credit,
)
from hotels.liteapi import LiteAPIError, get_client

from .models import Booking
from .voucher import build_demo_book_response, build_voucher_context


def _parse_booking_date(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _format_stay_date(value) -> str:
    if not value:
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%a, %d %b %Y")
    return str(value)


def _hotel_detail_url(booking: Booking, portal: str) -> str:
    name = "guest_hotel_detail" if portal == "partner" else "hotel_detail"
    return (
        reverse(name, args=[booking.hotel_id])
        + f"?checkin={booking.check_in or ''}&checkout={booking.check_out or ''}"
        + f"&adults={booking.adults}"
    )


def _rate_session_key(booking_id: int) -> str:
    return f"booking_rate_{booking_id}"


def _store_rate_snapshot(request, booking_id: int, data: dict) -> None:
    request.session[_rate_session_key(booking_id)] = data
    request.session.modified = True


def _get_rate_snapshot(request, booking_id: int) -> dict:
    return request.session.get(_rate_session_key(booking_id)) or {}


def _apply_prebook(booking: Booking, prebook: dict) -> None:
    booking.prebook_id = prebook.get("prebookId") or ""
    booking.transaction_id = prebook.get("transactionId") or ""
    booking.raw_prebook = prebook
    amount = prebook.get("price")
    try:
        booking.amount = Decimal(str(amount)) if amount is not None else None
    except (InvalidOperation, TypeError):
        booking.amount = None
    booking.currency = prebook.get("currency") or booking.currency or "USD"
    if not booking.hotel_id:
        booking.hotel_id = prebook.get("hotelId") or ""
    booking.save()


def _guest_defaults(request) -> dict:
    if request.user.is_authenticated and not request.user.is_staff:
        profile = getattr(request.user, "guest_profile", None)
        return {
            "first_name": request.user.first_name,
            "last_name": request.user.last_name,
            "email": request.user.email,
            "phone": getattr(profile, "phone", "") if profile else "",
        }
    return {}


def _is_partner_booking(request, booking: Booking) -> bool:
    rate = _get_rate_snapshot(request, booking.pk)
    return rate.get("portal") == "partner"


def _booking_guest_payload(booking: Booking, request) -> tuple[dict, list]:
    guest = request.session.get("guest") or {
        "first_name": booking.guest_first_name,
        "last_name": booking.guest_last_name,
        "email": booking.guest_email,
    }
    rate = _get_rate_snapshot(request, booking.pk)
    remarks = rate.get("special_requests") or ""
    holder = {
        "firstName": guest["first_name"],
        "lastName": guest["last_name"],
        "email": guest["email"],
    }
    guests = [
        {
            "occupancyNumber": 1,
            "firstName": guest["first_name"],
            "lastName": guest["last_name"],
            "email": guest["email"],
            "remarks": remarks,
        }
    ]
    return holder, guests


def _apply_book_result(booking: Booking, result: dict) -> None:
    booking.raw_book = result
    booking.liteapi_booking_id = result.get("bookingId") or ""
    booking.hotel_confirmation_code = result.get("hotelConfirmationCode") or ""
    booking.status = Booking.Status.CONFIRMED
    hotel = result.get("hotel") or {}
    if hotel.get("name"):
        booking.hotel_name = hotel["name"]
    if hotel.get("hotelId"):
        booking.hotel_id = hotel["hotelId"]
    if result.get("price") is not None:
        try:
            booking.amount = Decimal(str(result["price"]))
        except (InvalidOperation, TypeError):
            pass
    if result.get("currency"):
        booking.currency = result["currency"]
    booking.save()


def _finalize_partner_credit_booking(request, booking: Booking) -> Booking:
    if booking.status == Booking.Status.CONFIRMED and booking.liteapi_booking_id:
        return booking
    if booking.credit_charged:
        raise LiteAPIError("Credit already charged for this booking.")

    rate = _get_rate_snapshot(request, booking.pk)
    ok, reason = can_charge_credit(
        booking.user,
        booking.amount,
        booking.currency or "USD",
    )
    if not ok:
        raise InsufficientCreditError(Decimal("0"), booking.amount or Decimal("0"), booking.currency)

    holder, guests = _booking_guest_payload(booking, request)
    client = get_client()
    result = None
    api_error = None

    try:
        result = client.book_on_credit(
            prebook_id=booking.prebook_id,
            holder=holder,
            guests=guests,
        )
    except LiteAPIError as exc:
        api_error = exc
        if settings.DEBUG:
            result = build_demo_book_response(booking, rate)
        else:
            raise

    with transaction.atomic():
        charge_partner_credit(booking.user, booking.amount, booking.currency or "USD")
        booking.payment_method = "credit"
        booking.credit_charged = True
        _apply_book_result(booking, result)
        if api_error and settings.DEBUG:
            booking.error_message = f"Demo voucher (API credit unavailable): {api_error}"

    return booking


def _wizard_context(request, booking: Booking, step: int) -> dict:
    rate = _get_rate_snapshot(request, booking.pk)
    cancel_policies = rate.get("cancel_policies") or []
    if isinstance(cancel_policies, str):
        try:
            cancel_policies = json.loads(cancel_policies)
        except json.JSONDecodeError:
            cancel_policies = []
    prebook = booking.raw_prebook or {}
    amount = booking.amount
    if amount is None and prebook.get("price") is not None:
        try:
            amount = Decimal(str(prebook["price"]))
        except (InvalidOperation, TypeError):
            amount = None
    currency = booking.currency or prebook.get("currency") or rate.get("currency") or "USD"
    is_partner = rate.get("portal") == "partner"
    credit_ok = False
    credit_message = ""
    partner_credit = credit_summary_for_user(request.user) if is_partner else None
    if is_partner and request.user.is_authenticated:
        credit_ok, credit_message = can_charge_credit(request.user, amount, currency)
    return {
        "booking": booking,
        "step": step,
        "rate": rate,
        "cancel_policies": cancel_policies,
        "hotel_name": booking.hotel_name or rate.get("hotel_name") or booking.hotel_id,
        "hotel_photo": rate.get("hotel_photo") or "",
        "hotel_stars": rate.get("hotel_stars") or 0,
        "hotel_address": rate.get("hotel_address") or "",
        "room_name": rate.get("room_name") or "Room",
        "board": rate.get("board") or "Room Only",
        "board_type": rate.get("board_type") or "",
        "refundable_label": rate.get("refundable_label") or "",
        "is_refundable": bool(rate.get("is_refundable")),
        "amount": amount,
        "currency": currency,
        "checkin": booking.check_in,
        "checkout": booking.check_out,
        "checkin_display": _format_stay_date(booking.check_in),
        "checkout_display": _format_stay_date(booking.check_out),
        "nights": rate.get("nights") or 1,
        "adults": booking.adults,
        "occupancy_label": rate.get("occupancy_label") or f"{booking.adults} Adult(s)",
        "rooms_count": rate.get("rooms_count") or 1,
        "hotel_remarks": rate.get("hotel_remarks") or "",
        "guest_defaults": _guest_defaults(request),
        "is_partner": is_partner,
        "partner_credit": partner_credit,
        "credit_ok": credit_ok,
        "credit_message": credit_message,
        "public_key": settings.LITEAPI_PUBLIC_KEY,
        "secret_key": (booking.raw_prebook or {}).get("secretKey") or "",
        "return_url": request.build_absolute_uri(
            reverse("payment_return")
            + f"?prebookId={booking.prebook_id}&transactionId={booking.transaction_id}"
            + f"&booking={booking.pk}"
        ),
    }


@require_POST
def prebook_check(request):
    """Hold the selected rate via LiteAPI prebook before entering the booking wizard."""
    offer_id = (request.POST.get("offer_id") or "").strip()
    if not offer_id:
        return JsonResponse({"ok": False, "error": "Missing offer."}, status=400)

    portal = request.POST.get("portal") or "public"
    is_partner = portal == "partner"
    if is_partner and (not request.user.is_authenticated or request.user.is_staff):
        return JsonResponse({"ok": False, "error": "Partner login required."}, status=403)

    hotel_id = (request.POST.get("hotel_id") or "").strip()
    hotel_name = (request.POST.get("hotel_name") or "").strip()
    checkin = request.POST.get("checkin") or ""
    checkout = request.POST.get("checkout") or ""
    adults = int(request.POST.get("adults") or 2)

    try:
        client = get_client()
        prebook = client.prebook(offer_id, use_payment_sdk=not is_partner)
    except LiteAPIError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    amount = prebook.get("price")
    currency = prebook.get("currency") or request.POST.get("currency") or "USD"
    if is_partner:
        ok, reason = can_charge_credit(request.user, amount, currency)
        if not ok:
            return JsonResponse({"ok": False, "error": reason}, status=400)

    booking = Booking.objects.create(
        user=request.user if request.user.is_authenticated and not request.user.is_staff else None,
        offer_id=offer_id,
        hotel_id=hotel_id,
        hotel_name=hotel_name,
        check_in=_parse_booking_date(checkin),
        check_out=_parse_booking_date(checkout),
        adults=adults,
        guest_first_name="Pending",
        guest_last_name="Guest",
        guest_email="pending@booking.local",
        status=Booking.Status.PENDING_PAYMENT,
    )
    _apply_prebook(booking, prebook)

    cancel_raw = request.POST.get("cancel_policies") or "[]"
    try:
        cancel_policies = json.loads(cancel_raw)
    except json.JSONDecodeError:
        cancel_policies = []

    _store_rate_snapshot(
        request,
        booking.pk,
        {
            "portal": portal,
            "room_name": request.POST.get("room_name") or "",
            "board": request.POST.get("board") or "",
            "board_type": request.POST.get("board_type") or "",
            "refundable_label": request.POST.get("refundable_label") or "",
            "is_refundable": request.POST.get("is_refundable") == "1",
            "currency": currency,
            "hotel_photo": request.POST.get("hotel_photo") or "",
            "hotel_stars": int(request.POST.get("hotel_stars") or 0),
            "hotel_address": request.POST.get("hotel_address") or "",
            "occupancy_label": request.POST.get("occupancy_label") or "",
            "rooms_count": int(request.POST.get("rooms_count") or 1),
            "nights": int(request.POST.get("nights") or 1),
            "hotel_remarks": request.POST.get("hotel_remarks") or "",
            "cancel_policies": cancel_policies,
            "nationality": request.POST.get("nationality") or "",
        },
    )
    request.session["pending_booking_id"] = booking.pk

    return JsonResponse(
        {
            "ok": True,
            "booking_id": booking.pk,
            "redirect": reverse("booking_wizard", args=[booking.pk]),
        }
    )


@require_http_methods(["GET", "POST"])
def booking_wizard(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id)
    if not booking.prebook_id:
        messages.error(request, "This booking session expired. Please select a room again.")
        rate = _get_rate_snapshot(request, booking.pk)
        portal = rate.get("portal") or "public"
        if booking.hotel_id:
            return redirect(_hotel_detail_url(booking, portal))
        return redirect("book_home")

    step = int(request.GET.get("step") or request.POST.get("step") or 1)
    step = max(1, min(3, step))
    ctx = _wizard_context(request, booking, step)
    template = "bookings/wizard.html" if ctx["is_partner"] else "bookings/wizard_public.html"

    if request.method == "POST":
        action = (request.POST.get("action") or "next").strip()
        if step == 1:
            first_name = (request.POST.get("first_name") or "").strip()
            last_name = (request.POST.get("last_name") or "").strip()
            email = (request.POST.get("email") or "").strip()
            phone = (request.POST.get("phone") or "").strip()
            special_requests = (request.POST.get("special_requests") or "").strip()
            if not all([first_name, last_name, email]):
                messages.error(request, "Please complete all required guest details.")
                return render(request, template, ctx)
            booking.guest_first_name = first_name
            booking.guest_last_name = last_name
            booking.guest_email = email
            booking.guest_phone = phone
            booking.save(
                update_fields=[
                    "guest_first_name",
                    "guest_last_name",
                    "guest_email",
                    "guest_phone",
                    "updated_at",
                ]
            )
            rate = _get_rate_snapshot(request, booking.pk)
            rate["special_requests"] = special_requests
            _store_rate_snapshot(request, booking.pk, rate)
            request.session["guest"] = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
            }
            if action == "back":
                rate = _get_rate_snapshot(request, booking.pk)
                portal = rate.get("portal") or "public"
                if booking.hotel_id:
                    return redirect(_hotel_detail_url(booking, portal))
                return redirect("book_home")
            return redirect(reverse("booking_wizard", args=[booking.pk]) + "?step=2")

        if step == 2:
            if action == "back":
                return redirect(reverse("booking_wizard", args=[booking.pk]) + "?step=1")
            if ctx["is_partner"] and not ctx["credit_ok"]:
                messages.error(request, ctx["credit_message"] or "Insufficient credit for this booking.")
                return render(request, template, ctx)
            return redirect(reverse("booking_wizard", args=[booking.pk]) + "?step=3")

        if step == 3 and ctx["is_partner"] and action == "pay_credit":
            return partner_credit_pay(request, booking_id)

    if step == 3 and ctx["is_partner"] and not ctx["credit_ok"]:
        messages.error(request, ctx["credit_message"] or "Insufficient credit to complete this booking.")

    return render(request, template, ctx)


@require_POST
def partner_credit_pay(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id)
    if not _is_partner_booking(request, booking):
        messages.error(request, "Credit payment is only available for partner bookings.")
        return redirect("booking_wizard", booking_id=booking.pk)

    if not booking.user_id or booking.user_id != request.user.id:
        messages.error(request, "You can only pay for your own booking session.")
        return redirect("guest_search")

    if booking.status == Booking.Status.CONFIRMED:
        return redirect("booking_voucher", booking_id=booking.pk)

    try:
        _finalize_partner_credit_booking(request, booking)
    except InsufficientCreditError as exc:
        messages.error(request, str(exc))
        return redirect(reverse("booking_wizard", args=[booking.pk]) + "?step=3")
    except LiteAPIError as exc:
        booking.status = Booking.Status.FAILED
        booking.error_message = str(exc)
        booking.save(update_fields=["status", "error_message", "updated_at"])
        messages.error(request, f"Booking failed: {exc}")
        return render(
            request,
            "bookings/failed.html",
            {"booking": booking, "error": str(exc), "is_partner": True},
        )

    request.session.pop("pending_booking_id", None)
    messages.success(request, "Booking confirmed. Your voucher is ready.")
    return redirect("booking_voucher", booking_id=booking.pk)


@require_http_methods(["GET", "POST"])
def checkout(request):
    """Legacy checkout — redirect to wizard when possible."""
    if request.method == "GET":
        offer_id = (request.GET.get("offer_id") or "").strip()
        if not offer_id:
            messages.error(request, "Select a room rate to continue.")
            return redirect("book_home")
        pending = request.session.get("pending_booking_id")
        if pending:
            existing = Booking.objects.filter(pk=pending, offer_id=offer_id).first()
            if existing and existing.prebook_id:
                return redirect("booking_wizard", booking_id=existing.pk)
        guest_defaults = _guest_defaults(request)
        return render(
            request,
            "bookings/checkout.html",
            {
                "offer_id": offer_id,
                "hotel_id": (request.GET.get("hotel_id") or "").strip(),
                "hotel_name": (request.GET.get("hotel_name") or "").strip(),
                "checkin": request.GET.get("checkin") or "",
                "checkout": request.GET.get("checkout") or "",
                "adults": int(request.GET.get("adults") or 2),
                "guest_defaults": guest_defaults,
            },
        )

    offer_id = (request.POST.get("offer_id") or "").strip()
    hotel_id = (request.POST.get("hotel_id") or "").strip()
    hotel_name = (request.POST.get("hotel_name") or "").strip()
    checkin = request.POST.get("checkin") or None
    checkout_date = request.POST.get("checkout") or None
    adults = int(request.POST.get("adults") or 2)
    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()

    if not all([offer_id, first_name, last_name, email]):
        messages.error(request, "Please complete guest details.")
        return redirect(request.get_full_path())

    booking = Booking.objects.create(
        user=request.user if request.user.is_authenticated and not request.user.is_staff else None,
        offer_id=offer_id,
        hotel_id=hotel_id,
        hotel_name=hotel_name,
        check_in=_parse_booking_date(checkin or ""),
        check_out=_parse_booking_date(checkout_date or ""),
        adults=adults,
        guest_first_name=first_name,
        guest_last_name=last_name,
        guest_email=email,
        guest_phone=phone,
        status=Booking.Status.PENDING_PAYMENT,
    )

    try:
        client = get_client()
        prebook = client.prebook(offer_id)
    except LiteAPIError as exc:
        booking.status = Booking.Status.FAILED
        booking.error_message = str(exc)
        booking.save(update_fields=["status", "error_message", "updated_at"])
        messages.error(request, f"Could not hold this rate: {exc}")
        if hotel_id:
            return redirect(
                reverse("hotel_detail", args=[hotel_id])
                + f"?checkin={checkin or ''}&checkout={checkout_date or ''}&adults={adults}"
            )
        return redirect("book_home")

    _apply_prebook(booking, prebook)
    request.session["pending_booking_id"] = booking.pk
    request.session["guest"] = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
    }
    return redirect(reverse("booking_wizard", args=[booking.pk]) + "?step=3")


@require_GET
def payment_return(request):
    """After LiteAPI Payment SDK redirect — confirm the booking."""
    prebook_id = (request.GET.get("prebookId") or "").strip()
    transaction_id = (request.GET.get("transactionId") or "").strip()
    booking_pk = request.GET.get("booking")

    booking = None
    if booking_pk:
        booking = Booking.objects.filter(pk=booking_pk).first()
    if booking is None and prebook_id:
        booking = Booking.objects.filter(prebook_id=prebook_id).first()
    if booking is None:
        messages.error(request, "Booking session not found.")
        return redirect("book_home")

    if booking.status == Booking.Status.CONFIRMED and booking.liteapi_booking_id:
        return redirect("booking_voucher", booking_id=booking.pk)

    holder, guests = _booking_guest_payload(booking, request)
    prebook_id = prebook_id or booking.prebook_id
    transaction_id = transaction_id or booking.transaction_id

    try:
        client = get_client()
        result = client.book(
            prebook_id=prebook_id,
            transaction_id=transaction_id,
            holder=holder,
            guests=guests,
        )
    except LiteAPIError as exc:
        booking.status = Booking.Status.FAILED
        booking.error_message = str(exc)
        booking.save(update_fields=["status", "error_message", "updated_at"])
        messages.error(request, f"Booking failed: {exc}")
        return render(request, "bookings/failed.html", {"booking": booking, "error": str(exc)})

    booking.payment_method = "card"
    _apply_book_result(booking, result)
    request.session.pop("pending_booking_id", None)
    return redirect("booking_voucher", booking_id=booking.pk)


@require_GET
def confirmation(request, booking_id: int):
    return redirect("booking_voucher", booking_id=booking_id)


@require_GET
def booking_voucher(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id)
    if booking.status != Booking.Status.CONFIRMED:
        messages.error(request, "Voucher is available only for confirmed bookings.")
        return redirect("book_home")

    rate = request.session.get(_rate_session_key(booking_id)) or {}
    voucher = build_voucher_context(booking, rate)
    voucher["raw_book_json"] = json.dumps(voucher.get("raw_book") or {}, indent=2, default=str)
    is_partner = bool(rate.get("portal") == "partner" or booking.payment_method == "credit")
    template = "bookings/voucher_partner.html" if is_partner else "bookings/voucher.html"
    return render(request, template, {"voucher": voucher, "booking": booking})

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from hotels.liteapi import LiteAPIError, get_client

from .models import Booking


@require_http_methods(["GET", "POST"])
def checkout(request):
    if request.method == "GET":
        offer_id = (request.GET.get("offer_id") or "").strip()
        hotel_id = (request.GET.get("hotel_id") or "").strip()
        hotel_name = (request.GET.get("hotel_name") or "").strip()
        checkin = request.GET.get("checkin") or ""
        checkout_date = request.GET.get("checkout") or ""
        adults = int(request.GET.get("adults") or 2)
        if not offer_id:
            messages.error(request, "Select a room rate to continue.")
            return redirect("book_home")
        return render(
            request,
            "bookings/checkout.html",
            {
                "offer_id": offer_id,
                "hotel_id": hotel_id,
                "hotel_name": hotel_name,
                "checkin": checkin,
                "checkout": checkout_date,
                "adults": adults,
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
        offer_id=offer_id,
        hotel_id=hotel_id,
        hotel_name=hotel_name,
        check_in=checkin or None,
        check_out=checkout_date or None,
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

    booking.prebook_id = prebook.get("prebookId") or ""
    booking.transaction_id = prebook.get("transactionId") or ""
    booking.raw_prebook = prebook
    amount = prebook.get("price")
    try:
        booking.amount = Decimal(str(amount)) if amount is not None else None
    except (InvalidOperation, TypeError):
        booking.amount = None
    booking.currency = prebook.get("currency") or ""
    if not booking.hotel_id:
        booking.hotel_id = prebook.get("hotelId") or ""
    booking.save()

    request.session["pending_booking_id"] = booking.pk
    request.session["guest"] = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
    }

    return_url = request.build_absolute_uri(
        reverse("payment_return")
        + f"?prebookId={booking.prebook_id}&transactionId={booking.transaction_id}"
        f"&booking={booking.pk}"
    )

    return render(
        request,
        "bookings/payment.html",
        {
            "booking": booking,
            "secret_key": prebook.get("secretKey") or "",
            "public_key": settings.LITEAPI_PUBLIC_KEY,
            "return_url": return_url,
        },
    )


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
        return redirect("confirmation", booking_id=booking.pk)

    guest = request.session.get("guest") or {
        "first_name": booking.guest_first_name,
        "last_name": booking.guest_last_name,
        "email": booking.guest_email,
    }
    prebook_id = prebook_id or booking.prebook_id
    transaction_id = transaction_id or booking.transaction_id

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
        }
    ]

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

    request.session.pop("pending_booking_id", None)
    return redirect("confirmation", booking_id=booking.pk)


@require_GET
def confirmation(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id)
    return render(request, "bookings/confirmation.html", {"booking": booking})

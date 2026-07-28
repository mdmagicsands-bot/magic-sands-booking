"""Build voucher display context from LiteAPI book() response."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation


def _fmt_date(value: str) -> str:
    if not value:
        return "—"
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(value[:19], fmt[: len(value)] if len(value) < 19 else fmt).strftime(
                "%a, %d %b %Y"
            )
        except (TypeError, ValueError):
            continue
    return str(value)


def _money(amount, currency: str = "") -> str:
    if amount is None:
        return "—"
    try:
        val = Decimal(str(amount))
    except (InvalidOperation, TypeError):
        return str(amount)
    prefix = f"{currency} " if currency else ""
    return f"{prefix}{val:,.2f}"


def build_voucher_context(booking, rate_snapshot: dict | None = None) -> dict:
    """Normalize LiteAPI confirmation payload for voucher templates."""
    raw = booking.raw_book or {}
    rate = rate_snapshot or {}
    hotel = raw.get("hotel") or {}
    if isinstance(hotel, list):
        hotel = hotel[0] if hotel else {}
    cancel = raw.get("cancellationPolicies") or raw.get("cancellationPolicy") or {}
    if isinstance(cancel, list) and cancel:
        cancel = cancel[0]

    booked_rooms = raw.get("bookedRooms") or raw.get("roomTypes") or []
    rooms: list[dict] = []
    for idx, room in enumerate(booked_rooms, start=1):
        if not isinstance(room, dict):
            continue
        rt = room.get("roomType") or room.get("rate") or room
        name = (
            rt.get("name")
            or room.get("roomName")
            or room.get("name")
            or rate.get("room_name")
            or f"Room {idx}"
        )
        board = (
            rt.get("boardName")
            or rt.get("boardType")
            or room.get("boardName")
            or rate.get("board")
            or "Room Only"
        )
        adults = room.get("adults") or booking.adults
        children = room.get("children") or 0
        rate_block = room.get("rate") or rt
        retail = (rate_block.get("retailRate") or {}) if isinstance(rate_block, dict) else {}
        totals = retail.get("total") or [{}]
        room_amount = totals[0].get("amount") if totals else None
        room_currency = totals[0].get("currency") if totals else booking.currency
        rooms.append(
            {
                "number": idx,
                "name": name,
                "board": board,
                "adults": adults,
                "children": children,
                "amount": _money(room_amount, room_currency or booking.currency),
            }
        )

    if not rooms:
        rooms.append(
            {
                "number": 1,
                "name": rate.get("room_name") or "Room",
                "board": rate.get("board") or "Room Only",
                "adults": booking.adults,
                "children": 0,
                "amount": _money(booking.amount, booking.currency),
            }
        )

    cancel_rows = []
    for info in cancel.get("cancelPolicyInfos") or []:
        if not isinstance(info, dict):
            continue
        cancel_rows.append(
            {
                "from": info.get("cancelTime") or info.get("from") or "—",
                "to": info.get("to") or "—",
                "amount": info.get("amount"),
                "currency": info.get("currency") or booking.currency,
                "type": info.get("type") or "",
            }
        )

    holder = raw.get("holder") or {}
    guest_info = raw.get("guestInfo") or raw.get("guests") or []
    if isinstance(guest_info, dict):
        guest_info = guest_info.get("guests") or [guest_info]

    guests = []
    for g in guest_info:
        if not isinstance(g, dict):
            continue
        guests.append(
            {
                "name": f"{g.get('firstName', '')} {g.get('lastName', '')}".strip(),
                "email": g.get("email") or "",
            }
        )
    if not guests:
        guests.append(
            {
                "name": booking.guest_full_name,
                "email": booking.guest_email,
            }
        )

    refundable_tag = (cancel.get("refundableTag") or raw.get("refundableTag") or "").upper()
    if not refundable_tag and rate.get("is_refundable"):
        refundable_tag = "RFN"
    elif not refundable_tag:
        refundable_tag = "NRFN" if rate.get("refundable_label") == "Non-Refundable" else ""

    return {
        "booking": booking,
        "booking_id": raw.get("bookingId") or booking.liteapi_booking_id or str(booking.pk),
        "hotel_confirmation_code": raw.get("hotelConfirmationCode") or booking.hotel_confirmation_code,
        "supplier_booking_id": raw.get("supplierBookingId") or raw.get("supplierBookingName") or "",
        "supplier": raw.get("supplier") or raw.get("supplierId") or "",
        "status": raw.get("status") or booking.get_status_display(),
        "hotel_name": hotel.get("name") or booking.hotel_name or booking.hotel_id,
        "hotel_address": hotel.get("address") or rate.get("hotel_address") or "",
        "hotel_id": hotel.get("hotelId") or booking.hotel_id,
        "checkin": _fmt_date(raw.get("checkin") or str(booking.check_in or "")),
        "checkout": _fmt_date(raw.get("checkout") or str(booking.check_out or "")),
        "created_at": raw.get("createdAt") or booking.created_at,
        "guests": guests,
        "holder_name": f"{holder.get('firstName', booking.guest_first_name)} {holder.get('lastName', booking.guest_last_name)}".strip(),
        "holder_email": holder.get("email") or booking.guest_email,
        "rooms": rooms,
        "total": _money(raw.get("price") or booking.amount, raw.get("currency") or booking.currency),
        "currency": raw.get("currency") or booking.currency,
        "refundable_tag": refundable_tag,
        "refundable_label": (
            "Refundable" if refundable_tag == "RFN"
            else "Non-Refundable" if refundable_tag == "NRFN"
            else rate.get("refundable_label") or "See policy"
        ),
        "cancel_rows": cancel_rows,
        "hotel_remarks": cancel.get("hotelRemarks") or rate.get("hotel_remarks") or "",
        "special_requests": rate.get("special_requests") or "",
        "payment_method": booking.payment_method or "card",
        "is_demo": str(raw.get("bookingId") or "").startswith("DEMO-"),
        "raw_book": raw,
    }


def build_demo_book_response(booking, rate_snapshot: dict) -> dict:
    """Sandbox fallback shaped like LiteAPI /rates/book response."""
    amount = booking.amount
    currency = booking.currency or "USD"
    return {
        "bookingId": f"DEMO-{booking.pk:06d}",
        "hotelConfirmationCode": f"HCN-DEMO-{booking.pk:04d}",
        "supplierBookingId": f"SUP-DEMO-{booking.pk:04d}",
        "supplier": "LiteAPI Sandbox",
        "status": "CONFIRMED",
        "checkin": str(booking.check_in or ""),
        "checkout": str(booking.check_out or ""),
        "price": float(amount) if amount is not None else None,
        "currency": currency,
        "createdAt": booking.updated_at.isoformat() if booking.updated_at else "",
        "hotel": {
            "hotelId": booking.hotel_id,
            "name": booking.hotel_name,
            "address": rate_snapshot.get("hotel_address") or "",
        },
        "holder": {
            "firstName": booking.guest_first_name,
            "lastName": booking.guest_last_name,
            "email": booking.guest_email,
        },
        "guestInfo": [
            {
                "occupancyNumber": 1,
                "firstName": booking.guest_first_name,
                "lastName": booking.guest_last_name,
                "email": booking.guest_email,
            }
        ],
        "bookedRooms": [
            {
                "roomType": {"name": rate_snapshot.get("room_name") or "Standard Room"},
                "adults": booking.adults,
                "children": 0,
                "rate": {
                    "boardName": rate_snapshot.get("board") or "Room Only",
                    "boardType": rate_snapshot.get("board_type") or "RO",
                    "retailRate": {
                        "total": [{"amount": float(amount) if amount else 0, "currency": currency}]
                    },
                },
            }
        ],
        "cancellationPolicies": {
            "refundableTag": "RFN" if rate_snapshot.get("is_refundable") else "NRFN",
            "hotelRemarks": rate_snapshot.get("hotel_remarks") or "",
            "cancelPolicyInfos": rate_snapshot.get("cancel_policies") or [],
        },
    }

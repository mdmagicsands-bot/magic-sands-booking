from __future__ import annotations

import json
from datetime import date, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from bookings.models import Booking
from hotels.liteapi import (
    MAX_ADULTS_PER_ROOM,
    MAX_CHILD_AGE,
    MAX_CHILDREN_PER_ROOM,
    MAX_ROOMS,
    MIN_CHILD_AGE,
    NATIONALITY_CHOICES,
    LiteAPIError,
    get_client,
    is_search_market_country,
    normalize_nationality,
    occupancy_totals,
    parse_occupancies_from_request,
)
from hotels.views import (
    _build_cards,
    _default_dates,
    _looks_like_hotel_query,
    _parse_date,
    build_hotel_detail_context,
    lookup_hotels_by_name,
    organize_hotel_search_results,
)

from .forms import GuestLoginForm, GuestProfileForm, GuestRegisterForm
from .models import GuestProfile

User = get_user_model()


def _is_guest_user(user) -> bool:
    return user.is_authenticated and user.is_active and not user.is_staff


def _guest_required(view):
    """Allow only non-staff partner accounts into the booking portal."""

    @login_required(login_url="partner_login")
    def _wrapped(request, *args, **kwargs):
        if request.user.is_staff:
            messages.info(request, "Staff accounts use the website admin.")
            return redirect("admin_hub")
        return view(request, *args, **kwargs)

    return _wrapped


def _get_or_create_profile(user) -> GuestProfile:
    profile, _ = GuestProfile.objects.get_or_create(user=user)
    return profile


PARTNER_CURRENCY = "USD"


def _search_form_context(request, profile: GuestProfile | None = None) -> dict:
    """Shared context for the partner accommodation search form."""
    checkin, checkout = _default_dates()
    profile = profile or _get_or_create_profile(request.user)
    data = request.GET
    checkin_s = data.get("checkin", checkin)
    checkout_s = data.get("checkout", checkout)
    start = _parse_date(checkin_s)
    end = _parse_date(checkout_s)
    nights = (end - start).days if start and end and end > start else 1
    default_nat = normalize_nationality(
        data.get("nationality") or profile.nationality or settings.DEFAULT_GUEST_NATIONALITY
    )
    selected_stars = data.getlist("stars") if hasattr(data, "getlist") else []
    occupancies = parse_occupancies_from_request(data)
    totals = occupancy_totals(occupancies)
    return {
        "checkin": checkin_s,
        "checkout": checkout_s,
        "nights": str(nights),
        "adults": str(totals["adults"]),
        "rooms": str(totals["rooms"]),
        "children_count": totals["children"],
        "occupancies": occupancies,
        "occupancies_json": json.dumps(occupancies),
        "occupancy_label": _occupancy_label(totals),
        "destination": data.get("destination", ""),
        "place_id": data.get("place_id", ""),
        "hotel_id": data.get("hotel_id", ""),
        "country_code": data.get("country_code", ""),
        "query": "",
        "nationality": default_nat,
        "nationality_choices": NATIONALITY_CHOICES,
        "min_date": date.today().isoformat(),
        "currency": PARTNER_CURRENCY,
        "selected_stars": selected_stars,
        "profile": profile,
        "max_rooms": MAX_ROOMS,
        "max_adults_per_room": MAX_ADULTS_PER_ROOM,
        "max_children_per_room": MAX_CHILDREN_PER_ROOM,
        "min_child_age": MIN_CHILD_AGE,
        "max_child_age": MAX_CHILD_AGE,
    }


def _occupancy_label(totals: dict) -> str:
    guests = totals.get("guests") or (totals["adults"] + totals.get("children", 0))
    return f"{guests} Guest(s) in {totals['rooms']} Room(s)"


def _fmt_display_date(value: str) -> str:
    """Format YYYY-MM-DD as '26 Jul 2026'."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")
    except (TypeError, ValueError):
        return value or ""


def _adults_rooms_label(totals: dict) -> str:
    return f"{totals['adults']} Adult(s) in {totals['rooms']} Room(s)"


def _authenticate_guest(request, email: str, password: str):
    email = (email or "").strip().lower()
    user = authenticate(request, username=email, password=password)
    if user is None:
        match = User.objects.filter(email__iexact=email).first()
        if match:
            user = authenticate(request, username=match.username, password=password)
    if user is not None and user.is_active and not user.is_staff:
        return user
    return None


@require_http_methods(["GET", "POST"])
def guest_login(request):
    """Legacy URL — partner front-end login lives at /partner-login/."""
    return redirect("partner_login")


@require_http_methods(["GET", "POST"])
def guest_register(request):
    if _is_guest_user(request.user):
        return redirect("guest_search")

    form = GuestRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        user = User.objects.create_user(
            username=email,
            email=email,
            password=form.cleaned_data["password"],
            first_name=form.cleaned_data["first_name"].strip(),
            last_name=form.cleaned_data["last_name"].strip(),
            is_staff=False,
        )
        GuestProfile.objects.create(
            user=user,
            phone=(form.cleaned_data.get("phone") or "").strip(),
        )
        login(request, user)
        messages.success(request, "Welcome to Magic Sands. Start searching hotels.")
        return redirect("guest_search")

    return render(request, "guests/register.html", {"form": form})


@require_POST
def guest_logout(request):
    logout(request)
    return redirect("partner_login")


@_guest_required
@require_http_methods(["GET"])
def dashboard(request):
    profile = _get_or_create_profile(request.user)
    bookings = (
        Booking.objects.filter(
            Q(user=request.user) | Q(guest_email__iexact=request.user.email)
        )
        .distinct()
        .order_by("-created_at")[:5]
    )
    stats = {
        "total": Booking.objects.filter(
            Q(user=request.user) | Q(guest_email__iexact=request.user.email)
        )
        .distinct()
        .count(),
        "confirmed": Booking.objects.filter(
            Q(user=request.user) | Q(guest_email__iexact=request.user.email),
            status=Booking.Status.CONFIRMED,
        )
        .distinct()
        .count(),
        "upcoming": Booking.objects.filter(
            Q(user=request.user) | Q(guest_email__iexact=request.user.email),
            status=Booking.Status.CONFIRMED,
            check_in__gte=date.today(),
        )
        .distinct()
        .count(),
    }
    return render(
        request,
        "guests/dashboard.html",
        {
            "profile": profile,
            "recent_bookings": bookings,
            "stats": stats,
        },
    )


@_guest_required
@require_http_methods(["GET"])
def search_home(request):
    ctx = _search_form_context(request)
    ctx.update({"cards": None, "searched": False})
    return render(request, "guests/search.html", ctx)


@_guest_required
@require_http_methods(["GET", "POST"])
def search_results(request):
    data = request.POST if request.method == "POST" else request.GET
    checkin = (data.get("checkin") or "").strip()
    checkout = (data.get("checkout") or "").strip()
    place_id = (data.get("place_id") or "").strip()
    hotel_id = (data.get("hotel_id") or "").strip()
    destination = (data.get("destination") or "").strip()
    country_code = (data.get("country_code") or "").strip().upper()
    query = (data.get("q") or "").strip()
    profile = _get_or_create_profile(request.user)
    nationality = normalize_nationality(
        data.get("nationality") or profile.nationality or settings.DEFAULT_GUEST_NATIONALITY
    )
    occupancies = parse_occupancies_from_request(data)
    totals = occupancy_totals(occupancies)
    currency = PARTNER_CURRENCY

    if not checkin or not checkout:
        messages.error(request, "Please choose check-in and check-out dates.")
        return redirect("guest_search")

    start = _parse_date(checkin)
    end = _parse_date(checkout)
    if not start or not end:
        messages.error(request, "Dates must be in YYYY-MM-DD format.")
        return redirect("guest_search")
    if end <= start:
        messages.error(request, "Check-out must be after check-in.")
        return redirect("guest_search")
    if not destination and not hotel_id and not query:
        messages.error(request, "Enter a destination or hotel name.")
        return redirect("guest_search")
    if country_code and not is_search_market_country(country_code):
        messages.error(
            request,
            "Search is limited to GCC countries and Egypt for now. Pick a destination in that region.",
        )
        return redirect("guest_search")

    request.session["search"] = {
        "checkin": checkin,
        "checkout": checkout,
        "adults": totals["adults"],
        "rooms": totals["rooms"],
        "occupancies": occupancies,
        "place_id": place_id,
        "hotel_id": hotel_id,
        "destination": destination,
        "country_code": country_code,
        "q": query,
        "nationality": nationality,
        "currency": currency,
    }

    cards: list[dict] = []
    sandbox = None
    organized: dict = {"hotel_search_mode": False}
    try:
        client = get_client()
        payload: dict = {"data": [], "hotels": []}
        rate_kwargs = {
            "checkin": checkin,
            "checkout": checkout,
            "occupancies": occupancies,
            "guest_nationality": nationality,
            "currency": currency,
            "max_rates_per_hotel": 1,
            "include_hotel_data": True,
        }
        dest_l = destination.lower()
        hotel_matches: list[dict] = []
        # Only run multi-country hotel name lookup for property-like queries
        # and when the user did not already pick a destination place_id.
        if destination and not hotel_id and not place_id and _looks_like_hotel_query(destination):
            for h in lookup_hotels_by_name(
                client,
                destination,
                limit_per_country=3,
                prefer_country=nationality or country_code or "OM",
                max_countries=4,
                timeout=12,
                max_results=6,
            ):
                name_l = (h.get("name") or "").lower()
                if dest_l == name_l or dest_l in name_l or name_l in dest_l:
                    hotel_matches.append(h)

        if hotel_id:
            payload = client.search_rates(hotel_ids=[hotel_id], **rate_kwargs)
        elif place_id:
            # Selected destination from autocomplete — fastest path.
            payload = client.search_rates(place_id=place_id, **rate_kwargs)
            if not (payload.get("data") or payload.get("hotels")) and destination:
                payload = client.search_rates(ai_search=destination, **rate_kwargs)
        elif hotel_matches:
            ids = [
                str(h.get("id") or h.get("hotelId") or "").strip()
                for h in hotel_matches
            ]
            ids = [i for i in ids if i][:8]
            payload = client.search_rates(hotel_ids=ids, **rate_kwargs)
            if not (payload.get("data") or payload.get("hotels")):
                payload = client.search_rates(ai_search=destination, **rate_kwargs)
        elif destination and country_code:
            payload = client.search_rates(
                city_name=destination,
                country_code=country_code,
                **rate_kwargs,
            )
            if not (payload.get("data") or payload.get("hotels")):
                payload = client.search_rates(ai_search=destination, **rate_kwargs)
        elif destination:
            payload = client.search_rates(ai_search=destination, **rate_kwargs)
        elif query:
            payload = client.search_rates(ai_search=query, **rate_kwargs)
        cards = _build_cards(payload)
        sandbox = payload.get("sandbox")
        organized = organize_hotel_search_results(
            client,
            cards,
            hotel_id=hotel_id,
            place_id=place_id,
            destination=destination,
            hotel_matches=hotel_matches if hotel_matches else None,
            rate_kwargs=rate_kwargs,
        )
        if organized["hotel_search_mode"]:
            cards = organized["cards"]
    except LiteAPIError as exc:
        messages.error(request, f"Search failed: {exc}")
        return redirect("guest_search")

    nights = (end - start).days
    all_cards = cards[:]
    if organized.get("hotel_search_mode"):
        all_cards = [organized["choice_hotel"], *organized["recommended_hotels"], *organized["nearby_hotels"]]
    prices = [c["price"] for c in all_cards if c.get("price") is not None]
    price_min = int(min(prices)) if prices else 0
    price_max = int(max(prices)) + 1 if prices else 1000
    selected_stars = data.getlist("stars") if hasattr(data, "getlist") else []
    result_count = organized.get("result_count") if organized.get("hotel_search_mode") else len(cards)

    return render(
        request,
        "guests/search.html",
        {
            "checkin": checkin,
            "checkout": checkout,
            "adults": str(totals["adults"]),
            "rooms": str(totals["rooms"]),
            "children_count": totals["children"],
            "occupancies": occupancies,
            "occupancies_json": json.dumps(occupancies),
            "occupancy_label": _occupancy_label(totals),
            "destination": destination or query,
            "place_id": place_id,
            "hotel_id": hotel_id,
            "country_code": country_code,
            "query": query,
            "nationality": nationality,
            "nationality_choices": NATIONALITY_CHOICES,
            "min_date": date.today().isoformat(),
            "currency": currency,
            "selected_stars": selected_stars,
            "profile": profile,
            "cards": cards,
            "hotel_search_mode": organized.get("hotel_search_mode", False),
            "choice_hotel": organized.get("choice_hotel"),
            "choice_hotel_name": organized.get("choice_hotel_name", ""),
            "recommended_hotels": organized.get("recommended_hotels", []),
            "nearby_hotels": organized.get("nearby_hotels", []),
            "searched": True,
            "sandbox": sandbox,
            "result_count": result_count,
            "nights": str(nights),
            "price_min": price_min,
            "price_max": price_max,
            "max_rooms": MAX_ROOMS,
            "max_adults_per_room": MAX_ADULTS_PER_ROOM,
            "max_children_per_room": MAX_CHILDREN_PER_ROOM,
            "min_child_age": MIN_CHILD_AGE,
            "max_child_age": MAX_CHILD_AGE,
            "checkin_display": _fmt_display_date(checkin),
            "checkout_display": _fmt_display_date(checkout),
            "adults_rooms_label": _adults_rooms_label(totals),
            "show_recent": False,
        },
    )


@_guest_required
@require_http_methods(["GET"])
def bookings_list(request):
    bookings = (
        Booking.objects.filter(
            Q(user=request.user) | Q(guest_email__iexact=request.user.email)
        )
        .distinct()
        .order_by("-created_at")
    )
    status = (request.GET.get("status") or "").strip()
    if status:
        bookings = bookings.filter(status=status)
    return render(
        request,
        "guests/bookings.html",
        {
            "bookings": bookings,
            "status": status,
            "status_choices": Booking.Status.choices,
        },
    )


@_guest_required
@require_http_methods(["GET"])
def booking_detail(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.filter(
            Q(user=request.user) | Q(guest_email__iexact=request.user.email)
        ).distinct(),
        pk=booking_id,
    )
    return render(request, "guests/booking_detail.html", {"booking": booking})


@_guest_required
@require_http_methods(["GET", "POST"])
def profile(request):
    guest_profile = _get_or_create_profile(request.user)
    initial = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "phone": guest_profile.phone,
        "nationality": guest_profile.nationality or "OM",
        "preferred_currency": guest_profile.preferred_currency or "USD",
    }
    form = GuestProfileForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        request.user.first_name = form.cleaned_data["first_name"].strip()
        request.user.last_name = form.cleaned_data["last_name"].strip()
        request.user.save(update_fields=["first_name", "last_name"])
        guest_profile.phone = (form.cleaned_data.get("phone") or "").strip()
        guest_profile.nationality = (
            (form.cleaned_data.get("nationality") or "OM").strip().upper()[:2]
        )
        guest_profile.preferred_currency = (
            (form.cleaned_data.get("preferred_currency") or "USD").strip().upper()[:8]
        )
        guest_profile.save()
        messages.success(request, "Profile updated.")
        return redirect("guest_profile")

    return render(
        request,
        "guests/profile.html",
        {"form": form, "profile": guest_profile},
    )


@_guest_required
@require_http_methods(["GET"])
def saved_hotels(request):
    return render(request, "guests/saved.html")


@_guest_required
@require_http_methods(["GET"])
def support(request):
    return render(request, "guests/support.html")


@_guest_required
@require_GET
def privacy_policy(request):
    from marketing.legal_content import PRIVACY_POLICY

    return render(request, "guests/privacy_policy.html", {"privacy": PRIVACY_POLICY})


@_guest_required
@require_http_methods(["GET"])
def hotel_detail(request, hotel_id: str):
    """Partner portal hotel rates — table model fed by Nuitee/LiteAPI."""
    try:
        context = build_hotel_detail_context(request, hotel_id)
    except LiteAPIError as exc:
        messages.error(request, f"Could not load hotel rates: {exc}")
        return redirect("guest_search")

    totals = {
        "rooms": context.get("rooms_count") or 1,
        "adults": context.get("adults") or 2,
        "children": context.get("children_count") or 0,
    }
    form_ctx = _search_form_context(request)
    # Prefill search form with this stay so Modify Search works on the hotel page.
    form_ctx.update(
        {
            "checkin": context.get("checkin"),
            "checkout": context.get("checkout"),
            "adults": str(context.get("adults") or 2),
            "rooms": str(context.get("rooms_count") or 1),
            "nationality": context.get("nationality"),
            "destination": context.get("hotel", {}).get("name") or "",
            "occupancies": context.get("occupancies") or form_ctx.get("occupancies"),
            "occupancies_json": json.dumps(context.get("occupancies") or []),
            "show_recent": False,
        }
    )
    context.update(form_ctx)
    rooms_n = totals["rooms"]
    adults_n = totals["adults"]
    children_n = totals["children"]
    stay_occupancy_label = (
        f"{rooms_n} room{'s' if rooms_n != 1 else ''} "
        f"({adults_n} adult{'s' if adults_n != 1 else ''}, "
        f"{children_n} {'child' if children_n == 1 else 'children'})"
    )
    context.update(
        {
            "checkin_display": _fmt_display_date(context.get("checkin") or ""),
            "checkout_display": _fmt_display_date(context.get("checkout") or ""),
            "adults_rooms_label": _adults_rooms_label(totals),
            "occupancy_label": _occupancy_label(totals),
            "stay_occupancy_label": stay_occupancy_label,
            "hotel_id": hotel_id,
            "searched": True,
        }
    )
    return render(request, "guests/hotel_detail.html", context)


@_guest_required
@require_GET
def hotel_rates_api(request, hotel_id: str):
    """JSON rates for inline expand/collapse on search results."""
    try:
        ctx = build_hotel_detail_context(request, hotel_id)
    except LiteAPIError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=502)

    hotel = ctx.get("hotel") or {}
    rates = []
    for row in ctx.get("rate_rows") or []:
        rates.append(
            {
                "offer_id": row.get("offer_id") or "",
                "room_name": row.get("room_name") or "Room",
                "board": row.get("board") or "Room Only",
                "board_type": row.get("board_type") or "",
                "amount": row.get("amount"),
                "currency": row.get("currency") or "",
                "is_refundable": bool(row.get("is_refundable")),
                "refundable_label": row.get("refundable_label") or "",
                "available": bool(row.get("available", True)),
                "taxes": row.get("taxes") or [],
                "cancel_policies": row.get("cancel_policies") or [],
                "hotel_remarks": row.get("hotel_remarks") or "",
            }
        )

    return JsonResponse(
        {
            "ok": True,
            "hotel_id": hotel_id,
            "hotel_name": hotel.get("name") or hotel_id,
            "occupancy_summary": ctx.get("occupancy_summary") or "",
            "rate_count": len(rates),
            "checkin": ctx.get("checkin"),
            "checkout": ctx.get("checkout"),
            "adults": ctx.get("adults"),
            "nights": ctx.get("nights"),
            "board_options": ctx.get("board_options") or [],
            "room_options": ctx.get("room_options") or [],
            "rates": rates,
            "detail_url": reverse("guest_hotel_detail", kwargs={"hotel_id": hotel_id}),
            "checkout_url": reverse("checkout"),
        }
    )

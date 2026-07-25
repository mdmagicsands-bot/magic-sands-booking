"""Admin inventory + live hotel search wired to Nuitee Connect / LiteAPI."""

from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from django.conf import settings

from hotels.liteapi import (
    NATIONALITY_CHOICES,
    LiteAPIError,
    get_client,
    liteapi_connection_status,
    normalize_nationality,
)
from hotels.views import _build_cards, _default_dates, _parse_date


def _is_staff(user):
    return user.is_authenticated and user.is_staff


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
@require_http_methods(["GET"])
def live_hotel_search(request):
    """Admin live rates search against Nuitee /hotels/rates."""
    checkin_default, checkout_default = _default_dates()
    checkin = (request.GET.get("checkin") or checkin_default).strip()
    checkout = (request.GET.get("checkout") or checkout_default).strip()
    adults = int(request.GET.get("adults") or 2)
    destination = (request.GET.get("destination") or "").strip()
    country_code = (request.GET.get("country_code") or "").strip().upper()
    query = (request.GET.get("q") or "").strip()
    place_id = (request.GET.get("place_id") or "").strip()
    nationality = normalize_nationality(
        request.GET.get("nationality") or settings.DEFAULT_GUEST_NATIONALITY
    )

    api = liteapi_connection_status()
    cards: list[dict] = []
    searched = False
    result_count = 0
    sandbox = None
    nights = 0

    if request.GET.get("run") == "1" or destination or query:
        searched = True
        start = _parse_date(checkin)
        end = _parse_date(checkout)
        if not start or not end:
            messages.error(request, "Dates must be in YYYY-MM-DD format.")
        elif end <= start:
            messages.error(request, "Check-out must be after check-in.")
        elif not destination and not query:
            messages.error(request, "Enter a destination or free-text vibe search.")
        else:
            nights = (end - start).days
            try:
                client = get_client()
                payload: dict = {"data": [], "hotels": []}
                if query and not destination:
                    payload = client.search_rates(
                        checkin=checkin,
                        checkout=checkout,
                        adults=adults,
                        ai_search=query,
                        guest_nationality=nationality,
                        max_rates_per_hotel=1,
                        include_hotel_data=True,
                    )
                else:
                    if destination and country_code:
                        payload = client.search_rates(
                            checkin=checkin,
                            checkout=checkout,
                            adults=adults,
                            city_name=destination,
                            country_code=country_code,
                            guest_nationality=nationality,
                            max_rates_per_hotel=1,
                            include_hotel_data=True,
                        )
                    if not (payload.get("data") or payload.get("hotels")):
                        payload = client.search_rates(
                            checkin=checkin,
                            checkout=checkout,
                            adults=adults,
                            ai_search=destination or query or "hotel",
                            guest_nationality=nationality,
                            max_rates_per_hotel=1,
                            include_hotel_data=True,
                        )
                cards = _build_cards(payload)
                result_count = len(cards)
                sandbox = payload.get("sandbox")
            except LiteAPIError as exc:
                messages.error(request, f"Live search failed: {exc}")

    return render(
        request,
        "partners/nuitee_live_search.html",
        {
            "api": api,
            "checkin": checkin,
            "checkout": checkout,
            "adults": adults,
            "destination": destination,
            "country_code": country_code,
            "query": query,
            "place_id": place_id,
            "nationality": nationality,
            "nationality_choices": NATIONALITY_CHOICES,
            "min_date": date.today().isoformat(),
            "cards": cards,
            "searched": searched,
            "result_count": result_count,
            "sandbox": sandbox,
            "nights": nights,
        },
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
@require_GET
def nuitee_inventory(request):
    """Browse Nuitee static hotel inventory via /data/hotels."""
    city = (request.GET.get("city") or "Muscat").strip()
    country = (request.GET.get("country") or "OM").strip().upper()
    hotel_name = (request.GET.get("hotel_name") or "").strip()
    try:
        limit = min(max(int(request.GET.get("limit") or 40), 1), 100)
    except ValueError:
        limit = 40
    try:
        offset = max(int(request.GET.get("offset") or 0), 0)
    except ValueError:
        offset = 0

    api = liteapi_connection_status()
    hotels: list[dict] = []
    total = None
    error = None

    if api["configured"]:
        try:
            client = get_client()
            payload = client.list_hotels(
                country_code=country or None,
                city_name=city or None,
                hotel_name=hotel_name or None,
                limit=limit,
                offset=offset,
            )
            hotels = payload.get("data") or []
            total = payload.get("total")
        except LiteAPIError as exc:
            error = str(exc)
            messages.error(request, f"Inventory lookup failed: {exc}")
    else:
        error = api["message"]

    return render(
        request,
        "partners/nuitee_inventory.html",
        {
            "api": api,
            "hotels": hotels,
            "total": total,
            "city": city,
            "country": country,
            "hotel_name": hotel_name,
            "limit": limit,
            "offset": offset,
            "error": error,
            "next_offset": offset + limit if hotels and (total is None or offset + limit < total) else None,
            "prev_offset": max(offset - limit, 0) if offset else None,
        },
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
@require_GET
def liteapi_settings(request):
    """Show Nuitee / LiteAPI connection status (keys from .env)."""
    api = liteapi_connection_status()
    return render(
        request,
        "partners/liteapi_settings.html",
        {
            "api": api,
            "inventory_url": reverse("admin_mod_nuitee_hotels"),
            "search_url": reverse("admin_live_search"),
        },
    )

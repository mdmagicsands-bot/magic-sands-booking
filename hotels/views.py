from __future__ import annotations

from datetime import date, datetime, timedelta

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from django.conf import settings

from .liteapi import (
    NATIONALITY_CHOICES,
    LiteAPIError,
    country_code_from_address,
    first_offer_id,
    get_client,
    lowest_total,
    normalize_nationality,
)


def _default_dates() -> tuple[str, str]:
    checkin = date.today() + timedelta(days=14)
    checkout = checkin + timedelta(days=2)
    return checkin.isoformat(), checkout.isoformat()


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _cheapest_rate_meta(rate_block: dict) -> dict:
    """Pull board / refundable / room name from the cheapest offer."""
    best: dict = {
        "board": "",
        "refundable": "",
        "room_name": "",
        "offer_id": None,
    }
    best_price: float | None = None
    for rt in rate_block.get("roomTypes") or []:
        offer_id = rt.get("offerId")
        for rate in rt.get("rates") or []:
            totals = (rate.get("retailRate") or {}).get("total") or []
            if not totals:
                continue
            try:
                amount = float(totals[0].get("amount"))
            except (TypeError, ValueError):
                continue
            if best_price is not None and amount >= best_price:
                continue
            best_price = amount
            cancel = rate.get("cancellationPolicies") or {}
            best = {
                "board": rate.get("boardName") or "",
                "refundable": cancel.get("refundableTag") or "",
                "room_name": rate.get("name") or "",
                "offer_id": offer_id or rate.get("offerId"),
            }
    return best


def _normalize_stars(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    # LiteAPI sometimes returns review score 0–10; stars are usually 1–5.
    if num > 5:
        num = round(num / 2)
    stars = int(round(num))
    return max(0, min(5, stars)) if stars else None


def _build_cards(payload: dict) -> list[dict]:
    rates_by_id = {item.get("hotelId"): item for item in (payload.get("data") or [])}
    hotels_meta = {h.get("id"): h for h in (payload.get("hotels") or []) if h.get("id")}

    cards = []
    hotel_ids = list(dict.fromkeys([*hotels_meta.keys(), *rates_by_id.keys()]))
    for hotel_id in hotel_ids:
        rate_block = rates_by_id.get(hotel_id) or {}
        meta = hotels_meta.get(hotel_id) or rate_block.get("hotel") or {}
        price, currency = lowest_total(rate_block)
        rate_meta = _cheapest_rate_meta(rate_block)
        photo = (
            meta.get("main_photo")
            or meta.get("mainPhoto")
            or meta.get("thumbnail")
            or (meta.get("hotelImages") or [{}])[0].get("url")
        )
        stars = _normalize_stars(
            meta.get("stars") or meta.get("starRating") or meta.get("star_rating")
        )
        review = meta.get("rating")
        try:
            review_score = float(review) if review is not None else None
        except (TypeError, ValueError):
            review_score = None
        # If rating looks like 0–10 guest score, keep it; if 1–5 and no stars, treat as stars.
        if stars is None and review_score is not None and review_score <= 5:
            stars = _normalize_stars(review_score)
            review_score = None

        cards.append(
            {
                "hotel_id": hotel_id,
                "name": meta.get("name") or rate_block.get("hotelName") or hotel_id,
                "photo": photo,
                "address": meta.get("address")
                or meta.get("formattedAddress")
                or ", ".join(
                    x
                    for x in [meta.get("city_name") or meta.get("city"), meta.get("country_code")]
                    if x
                ),
                "city": meta.get("city_name") or meta.get("city") or "",
                "stars": stars or 0,
                "review_score": review_score,
                "review_count": meta.get("review_count") or meta.get("reviewCount"),
                "price": price,
                "currency": currency or "USD",
                "board": rate_meta["board"],
                "refundable": rate_meta["refundable"],
                "room_name": rate_meta["room_name"],
                "tags": meta.get("tags") or [],
            }
        )

    for card in cards:
        if card["name"] == card["hotel_id"]:
            rb = rates_by_id.get(card["hotel_id"]) or {}
            nested = rb.get("hotel") or {}
            if nested.get("name"):
                card["name"] = nested["name"]
            if not card["photo"]:
                card["photo"] = nested.get("main_photo") or nested.get("mainPhoto")
            if not card["address"]:
                card["address"] = nested.get("address") or ""

    cards.sort(key=lambda c: (c["price"] is None, c["price"] or 0))
    return cards


@require_GET
def home(request):
    checkin, checkout = _default_dates()
    return render(
        request,
        "hotels/home.html",
        {
            "checkin": request.GET.get("checkin", checkin),
            "checkout": request.GET.get("checkout", checkout),
            "adults": request.GET.get("adults", "2"),
            "destination": request.GET.get("destination", ""),
            "place_id": request.GET.get("place_id", ""),
            "country_code": request.GET.get("country_code", ""),
            "query": request.GET.get("q", ""),
            "nationality": normalize_nationality(
                request.GET.get("nationality") or settings.DEFAULT_GUEST_NATIONALITY
            ),
            "nationality_choices": NATIONALITY_CHOICES,
            "min_date": date.today().isoformat(),
        },
    )


@require_GET
def places_autocomplete(request):
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})
    try:
        client = get_client()
        places = client.search_places(q)[:8]
    except LiteAPIError as exc:
        return JsonResponse({"results": [], "error": str(exc)}, status=502)
    results = []
    for p in places:
        if not p.get("placeId"):
            continue
        address = p.get("formattedAddress") or ""
        results.append(
            {
                "placeId": p.get("placeId"),
                "displayName": p.get("displayName"),
                "formattedAddress": address,
                "countryCode": country_code_from_address(address),
            }
        )
    return JsonResponse({"results": results})


@require_http_methods(["GET", "POST"])
def search(request):
    data = request.POST if request.method == "POST" else request.GET
    checkin = (data.get("checkin") or "").strip()
    checkout = (data.get("checkout") or "").strip()
    adults = int(data.get("adults") or 2)
    place_id = (data.get("place_id") or "").strip()
    destination = (data.get("destination") or "").strip()
    country_code = (data.get("country_code") or "").strip().upper()
    query = (data.get("q") or "").strip()
    nationality = normalize_nationality(
        data.get("nationality") or settings.DEFAULT_GUEST_NATIONALITY
    )

    if not checkin or not checkout:
        messages.error(request, "Please choose check-in and check-out dates.")
        return redirect("book_home")

    start = _parse_date(checkin)
    end = _parse_date(checkout)
    if not start or not end:
        messages.error(request, "Dates must be in YYYY-MM-DD format.")
        return redirect("book_home")
    if end <= start:
        messages.error(request, "Check-out must be after check-in.")
        return redirect("book_home")

    if not destination and not query:
        messages.error(request, "Enter a destination or hotel vibe search.")
        return redirect("book_home")

    request.session["search"] = {
        "checkin": checkin,
        "checkout": checkout,
        "adults": adults,
        "place_id": place_id,
        "destination": destination,
        "country_code": country_code,
        "q": query,
        "nationality": nationality,
    }

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
            # City + country is the most reliable sandbox query.
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
                # Fall back to AI search using destination text.
                payload = client.search_rates(
                    checkin=checkin,
                    checkout=checkout,
                    adults=adults,
                    ai_search=destination or query or "hotel",
                    guest_nationality=nationality,
                    max_rates_per_hotel=1,
                    include_hotel_data=True,
                )
    except LiteAPIError as exc:
        messages.error(request, f"Search failed: {exc}")
        return redirect("book_home")

    cards = _build_cards(payload)
    nights = (end - start).days

    prices = [c["price"] for c in cards if c.get("price") is not None]
    price_min = int(min(prices)) if prices else 0
    price_max = int(max(prices)) + 1 if prices else 1000

    return render(
        request,
        "hotels/results.html",
        {
            "cards": cards,
            "checkin": checkin,
            "checkout": checkout,
            "adults": adults,
            "nights": nights,
            "destination": destination or query,
            "place_id": place_id,
            "country_code": country_code,
            "query": query,
            "nationality": nationality,
            "sandbox": payload.get("sandbox"),
            "result_count": len(cards),
            "price_min": price_min,
            "price_max": price_max,
        },
    )


@require_GET
def hotel_detail(request, hotel_id: str):
    search_data = request.session.get("search") or {}
    checkin = request.GET.get("checkin") or search_data.get("checkin")
    checkout = request.GET.get("checkout") or search_data.get("checkout")
    adults = int(request.GET.get("adults") or search_data.get("adults") or 2)
    nationality = normalize_nationality(
        request.GET.get("nationality")
        or search_data.get("nationality")
        or settings.DEFAULT_GUEST_NATIONALITY
    )

    if not checkin or not checkout:
        d1, d2 = _default_dates()
        checkin, checkout = d1, d2

    try:
        client = get_client()
        hotel = client.get_hotel(hotel_id)
        rates_payload = client.search_rates(
            checkin=checkin,
            checkout=checkout,
            adults=adults,
            hotel_ids=[hotel_id],
            guest_nationality=nationality,
            max_rates_per_hotel=None,
            include_hotel_data=True,
        )
    except LiteAPIError as exc:
        messages.error(request, f"Could not load hotel: {exc}")
        return redirect("book_home")

    rate_block = next(
        (r for r in (rates_payload.get("data") or []) if r.get("hotelId") == hotel_id),
        (rates_payload.get("data") or [None])[0],
    ) or {}

    rooms: dict[str, dict] = {}
    for rt in rate_block.get("roomTypes") or []:
        offer_id = rt.get("offerId") or first_offer_id({"roomTypes": [rt]})
        for rate in rt.get("rates") or []:
            room_key = str(rate.get("mappedRoomId") or rate.get("name") or "room")
            room = rooms.setdefault(
                room_key,
                {
                    "name": rate.get("name") or "Room",
                    "image": None,
                    "offers": [],
                },
            )
            totals = (rate.get("retailRate") or {}).get("total") or [{}]
            cancel = rate.get("cancellationPolicies") or {}
            room["offers"].append(
                {
                    "offer_id": offer_id or rate.get("offerId"),
                    "board": rate.get("boardName") or "",
                    "amount": totals[0].get("amount"),
                    "currency": totals[0].get("currency"),
                    "refundable": cancel.get("refundableTag"),
                }
            )

    for room_info in hotel.get("rooms") or []:
        key = str(room_info.get("id") or "")
        if key in rooms:
            photos = room_info.get("photos") or []
            if photos:
                rooms[key]["image"] = photos[0].get("url")
            rooms[key]["name"] = room_info.get("roomName") or rooms[key]["name"]

    images = hotel.get("hotelImages") or []
    main_photo = hotel.get("main_photo") or next(
        (i.get("url") for i in images if i.get("defaultImage")),
        (images[0].get("url") if images else None),
    )

    return render(
        request,
        "hotels/hotel_detail.html",
        {
            "hotel": hotel,
            "hotel_id": hotel_id,
            "main_photo": main_photo,
            "rooms": list(rooms.values()),
            "checkin": checkin,
            "checkout": checkout,
            "adults": adults,
            "nationality": nationality,
        },
    )

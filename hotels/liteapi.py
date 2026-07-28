"""LiteAPI / Nuitee Connect HTTP client (server-side only)."""

from __future__ import annotations

import json
import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Nuitee rates API: each occupancy entry = one room (adults + child ages).
MAX_ROOMS = 4
MAX_ADULTS_PER_ROOM = 9
MAX_CHILDREN_PER_ROOM = 4
MIN_CHILD_AGE = 1
MAX_CHILD_AGE = 18


def normalize_occupancies(
    occupancies: list[dict[str, Any]] | None = None,
    *,
    adults: int = 2,
    children: list[int] | None = None,
) -> list[dict[str, Any]]:
    """
    Build LiteAPI `occupancies` payload.

    Each item: {"adults": int, "children": [age, ...]} — one room per item.
    """
    if not occupancies:
        room: dict[str, Any] = {
            "adults": max(1, min(MAX_ADULTS_PER_ROOM, int(adults or 2)))
        }
        ages = [int(a) for a in (children or []) if MIN_CHILD_AGE <= int(a) <= MAX_CHILD_AGE]
        if ages:
            room["children"] = ages[:MAX_CHILDREN_PER_ROOM]
        return [room]

    cleaned: list[dict[str, Any]] = []
    for raw in occupancies[:MAX_ROOMS]:
        try:
            room_adults = int(raw.get("adults") or 1)
        except (TypeError, ValueError):
            room_adults = 1
        room_adults = max(1, min(MAX_ADULTS_PER_ROOM, room_adults))
        ages: list[int] = []
        for age in raw.get("children") or []:
            try:
                age_i = int(age)
            except (TypeError, ValueError):
                continue
            if MIN_CHILD_AGE <= age_i <= MAX_CHILD_AGE:
                ages.append(age_i)
            if len(ages) >= MAX_CHILDREN_PER_ROOM:
                break
        room = {"adults": room_adults}
        if ages:
            room["children"] = ages
        cleaned.append(room)
    return cleaned or [{"adults": 2}]


def parse_occupancies_from_request(data) -> list[dict[str, Any]]:
    """Parse occupancies from form GET/POST (JSON field or legacy adults/rooms)."""
    raw = (data.get("occupancies") or "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return normalize_occupancies(parsed)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    try:
        adults = int(data.get("adults") or 2)
    except (TypeError, ValueError):
        adults = 2
    try:
        rooms = int(data.get("rooms") or 1)
    except (TypeError, ValueError):
        rooms = 1
    rooms = max(1, min(MAX_ROOMS, rooms))
    adults = max(1, min(MAX_ADULTS_PER_ROOM * rooms, adults))

    # Spread adults across rooms for legacy room-count forms.
    base, rem = divmod(adults, rooms)
    child_ages: list[int] = []
    for age in data.getlist("child_ages") if hasattr(data, "getlist") else []:
        try:
            age_i = int(age)
        except (TypeError, ValueError):
            continue
        if MIN_CHILD_AGE <= age_i <= MAX_CHILD_AGE:
            child_ages.append(age_i)

    occ: list[dict[str, Any]] = []
    for i in range(rooms):
        room_adults = base + (1 if i < rem else 0)
        room: dict[str, Any] = {"adults": max(1, room_adults)}
        if i == 0 and child_ages:
            room["children"] = child_ages[:MAX_CHILDREN_PER_ROOM]
        occ.append(room)
    return normalize_occupancies(occ)


def occupancy_totals(occupancies: list[dict[str, Any]]) -> dict[str, int]:
    adults = sum(int(o.get("adults") or 0) for o in occupancies)
    children = sum(len(o.get("children") or []) for o in occupancies)
    return {
        "rooms": len(occupancies),
        "adults": adults,
        "children": children,
        "guests": adults + children,
    }


class LiteAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class LiteAPIClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.LITEAPI_API_KEY
        self.api_base = settings.LITEAPI_API_BASE.rstrip("/")
        self.book_base = settings.LITEAPI_BOOK_BASE.rstrip("/")
        if not self.api_key:
            raise LiteAPIError(
                "LITEAPI_API_KEY is not set. Add it to .env (see .env.example)."
            )

    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "accept": "application/json",
            "content-type": "application/json",
        }

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        try:
            response = requests.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=json,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise LiteAPIError(f"Network error calling LiteAPI: {exc}") from exc

        try:
            payload = response.json() if response.content else {}
        except ValueError:
            payload = {"raw": response.text}

        if response.status_code >= 400:
            err = payload.get("error") if isinstance(payload, dict) else None
            message = (
                err.get("description") or err.get("message")
                if isinstance(err, dict)
                else f"LiteAPI HTTP {response.status_code}"
            )
            raise LiteAPIError(str(message), status_code=response.status_code, payload=payload)

        return payload if isinstance(payload, dict) else {"data": payload}

    def search_places(self, text_query: str) -> list[dict]:
        payload = self._request(
            "GET",
            f"{self.api_base}/data/places",
            params={"textQuery": text_query},
            timeout=30,
        )
        return payload.get("data") or []

    def get_hotel(self, hotel_id: str) -> dict:
        payload = self._request(
            "GET",
            f"{self.api_base}/data/hotel",
            params={"hotelId": hotel_id, "timeout": 4},
            timeout=30,
        )
        return payload.get("data") or {}

    def get_reviews(
        self,
        hotel_id: str,
        *,
        limit: int = 40,
        get_sentiment: bool = True,
        timeout: int = 20,
    ) -> dict[str, Any]:
        """Guest reviews + optional AI sentiment for a hotel (`GET /data/reviews`)."""
        params: dict[str, Any] = {
            "hotelId": hotel_id,
            "limit": max(1, min(int(limit), 200)),
            "timeout": min(timeout, 30),
        }
        if get_sentiment:
            params["getSentiment"] = "true"
        return self._request(
            "GET",
            f"{self.api_base}/data/reviews",
            params=params,
            timeout=timeout,
        )

    def list_hotels(
        self,
        *,
        country_code: str | None = None,
        city_name: str | None = None,
        hotel_name: str | None = None,
        place_id: str | None = None,
        ai_search: str | None = None,
        hotel_ids: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        timeout: int = 60,
    ) -> dict[str, Any]:
        """Browse static hotel inventory (Nuitee /data/hotels)."""
        params: dict[str, Any] = {
            "limit": max(1, min(int(limit), 200)),
            "offset": max(0, int(offset)),
        }
        if country_code:
            params["countryCode"] = country_code.upper()
        if city_name:
            params["cityName"] = city_name
        if hotel_name:
            params["hotelName"] = hotel_name
        if place_id:
            params["placeId"] = place_id
        if ai_search:
            params["aiSearch"] = ai_search
        if hotel_ids:
            params["hotelIds"] = ",".join(hotel_ids)

        if not any(
            [
                country_code,
                city_name,
                hotel_name,
                place_id,
                ai_search,
                hotel_ids,
            ]
        ):
            raise LiteAPIError(
                "Provide country_code, city_name, hotel_name, place_id, ai_search, or hotel_ids."
            )

        return self._request(
            "GET",
            f"{self.api_base}/data/hotels",
            params=params,
            timeout=timeout,
        )

    def search_rates(
        self,
        *,
        checkin: str,
        checkout: str,
        adults: int = 2,
        children: list[int] | None = None,
        occupancies: list[dict[str, Any]] | None = None,
        place_id: str | None = None,
        hotel_ids: list[str] | None = None,
        hotel_name: str | None = None,
        city_name: str | None = None,
        country_code: str | None = None,
        ai_search: str | None = None,
        currency: str | None = None,
        guest_nationality: str | None = None,
        max_rates_per_hotel: int | None = 1,
        include_hotel_data: bool = True,
        limit: int | None = 50,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "occupancies": normalize_occupancies(
                occupancies, adults=adults, children=children
            ),
            "currency": currency or settings.DEFAULT_CURRENCY,
            "guestNationality": guest_nationality or settings.DEFAULT_GUEST_NATIONALITY,
            "checkin": checkin,
            "checkout": checkout,
            "roomMapping": True,
            "includeHotelData": include_hotel_data,
        }
        if max_rates_per_hotel is not None:
            body["maxRatesPerHotel"] = max_rates_per_hotel
        if limit is not None:
            body["limit"] = limit

        # Prefer exact hotel IDs, then hotel name, city/country, AI, placeId.
        if hotel_ids:
            body["hotelIds"] = hotel_ids
        elif hotel_name:
            body["hotelName"] = hotel_name
            if country_code:
                body["countryCode"] = country_code
            if city_name:
                body["cityName"] = city_name
        elif city_name and country_code:
            body["cityName"] = city_name
            body["countryCode"] = country_code
        elif ai_search:
            body["aiSearch"] = ai_search
        elif place_id:
            body["placeId"] = place_id
        elif city_name:
            body["cityName"] = city_name
        else:
            raise LiteAPIError(
                "Provide hotel_ids, hotel_name, city_name+country_code, ai_search, or place_id."
            )

        return self._request(
            "POST",
            f"{self.api_base}/hotels/rates",
            json=body,
            timeout=90,
        )

    def prebook(self, offer_id: str, *, use_payment_sdk: bool = True) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"{self.book_base}/rates/prebook",
            json={"usePaymentSdk": use_payment_sdk, "offerId": offer_id},
            timeout=90,
        )
        return payload.get("data") or payload

    def book(
        self,
        *,
        prebook_id: str,
        transaction_id: str,
        holder: dict[str, str],
        guests: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"{self.book_base}/rates/book",
            json={
                "prebookId": prebook_id,
                "holder": holder,
                "payment": {
                    "method": "TRANSACTION_ID",
                    "transactionId": transaction_id,
                },
                "guests": guests,
            },
            timeout=90,
        )
        return payload.get("data") or payload

    def book_on_credit(
        self,
        *,
        prebook_id: str,
        holder: dict[str, str],
        guests: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"{self.book_base}/rates/book",
            json={
                "prebookId": prebook_id,
                "holder": holder,
                "payment": {"method": "CREDIT"},
                "guests": guests,
            },
            timeout=90,
        )
        return payload.get("data") or payload

    def get_booking(self, booking_id: str) -> dict[str, Any]:
        payload = self._request(
            "GET",
            f"{self.book_base}/bookings/{booking_id}",
            timeout=30,
        )
        return payload.get("data") or payload


COUNTRY_NAME_TO_CODE = {
    "united arab emirates": "AE",
    "uae": "AE",
    "oman": "OM",
    "saudi arabia": "SA",
    "ksa": "SA",
    "qatar": "QA",
    "bahrain": "BH",
    "kuwait": "KW",
    "egypt": "EG",
    "united kingdom": "GB",
    "uk": "GB",
    "united states": "US",
    "usa": "US",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
    "germany": "DE",
    "turkey": "TR",
    "india": "IN",
    "thailand": "TH",
    "singapore": "SG",
    "malaysia": "MY",
    "indonesia": "ID",
    "maldives": "MV",
    "georgia": "GE",
    "azerbaijan": "AZ",
}

# Inventory search markets: GCC + Egypt only (for now).
SEARCH_MARKET_COUNTRY_CODES = frozenset({"OM", "AE", "SA", "QA", "BH", "KW", "EG"})
SEARCH_MARKET_COUNTRY_ORDER = ("OM", "AE", "SA", "QA", "BH", "KW", "EG")

# Guest nationality options for hotel search (ISO-2 → label).
NATIONALITY_CHOICES = [
    ("OM", "Oman"),
    ("AE", "United Arab Emirates"),
    ("SA", "Saudi Arabia"),
    ("QA", "Qatar"),
    ("BH", "Bahrain"),
    ("KW", "Kuwait"),
    ("IN", "India"),
    ("PK", "Pakistan"),
    ("BD", "Bangladesh"),
    ("PH", "Philippines"),
    ("EG", "Egypt"),
    ("JO", "Jordan"),
    ("LB", "Lebanon"),
    ("TR", "Turkey"),
    ("GB", "United Kingdom"),
    ("US", "United States"),
    ("CA", "Canada"),
    ("AU", "Australia"),
    ("DE", "Germany"),
    ("FR", "France"),
    ("IT", "Italy"),
    ("ES", "Spain"),
    ("NL", "Netherlands"),
    ("RU", "Russia"),
    ("CN", "China"),
    ("JP", "Japan"),
    ("KR", "South Korea"),
    ("SG", "Singapore"),
    ("MY", "Malaysia"),
    ("ID", "Indonesia"),
    ("TH", "Thailand"),
    ("MV", "Maldives"),
    ("ZA", "South Africa"),
    ("NG", "Nigeria"),
    ("KE", "Kenya"),
    ("BR", "Brazil"),
]


def normalize_nationality(value: str | None, default: str | None = None) -> str:
    code = (value or "").strip().upper()[:2]
    valid = {c for c, _ in NATIONALITY_CHOICES}
    if code in valid:
        return code
    fallback = (default or settings.DEFAULT_GUEST_NATIONALITY or "OM").strip().upper()[:2]
    return fallback if fallback in valid else "OM"


def country_code_from_address(address: str | None) -> str | None:
    if not address:
        return None
    lower = address.strip().lower()
    if lower in COUNTRY_NAME_TO_CODE:
        return COUNTRY_NAME_TO_CODE[lower]
    for name, code in COUNTRY_NAME_TO_CODE.items():
        if name in lower:
            return code
    # Last comma segment often is the country
    parts = [p.strip().lower() for p in address.split(",") if p.strip()]
    if parts and parts[-1] in COUNTRY_NAME_TO_CODE:
        return COUNTRY_NAME_TO_CODE[parts[-1]]
    # Bare ISO-2 at end (e.g. "Nizwa, OM")
    if parts and len(parts[-1]) == 2:
        return parts[-1].upper()
    return None


def is_search_market_country(code: str | None) -> bool:
    return bool(code) and code.strip().upper()[:2] in SEARCH_MARKET_COUNTRY_CODES


def hotel_country_code(hotel: dict | None) -> str | None:
    """Best-effort country code from a LiteAPI hotel / meta object."""
    if not hotel:
        return None
    for key in ("countryCode", "country_code", "country"):
        raw = hotel.get(key)
        if not raw:
            continue
        text = str(raw).strip()
        if len(text) == 2:
            return text.upper()
        mapped = COUNTRY_NAME_TO_CODE.get(text.lower())
        if mapped:
            return mapped
    address = hotel.get("address") or hotel.get("formattedAddress") or ""
    city = hotel.get("city") or hotel.get("cityName") or hotel.get("city_name") or ""
    return country_code_from_address(", ".join(x for x in [address, city] if x))


def get_client() -> LiteAPIClient:
    return LiteAPIClient()


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return "(not set)"
    if len(api_key) <= 12:
        return api_key[:4] + "…"
    return f"{api_key[:8]}…{api_key[-4:]}"


def liteapi_connection_status() -> dict[str, Any]:
    """Return connection details for admin settings / inventory headers."""
    api_key = settings.LITEAPI_API_KEY or ""
    public_key = settings.LITEAPI_PUBLIC_KEY or ""
    mode = "sandbox"
    if api_key.startswith("prod_"):
        mode = "live"
    elif api_key.startswith(("sand_", "sandbox_")):
        mode = "sandbox"
    elif api_key:
        mode = "custom"

    status: dict[str, Any] = {
        "configured": bool(api_key),
        "ok": False,
        "mode": mode,
        "public_key": public_key or "—",
        "api_key_masked": mask_api_key(api_key),
        "api_base": settings.LITEAPI_API_BASE,
        "book_base": settings.LITEAPI_BOOK_BASE,
        "currency": settings.DEFAULT_CURRENCY,
        "guest_nationality": settings.DEFAULT_GUEST_NATIONALITY,
        "message": "",
        "sample_hotel": None,
        "total_hint": None,
    }

    if not api_key:
        status["message"] = "LITEAPI_API_KEY is missing from .env"
        return status

    try:
        client = LiteAPIClient(api_key=api_key)
        payload = client.list_hotels(country_code="OM", city_name="Muscat", limit=1)
        hotels = payload.get("data") or []
        status["ok"] = True
        status["total_hint"] = payload.get("total")
        status["message"] = "Connected to Nuitee Connect / LiteAPI"
        if hotels:
            h = hotels[0]
            status["sample_hotel"] = {
                "id": h.get("id"),
                "name": h.get("name"),
                "city": h.get("city"),
                "country": h.get("country"),
            }
    except LiteAPIError as exc:
        status["message"] = str(exc)
        status["ok"] = False

    return status


def lowest_total(rate_block: dict) -> tuple[float | None, str | None]:
    """Extract lowest display total from a hotel rates entry."""
    room_types = rate_block.get("roomTypes") or []
    best: float | None = None
    currency: str | None = None
    for rt in room_types:
        for rate in rt.get("rates") or []:
            totals = (rate.get("retailRate") or {}).get("total") or []
            if not totals:
                continue
            amount = totals[0].get("amount")
            cur = totals[0].get("currency")
            if amount is None:
                continue
            try:
                value = float(amount)
            except (TypeError, ValueError):
                continue
            if best is None or value < best:
                best = value
                currency = cur
    return best, currency


def first_offer_id(rate_block: dict) -> str | None:
    for rt in rate_block.get("roomTypes") or []:
        if rt.get("offerId"):
            return rt["offerId"]
        for rate in rt.get("rates") or []:
            if rate.get("offerId"):
                return rate["offerId"]
    return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_rate_rows(rate_block: dict, hotel: dict | None = None) -> list[dict[str, Any]]:
    """
    Flatten LiteAPI hotel rates into table rows:
    Room Details | Board Basis | Price (+ breakup / cancellation payloads).
    """
    hotel = hotel or {}
    room_meta: dict[str, dict[str, Any]] = {}
    for room_info in hotel.get("rooms") or []:
        key = str(room_info.get("id") or "")
        if not key:
            continue
        photos = room_info.get("photos") or []
        room_meta[key] = {
            "name": room_info.get("roomName") or "",
            "image": (photos[0].get("url") if photos else None),
        }

    rows: list[dict[str, Any]] = []
    for rt in rate_block.get("roomTypes") or []:
        offer_id = rt.get("offerId") or first_offer_id({"roomTypes": [rt]})
        offer_total = rt.get("offerRetailRate") or {}
        for rate in rt.get("rates") or []:
            mapped_id = str(rate.get("mappedRoomId") or "")
            meta = room_meta.get(mapped_id) or {}
            retail = rate.get("retailRate") or {}
            totals = retail.get("total") or [{}]
            amount = totals[0].get("amount")
            currency = totals[0].get("currency")
            if amount is None and offer_total.get("amount") is not None:
                amount = offer_total.get("amount")
                currency = offer_total.get("currency") or currency

            cancel = rate.get("cancellationPolicies") or {}
            tag = (cancel.get("refundableTag") or "").upper()
            taxes_raw = retail.get("taxesAndFees") or []
            taxes = []
            for tax in taxes_raw:
                taxes.append(
                    {
                        "description": tax.get("description") or tax.get("included") or "Fee",
                        "amount": tax.get("amount"),
                        "currency": tax.get("currency") or currency,
                        "included": bool(tax.get("included")),
                    }
                )

            cancel_policies = []
            for info in cancel.get("cancelPolicyInfos") or []:
                cancel_policies.append(
                    {
                        "cancel_time": info.get("cancelTime") or info.get("cancel_time") or "",
                        "amount": info.get("amount"),
                        "currency": info.get("currency") or currency,
                        "type": info.get("type") or "",
                        "timezone": info.get("timezone") or "",
                    }
                )

            room_name = (
                meta.get("name")
                or rate.get("name")
                or rt.get("name")
                or "Room"
            )
            board = rate.get("boardName") or rate.get("boardType") or "Room Only"
            amount_f = _safe_float(amount)
            rows.append(
                {
                    "offer_id": offer_id or rate.get("offerId"),
                    "room_key": mapped_id or room_name,
                    "room_name": room_name,
                    "image": meta.get("image"),
                    "board": board,
                    "board_type": rate.get("boardType") or "",
                    "occupancy_number": rate.get("occupancyNumber") or 1,
                    "amount": amount,
                    "amount_value": amount_f if amount_f is not None else 0.0,
                    "currency": currency or "",
                    "refundable": tag,
                    "is_refundable": tag == "RFN",
                    "refundable_label": (
                        "Refundable" if tag == "RFN"
                        else "Non-Refundable" if tag == "NRFN"
                        else (tag or "See policy")
                    ),
                    "available": True,
                    "taxes": taxes,
                    "cancel_policies": cancel_policies,
                    "hotel_remarks": cancel.get("hotelRemarks") or rate.get("remarks") or "",
                    "max_occupancy": rate.get("maxOccupancy") or rate.get("adultCount") or "",
                    "suggested_selling": (retail.get("suggestedSellingPrice") or {}).get("amount")
                    if isinstance(retail.get("suggestedSellingPrice"), dict)
                    else retail.get("suggestedSellingPrice"),
                }
            )

    rows.sort(key=lambda r: (r.get("amount_value") or 0.0, r.get("room_name") or ""))
    return rows

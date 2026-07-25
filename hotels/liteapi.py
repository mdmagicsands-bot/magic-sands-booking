"""LiteAPI / Nuitee Connect HTTP client (server-side only)."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


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

    def search_rates(
        self,
        *,
        checkin: str,
        checkout: str,
        adults: int = 2,
        children: list[int] | None = None,
        place_id: str | None = None,
        hotel_ids: list[str] | None = None,
        city_name: str | None = None,
        country_code: str | None = None,
        ai_search: str | None = None,
        currency: str | None = None,
        guest_nationality: str | None = None,
        max_rates_per_hotel: int | None = 1,
        include_hotel_data: bool = True,
        limit: int | None = 50,
    ) -> dict[str, Any]:
        occupancy: dict[str, Any] = {"adults": adults}
        if children:
            occupancy["children"] = children

        body: dict[str, Any] = {
            "occupancies": [occupancy],
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

        # Prefer city/country (most reliable in sandbox), then hotel IDs, AI, placeId.
        if city_name and country_code:
            body["cityName"] = city_name
            body["countryCode"] = country_code
        elif hotel_ids:
            body["hotelIds"] = hotel_ids
        elif ai_search:
            body["aiSearch"] = ai_search
        elif place_id:
            body["placeId"] = place_id
        elif city_name:
            body["cityName"] = city_name
        else:
            raise LiteAPIError(
                "Provide city_name+country_code, hotel_ids, ai_search, or place_id."
            )

        return self._request(
            "POST",
            f"{self.api_base}/hotels/rates",
            json=body,
            timeout=90,
        )


COUNTRY_NAME_TO_CODE = {
    "united arab emirates": "AE",
    "uae": "AE",
    "oman": "OM",
    "saudi arabia": "SA",
    "qatar": "QA",
    "bahrain": "BH",
    "kuwait": "KW",
    "united kingdom": "GB",
    "uk": "GB",
    "united states": "US",
    "usa": "US",
    "france": "FR",
    "italy": "IT",
    "spain": "ES",
    "germany": "DE",
    "turkey": "TR",
    "egypt": "EG",
    "india": "IN",
    "thailand": "TH",
    "singapore": "SG",
    "malaysia": "MY",
    "indonesia": "ID",
    "maldives": "MV",
    "georgia": "GE",
    "azerbaijan": "AZ",
}


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
    return None

    def prebook(self, offer_id: str) -> dict[str, Any]:
        payload = self._request(
            "POST",
            f"{self.book_base}/rates/prebook",
            json={"usePaymentSdk": True, "offerId": offer_id},
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

    def get_booking(self, booking_id: str) -> dict[str, Any]:
        payload = self._request(
            "GET",
            f"{self.book_base}/bookings/{booking_id}",
            timeout=30,
        )
        return payload.get("data") or payload


def get_client() -> LiteAPIClient:
    return LiteAPIClient()


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

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .liteapi import (
    NATIONALITY_CHOICES,
    SEARCH_MARKET_COUNTRY_CODES,
    SEARCH_MARKET_COUNTRY_ORDER,
    LiteAPIError,
    build_rate_rows,
    country_code_from_address,
    first_offer_id,
    get_client,
    hotel_country_code,
    is_search_market_country,
    lowest_total,
    normalize_nationality,
    normalize_occupancies,
    occupancy_totals,
    parse_occupancies_from_request,
)


def _default_dates() -> tuple[str, str]:
    checkin = date.today()
    checkout = checkin + timedelta(days=1)
    return checkin.isoformat(), checkout.isoformat()


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _normalize_board_code(board_type: str = "", board_name: str = "") -> str:
    """Map LiteAPI boardType / boardName to RO|BB|HB|FB|AI."""
    raw = (board_type or "").strip().upper()
    if raw:
        # BB1 / HB2 / AI3 → base code; TI is all-inclusive alias.
        base = "".join(ch for ch in raw if ch.isalpha())
        if base == "TI":
            return "AI"
        if base in {"RO", "BB", "HB", "FB", "AI"}:
            return base
    name = (board_name or "").strip().lower()
    if not name:
        return ""
    if "all inclusive" in name or "all-inclusive" in name:
        return "AI"
    if "full board" in name:
        return "FB"
    if "half board" in name:
        return "HB"
    if "breakfast" in name or name in {"bb", "bed and breakfast"}:
        return "BB"
    if "room only" in name or name in {"ro", "room-only"}:
        return "RO"
    return ""


def _has_free_cancellation(cancel: dict) -> bool:
    tag = (cancel.get("refundableTag") or "").upper()
    if tag != "RFN":
        return False
    infos = cancel.get("cancelPolicyInfos") or []
    if not infos:
        return True
    for info in infos:
        try:
            amount = float(info.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0
        if amount <= 0:
            return True
    return False


def _infer_property_type(meta: dict, name: str = "") -> str:
    raw = (
        meta.get("hotelType")
        or meta.get("hotel_type")
        or meta.get("type")
        or meta.get("propertyType")
        or ""
    )
    blob = f"{raw} {name}".lower()
    if any(k in blob for k in ("resort", "resort spa")):
        return "resort"
    if any(k in blob for k in ("apartment", "apart-hotel", "aparthotel", "apartments")):
        return "apartment"
    if "villa" in blob:
        return "villa"
    if any(k in blob for k in ("camp", "glamping", "tent")):
        return "camp"
    return "hotel"


def _facility_blob(meta: dict) -> str:
    parts: list[str] = []
    for fac in meta.get("hotelFacilities") or []:
        if isinstance(fac, str):
            parts.append(fac)
        elif isinstance(fac, dict):
            parts.append(str(fac.get("name") or ""))
    for fac in meta.get("facilities") or []:
        if isinstance(fac, dict):
            parts.append(str(fac.get("name") or ""))
        elif isinstance(fac, str):
            parts.append(fac)
    return " | ".join(p for p in parts if p).lower()


_AMENITY_MATCHERS = {
    "pool": ("pool", "swimming"),
    "beach": ("beach", "private beach", "beachfront"),
    "spa": ("spa", "wellness"),
    "gym": ("gym", "fitness", "fitness centre", "fitness center"),
    "wifi": ("wifi", "wi-fi", "wireless internet"),
    "parking": ("parking", "car park"),
    "restaurant": ("restaurant", "dining"),
}


def _match_amenities(facilities_text: str) -> list[str]:
    if not facilities_text:
        return []
    found = []
    for key, needles in _AMENITY_MATCHERS.items():
        if any(n in facilities_text for n in needles):
            found.append(key)
    return found


# Higher weight = more distinctive for the summary checkmark row.
_HIGHLIGHT_FEATURE_WEIGHTS: list[tuple[int, str, tuple[str, ...]]] = [
    (100, "Private Beach", ("private beach", "beachfront", "beach access")),
    (96, "Infinity Pool", ("infinity pool",)),
    (94, "Outdoor Pool", ("outdoor pool", "rooftop pool")),
    (92, "Indoor Pool", ("indoor pool",)),
    (90, "Swimming Pool", ("swimming pool", " pool")),
    (88, "Spa & Wellness", ("spa and wellness", "spa ", "wellness centre", "wellness center", "hammam", "sauna")),
    (86, "Kids Club", ("kids club", "children's club", "childrens club", "kids' club")),
    (84, "Water Park", ("water park", "waterpark")),
    (82, "Tennis Court", ("tennis",)),
    (80, "Golf", ("golf",)),
    (78, "Diving", ("diving", "snorkel")),
    (76, "Fitness Centre", ("fitness", "gym")),
    (74, "Yoga", ("yoga",)),
    (72, "Restaurant", ("restaurant",)),
    (70, "Bar", (" bar", "lounge bar", "rooftop bar")),
    (68, "Room Service", ("room service",)),
    (66, "Business Centre", ("business centre", "business center", "meeting room", "conference")),
    (64, "Airport Shuttle", ("airport shuttle", "airport transfer")),
    (62, "Family Rooms", ("family room", "family rooms")),
    (60, "Sea View", ("sea view", "ocean view", "pool view")),
    (58, "Balcony", ("balcony", "terrace")),
    (56, "Pet Friendly", ("pets allowed", "pet friendly", "pets are allowed")),
    (54, "EV Charging", ("ev charging", "electric vehicle")),
    (52, "Valet Parking", ("valet parking",)),
    (50, "Free Parking", ("free parking", "free self parking")),
    (48, "Parking", ("parking", "car park")),
    (46, "Accessible", ("wheelchair", "accessible", "disability")),
    (40, "Free WiFi", ("free wifi", "free wi-fi", "wifi available in all")),
]

_HIGHLIGHT_SKIP = (
    "non-smoking",
    "air conditioning",
    "heating",
    "lift",
    "elevator",
    "fax",
    "newspaper",
    "safety deposit",
    "smoke detector",
    "fire extinguisher",
    "cctv",
    "24-hour front desk",
    "front desk",
    "wakeup",
    "wake-up",
    "luggage",
    "ticket service",
    "currency exchange",
    "vending",
    "iron",
    "laundry",
    "dry cleaning",
    "daily housekeeping",
    "soundproof",
    "fan",
    "desk",
    "telephone",
    "tv",
    "satellite",
    "cable channels",
    "minibar",
    "fridge",
    "coffee machine",
    "kettle",
    "towels",
    "linens",
    "slippers",
    "bathrobe",
    "hairdryer",
    "toiletries",
    "shower",
    "bathtub",
    "bidet",
    "toilet",
    "socket",
    "adapter",
    "alarm clock",
    "wardrobe",
    "closet",
    "carpeted",
    "tile/marble",
    "hardwood",
    "hypoallergenic",
    "extra long beds",
    "screens / barriers",
    "barrier",
    "coronavirus",
    "covid",
    "hand sanitizer",
    "face mask",
    "social distancing",
    "staff follow",
    "guest accommodation is disinfected",
    "linens, towels and laundry",
    "physical distancing",
    "cashless",
    "contactless",
    "first aid kit",
)


def _normalize_highlight_label(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    cleaned = cleaned.replace("&amp;", "&")
    if not cleaned:
        return ""
    # Keep short facility names readable; trim noisy measurements.
    cleaned = re.sub(r"\s*[-–]\s*\d+(\.\d+)?\s*(cm|m|ft|feet|meters?).*$", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*\(\d+.*$", "", cleaned)
    if len(cleaned) > 32:
        cleaned = cleaned[:29].rsplit(" ", 1)[0] + "…"
    return cleaned


def _pick_highlight_amenities(facility_names: list[str], limit: int = 5) -> list[str]:
    """
    Pick distinctive, hotel-specific amenity labels for the summary checkmark row.
    Prefers rarer features from this hotel's own facility list over a fixed Parking→Spa checklist.
    """
    if not facility_names:
        return []

    scored: list[tuple[int, int, str]] = []  # weight, original index, label
    used_keys: set[str] = set()

    for idx, raw in enumerate(facility_names):
        name = (raw or "").strip()
        if not name:
            continue
        low = name.lower()
        if any(skip in low for skip in _HIGHLIGHT_SKIP):
            continue

        weight = 0
        canonical = ""
        for w, label, needles in _HIGHLIGHT_FEATURE_WEIGHTS:
            if any(n in low for n in needles):
                weight = w
                canonical = label
                break

        # Unmatched but specific-looking facilities still qualify at mid weight.
        if weight == 0:
            if len(name) < 4 or len(name) > 48:
                continue
            if low.count(" ") == 0 and low in {"wifi", "parking", "restaurant", "bar", "gym", "spa"}:
                weight = 35
                canonical = name.title()
            elif any(ch.isdigit() for ch in name):
                # Skip measurement-heavy noise unless already matched.
                continue
            else:
                weight = 42
                canonical = _normalize_highlight_label(name)
        else:
            # Prefer the hotel's own wording when short/clear; else canonical label.
            own = _normalize_highlight_label(name)
            canonical = own if 4 <= len(own) <= 28 else canonical

        if not canonical:
            continue
        key = canonical.lower()
        # Collapse near-duplicates (Free Parking / Parking).
        dedupe_key = key
        for stem in ("parking", "pool", "wifi", "wi-fi", "spa", "fitness", "gym", "restaurant", "beach"):
            if stem in key:
                dedupe_key = stem
                break
        if dedupe_key in used_keys:
            continue
        used_keys.add(dedupe_key)
        scored.append((weight, idx, canonical))

    scored.sort(key=lambda t: (-t[0], t[1]))
    picks = [label for _, _, label in scored[:limit]]

    # If still short, fill from remaining real names (still skip boring ones).
    if len(picks) < limit:
        have = {p.lower() for p in picks}
        for raw in facility_names:
            label = _normalize_highlight_label(raw)
            low = label.lower()
            if not label or low in have:
                continue
            if any(skip in low for skip in _HIGHLIGHT_SKIP):
                continue
            picks.append(label)
            have.add(low)
            if len(picks) >= limit:
                break
    return picks


def _infer_promotions(rate: dict, room_type: dict) -> list[str]:
    promos: list[str] = []
    rate_type = (rate.get("rateType") or room_type.get("rateType") or "").lower()
    if rate_type == "package":
        promos.append("special")
    remarks = " ".join(
        str(x)
        for x in [
            rate.get("remarks") or "",
            " ".join(str(r) for r in ((rate.get("cancellationPolicies") or {}).get("hotelRemarks") or [])),
        ]
    ).lower()
    if any(k in remarks for k in ("early bird", "early-bird", "advance purchase")):
        promos.append("early_bird")
    if any(k in remarks for k in ("last minute", "last-minute", "late deal")):
        promos.append("last_minute")
    if any(k in remarks for k in ("special offer", "promo", "promotion", "deal")):
        if "special" not in promos:
            promos.append("special")
    return promos


def _cheapest_rate_meta(rate_block: dict) -> dict:
    """Pull board / refundable / room name from the cheapest offer."""
    best: dict = {
        "board": "",
        "board_code": "",
        "refundable": "",
        "free_cancellation": False,
        "room_name": "",
        "offer_id": None,
        "supplier": "api",
        "promotions": [],
    }
    best_price: float | None = None
    for rt in rate_block.get("roomTypes") or []:
        offer_id = rt.get("offerId")
        supplier_raw = str(rt.get("supplier") or "").strip().lower()
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
            board_name = rate.get("boardName") or ""
            board_type = rate.get("boardType") or ""
            # Direct-style inventory when supplier is clearly not the aggregator.
            supplier = "direct" if supplier_raw and supplier_raw not in {"nuitee", "liteapi", "api"} else "api"
            best = {
                "board": board_name or board_type or "",
                "board_code": _normalize_board_code(board_type, board_name),
                "refundable": cancel.get("refundableTag") or "",
                "free_cancellation": _has_free_cancellation(cancel),
                "room_name": rate.get("name") or "",
                "offer_id": offer_id or rate.get("offerId"),
                "supplier": supplier,
                "promotions": _infer_promotions(rate, rt),
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


def _guest_rating_label(score: float | None) -> str:
    """Map 0–10 guest score to a short TBO-style label."""
    if score is None:
        return ""
    if score >= 9:
        return "Excellent"
    if score >= 8:
        return "Very Good"
    if score >= 7:
        return "Good"
    if score >= 6:
        return "Pleasant"
    return "Fair"


# Caption keywords → TBO-style gallery filter labels (LiteAPI has captions, not categories).
_GALLERY_CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Exterior", ("exterior", "building", "facade", "façade", "outside", "entrance", "aerial", "view of hotel")),
    ("Lobby", ("lobby", "reception", "front desk", "atrium", "concierge")),
    ("Leisure & Recreation", ("pool", "swimming", "beach", "recreation", "leisure", "kids club", "playground", "tennis", "golf")),
    ("Dining & Bars", ("restaurant", "dining", "bar", "cafe", "café", "breakfast", "lounge", "food", "buffet")),
    ("Health & Wellness", ("spa", "wellness", "fitness", "gym", "sauna", "massage", "health")),
    ("Meeting & Event Spaces", ("meeting", "conference", "ballroom", "event", "banquet", "boardroom")),
    ("Guest Rooms & Amenities", ("room", "suite", "bedroom", "bathroom", "guest room", "bed", "balcony")),
    ("Property Amenities", ("amenity", "parking", "garden", "terrace", "rooftop", "corridor", "elevator")),
]


def _gallery_category_from_caption(caption: str) -> str:
    text = (caption or "").strip().lower()
    if not text:
        return "Property Amenities"
    for label, needles in _GALLERY_CATEGORY_RULES:
        if any(n in text for n in needles):
            return label
    return "Property Amenities"


def _build_gallery_items(images: list) -> list[dict]:
    """Normalize LiteAPI hotelImages into gallery items with category filters."""
    items: list[dict] = []
    for idx, raw in enumerate(images or []):
        if not isinstance(raw, dict):
            continue
        url = raw.get("url") or raw.get("imageHdUrl") or raw.get("thumbnailUrl")
        if not url:
            continue
        caption = (raw.get("caption") or raw.get("category") or "").strip()
        category = _gallery_category_from_caption(caption)
        items.append(
            {
                "url": url,
                "thumb": raw.get("thumbnailUrl") or url,
                "caption": caption.title() if caption else category,
                "category": category,
                "default": bool(raw.get("defaultImage")),
                "order": raw.get("order") if raw.get("order") is not None else idx,
            }
        )
    items.sort(key=lambda x: (0 if x["default"] else 1, x["order"]))
    return items


def _strip_html_keep_text(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html or "", flags=re.I)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return re.sub(r"[ \t]{2,}", " ", text).strip()


def _parse_hotel_detail_sections(description_html: str) -> list[dict]:
    """
    Split LiteAPI hotelDescription into TBO-style labeled sections.
    LiteAPI often uses <strong>Title</strong> headings inside HTML paragraphs.
    """
    html = (description_html or "").strip()
    if not html:
        return []

    # Prefer strong-tagged headings.
    parts = re.split(r"<strong[^>]*>\s*([^<]+?)\s*</strong>", html, flags=re.I)
    sections: list[dict] = []
    if len(parts) >= 3:
        # parts[0] = preamble before first strong (often empty)
        preamble = _strip_html_keep_text(parts[0])
        if preamble:
            sections.append({"title": "Hotel Overview", "body": preamble, "is_list": False})
        for i in range(1, len(parts) - 1, 2):
            title = re.sub(r"\s+", " ", parts[i]).strip().rstrip(":")
            body = _strip_html_keep_text(parts[i + 1])
            if not title or not body:
                continue
            # Bullet-ish bodies (lines starting with - or •)
            lines = [ln.strip(" •-\t") for ln in body.split("\n") if ln.strip()]
            is_list = len(lines) >= 2 and all(len(ln) < 180 for ln in lines[:6]) and (
                body.count("\n") >= 1 or " - " in body
            )
            # Only treat as list when content looks like discrete short items.
            if is_list and len(lines) >= 2 and sum(1 for ln in lines if len(ln) < 90) >= max(2, len(lines) // 2):
                sections.append({"title": title, "items": lines, "is_list": True})
            else:
                sections.append({"title": title, "body": body, "is_list": False})
        return sections

    plain = _strip_html_keep_text(html)
    if plain:
        return [{"title": "Hotel Overview", "body": plain, "is_list": False}]
    return []


# Keyword → TBO-like amenity category (order matters; first match wins).
_AMENITY_CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Accessibility", ("accessib", "wheelchair", "disabled", "elevator door", "braille", "hearing")),
    ("Internet", ("wifi", "wi-fi", "wireless", "internet")),
    ("Parking", ("parking", "garage", "valet")),
    ("Pets", ("pet", "dog", "cat")),
    ("Pool", ("pool", "swim", "cabana", "infinity pool")),
    ("Beach", ("beach", "beachfront")),
    ("Spa/Wellness", ("spa", "sauna", "steam", "hammam", "massage", "wellness", "hot tub", "jacuzzi")),
    ("Health And Wellness", ("fitness", "gym", "yoga", "aerobics", "beauty", "health")),
    ("Food and Drinks", ("restaurant", "bar", "cafe", "café", "breakfast", "dining", "wine", "champagne", "meal", "drink")),
    ("Room Service", ("room service",)),
    ("Family And Children", ("family", "child", "kids", "babysit", "crib", "playground")),
    ("Business and conference", ("meeting", "conference", "business", "banquet", "boardroom")),
    ("Transportation and shuttles", ("shuttle", "airport transfer", "taxi", "car hire", "transport")),
    ("Water-Based Activities", ("snorkel", "diving", "boat", "canoe", "windsurf", "kayak", "water sport")),
    ("Adventure activities", ("hiking", "horse", "cave", "bowling", "cycling", "climbing")),
    ("Sports Facility", ("tennis", "golf", "sport", "court")),
    ("Outdoor Areas", ("garden", "terrace", "rooftop", "picnic", "patio", "balcony")),
    ("Shopping", ("shop", "boutique", "store", "souvenir")),
    ("Romantic", ("couple", "honeymoon", "romantic")),
    ("Entertainment and Tech", ("tv", "entertainment", "nightclub", "dj", "karaoke", "game", "cctv", "security")),
    ("Games and Entertainment", ("game room", "billiard", "casino", "evening entertainment")),
    ("Health and Safety", ("first aid", "sanitizer", "face mask", "cleaning chemical", "coronavirus", "hygiene", "smoke alarm", "fire extinguisher")),
    ("Guest facilities and services", (
        "front desk", "concierge", "laundry", "dry cleaning", "luggage", "currency", "atm",
        "multilingual", "newspaper", "tour desk", "wake-up", "express check", "lockers",
    )),
    ("Basic Facility", ("air conditioning", "non-smoking", "lift", "elevator", "heating", "soundproof", "fan")),
]


def _group_amenities(facility_names: list[str]) -> list[dict]:
    """Group flat LiteAPI facility strings into categorized columns for TBO-style UI."""
    buckets: dict[str, list[str]] = {}
    for raw in facility_names or []:
        name = (raw or "").strip()
        if not name:
            continue
        low = name.lower()
        cat = "Other"
        for label, needles in _AMENITY_CATEGORY_RULES:
            if any(n in low for n in needles):
                cat = label
                break
        bucket = buckets.setdefault(cat, [])
        if name not in bucket:
            bucket.append(name)

    # Stable display order: known categories first, then Other.
    order = [c for c, _ in _AMENITY_CATEGORY_RULES] + ["Other"]
    grouped: list[dict] = []
    for cat in order:
        items = buckets.get(cat)
        if items:
            grouped.append({"category": cat, "items": items})
    return grouped


def _policy_bullets(hotel: dict, times: dict) -> list[str]:
    bullets: list[str] = []
    cin = (
        times.get("checkin")
        or times.get("checkinStart")
        or times.get("checkin_start")
        or ""
    )
    cout = (
        times.get("checkout")
        or times.get("checkoutEnd")
        or times.get("checkout_end")
        or ""
    )
    if cin:
        bullets.append(f"Check-in from {cin}")
    if cout:
        bullets.append(f"Check-out by {cout}")
    important = _strip_html_keep_text(hotel.get("hotelImportantInformation") or "")
    if important:
        for chunk in re.split(r"(?<=[.!?])\s+|\n+", important):
            chunk = chunk.strip()
            if chunk:
                bullets.append(chunk)
    policies = hotel.get("policies")
    if isinstance(policies, dict):
        for key, val in policies.items():
            text = _strip_html_keep_text(str(val or ""))
            if text:
                label = re.sub(r"[_-]+", " ", str(key)).strip().title()
                bullets.append(f"{label}: {text}")
    elif isinstance(policies, list):
        for item in policies:
            if isinstance(item, str) and item.strip():
                bullets.append(item.strip())
            elif isinstance(item, dict):
                text = item.get("description") or item.get("text") or item.get("name")
                if text:
                    bullets.append(str(text).strip())
    # Dedupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for b in bullets:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out[:12]


def _score_to_five(value) -> float | None:
    """Normalize LiteAPI 0–10 (or already 0–5) scores to one decimal /5."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if num > 5:
        num = num / 2.0
    return round(max(0.0, min(5.0, num)), 1)


def _traveler_bucket(raw_type: str) -> str:
    text = (raw_type or "").strip().lower()
    if not text:
        return "Other"
    if "family" in text or "child" in text:
        return "Families"
    if "couple" in text:
        return "Couples"
    if "solo" in text or "single" in text:
        return "Solo"
    if "group" in text or "friends" in text:
        return "Groups"
    if "business" in text:
        return "Business"
    return "Other"


def _build_reviews_context(client, hotel_id: str, hotel: dict) -> dict:
    """Fetch LiteAPI reviews + sentiment; degrade gracefully if unavailable."""
    reviews_raw: list = []
    sentiment: dict = {}
    try:
        payload = client.get_reviews(hotel_id, limit=40, get_sentiment=True)
        reviews_raw = payload.get("data") or []
        if not isinstance(reviews_raw, list):
            reviews_raw = []
        sentiment = (
            payload.get("sentimentAnalysis")
            or payload.get("sentiment_analysis")
            or {}
        )
        if not isinstance(sentiment, dict):
            sentiment = {}
    except LiteAPIError:
        reviews_raw = []
        sentiment = {}

    # Prefer live reviews sentiment; fall back to hotel payload if present.
    if not sentiment:
        fallback = hotel.get("sentiment_analysis") or hotel.get("sentimentAnalysis") or {}
        if isinstance(fallback, dict):
            sentiment = fallback

    review_items: list[dict] = []
    type_counts: dict[str, int] = {}
    score_sum = 0.0
    score_n = 0
    for raw in reviews_raw:
        if not isinstance(raw, dict):
            continue
        score5 = _score_to_five(raw.get("averageScore") or raw.get("score") or raw.get("rating"))
        traveler = _traveler_bucket(str(raw.get("type") or raw.get("travelerType") or ""))
        type_counts[traveler] = type_counts.get(traveler, 0) + 1
        if score5 is not None:
            score_sum += score5
            score_n += 1
        date_raw = str(raw.get("date") or "")[:10]
        review_items.append(
            {
                "name": (raw.get("name") or "Guest").strip() or "Guest",
                "headline": (raw.get("headline") or "").strip(),
                "pros": (raw.get("pros") or "").strip(),
                "cons": (raw.get("cons") or "").strip(),
                "score": score5,
                "traveler": traveler,
                "country": (raw.get("country") or "").upper(),
                "date": date_raw,
                "language": (raw.get("language") or "en").lower(),
            }
        )

    total = len(review_items)
    traveler_tabs = [{"key": "All", "label": "All", "pct": 100 if total else 0, "count": total}]
    for key in ("Couples", "Families", "Solo", "Groups", "Business", "Other"):
        count = type_counts.get(key, 0)
        if not count:
            continue
        traveler_tabs.append(
            {
                "key": key,
                "label": key,
                "count": count,
                "pct": int(round((count / total) * 100)) if total else 0,
            }
        )

    categories: list[dict] = []
    for cat in sentiment.get("categories") or []:
        if not isinstance(cat, dict):
            continue
        name = (cat.get("name") or "").strip()
        score5 = _score_to_five(cat.get("rating") or cat.get("score"))
        if not name or score5 is None:
            continue
        categories.append(
            {
                "name": name,
                "score": score5,
                "pct": int(round((score5 / 5.0) * 100)),
                "description": (cat.get("description") or "").strip(),
            }
        )
    categories.sort(key=lambda c: c["score"], reverse=True)

    pros = [str(p).strip() for p in (sentiment.get("pros") or []) if str(p).strip()][:8]
    cons = [str(c).strip() for c in (sentiment.get("cons") or []) if str(c).strip()][:6]

    avg_from_reviews = round(score_sum / score_n, 1) if score_n else None
    hotel_score5 = _score_to_five(hotel.get("rating"))
    overall = avg_from_reviews or hotel_score5
    overall_label = _guest_rating_label(overall * 2 if overall is not None else None) if overall is not None else ""

    # Short narrative from top category blurbs / pros.
    summary_bits = [c["description"] for c in categories[:3] if c.get("description")]
    if not summary_bits and pros:
        summary_bits = [f"Guests often mention: {', '.join(pros[:5])}."]
    narrative = " ".join(summary_bits[:2])
    if len(narrative) > 320:
        narrative = narrative[:317].rsplit(" ", 1)[0] + "…"

    hotel_count = hotel.get("reviewCount") or hotel.get("review_count")
    try:
        hotel_count_i = int(hotel_count) if hotel_count not in (None, "") else total
    except (TypeError, ValueError):
        hotel_count_i = total

    return {
        "guest_reviews": review_items,
        "review_traveler_tabs": traveler_tabs,
        "review_categories": categories,
        "review_pros": pros,
        "review_cons": cons,
        "review_overall": overall,
        "review_overall_label": overall_label or _guest_rating_label(hotel.get("rating")),
        "review_narrative": narrative,
        "review_fetched_count": total,
        "review_summary_count": hotel_count_i or total,
        "has_guest_reviews": bool(review_items or categories or overall),
    }


def _build_nightly_fares(checkin: str, checkout: str, total: float | None) -> list[dict]:
    """Split stay total into per-night rows for the rate breakup modal."""
    start = _parse_date(checkin)
    end = _parse_date(checkout)
    if not start or not end or end <= start or total is None or total <= 0:
        return []
    nights = (end - start).days
    if nights <= 0:
        return []
    per_night = round(total / nights, 2)
    items: list[dict] = []
    allocated = 0.0
    for i in range(nights):
        day = start + timedelta(days=i)
        if i == nights - 1:
            amount = round(total - allocated, 2)
        else:
            amount = per_night
            allocated += amount
        items.append(
            {
                "date": day.isoformat(),
                "date_label": day.strftime("%d %b, %a"),
                "amount": amount,
            }
        )
    return items


def _board_basis_label(board: str, board_type: str = "") -> str:
    board = (board or "Room Only").strip()
    code = (board_type or board).strip()
    if code and code.lower() != board.lower():
        return f"{board} - {board} ({code})"
    return f"{board} - {board} ({board})"


def _hotel_coords(meta: dict) -> tuple[float | None, float | None]:
    loc = meta.get("location") if isinstance(meta.get("location"), dict) else {}
    lat = meta.get("latitude") or loc.get("latitude")
    lng = meta.get("longitude") or loc.get("longitude")
    try:
        lat_f = float(lat) if lat is not None and lat != "" else None
    except (TypeError, ValueError):
        lat_f = None
    try:
        lng_f = float(lng) if lng is not None and lng != "" else None
    except (TypeError, ValueError):
        lng_f = None
    return lat_f, lng_f


def _photo_count(meta: dict) -> int:
    images = meta.get("hotelImages") or meta.get("hotel_images") or []
    if isinstance(images, list) and images:
        return len([i for i in images if (isinstance(i, dict) and i.get("url")) or isinstance(i, str)])
    if meta.get("main_photo") or meta.get("mainPhoto") or meta.get("thumbnail"):
        return 1
    return 0


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

        cc = hotel_country_code(meta) or hotel_country_code(rate_block.get("hotel") or {})
        hotel_name = meta.get("name") or rate_block.get("hotelName") or hotel_id
        facilities_text = _facility_blob(meta)
        refund_tag = (rate_meta.get("refundable") or "").upper()
        lat, lng = _hotel_coords(meta)
        photo_count = _photo_count(meta)
        # Normalize review to a 0–100 display score when API returns 0–10.
        review_display = None
        if review_score is not None:
            review_display = int(round(review_score * 10)) if review_score <= 10 else int(round(review_score))
        cards.append(
            {
                "hotel_id": hotel_id,
                "name": hotel_name,
                "photo": photo,
                "photo_count": photo_count,
                "extra_photos": max(0, photo_count - 1),
                "address": meta.get("address")
                or meta.get("formattedAddress")
                or ", ".join(
                    x
                    for x in [meta.get("city_name") or meta.get("city"), meta.get("country_code")]
                    if x
                ),
                "city": meta.get("city_name") or meta.get("city") or "",
                "country_code": cc or "",
                "stars": stars or 0,
                "review_score": review_score,
                "review_display": review_display,
                "guest_rating_label": _guest_rating_label(review_score),
                "review_count": meta.get("review_count") or meta.get("reviewCount"),
                "lat": lat,
                "lng": lng,
                "price": price,
                "currency": currency or "USD",
                "board": rate_meta["board"],
                "board_code": rate_meta.get("board_code") or "",
                "refundable": rate_meta["refundable"],
                "is_refundable": refund_tag == "RFN",
                "is_non_refundable": refund_tag == "NRFN",
                "free_cancellation": bool(rate_meta.get("free_cancellation")),
                "room_name": rate_meta["room_name"],
                "offer_id": rate_meta.get("offer_id"),
                "property_type": _infer_property_type(meta, str(hotel_name)),
                "amenities": _match_amenities(facilities_text),
                "availability": "instant" if price is not None else "on_request",
                "promotions": rate_meta.get("promotions") or [],
                "supplier": rate_meta.get("supplier") or "api",
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
            if not card.get("lat") or not card.get("lng"):
                nlat, nlng = _hotel_coords(nested)
                if nlat is not None:
                    card["lat"] = nlat
                if nlng is not None:
                    card["lng"] = nlng
            if not card.get("photo_count"):
                card["photo_count"] = _photo_count(nested)
                card["extra_photos"] = max(0, (card["photo_count"] or 0) - 1)

    # Restrict inventory to GCC + Egypt.
    cards = [
        c
        for c in cards
        if is_search_market_country(c.get("country_code"))
        or is_search_market_country(country_code_from_address(c.get("address") or ""))
    ]
    cards.sort(key=lambda c: (c["price"] is None, c["price"] or 0))
    return cards


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    import math

    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def _pick_choice_hotel(
    cards: list[dict],
    *,
    hotel_id: str,
    destination: str,
    hotel_matches: list[dict] | None,
) -> dict | None:
    if not cards:
        return None
    if hotel_id:
        for card in cards:
            if str(card.get("hotel_id")) == str(hotel_id):
                return card
    if hotel_matches:
        primary_id = str(hotel_matches[0].get("id") or hotel_matches[0].get("hotelId") or "")
        for card in cards:
            if str(card.get("hotel_id")) == primary_id:
                return card
    dest_l = (destination or "").strip().lower()
    if dest_l:
        for card in cards:
            name_l = (card.get("name") or "").lower()
            if dest_l == name_l or (len(dest_l) >= 4 and dest_l in name_l):
                return card
        for card in cards:
            name_l = (card.get("name") or "").lower()
            if name_l in dest_l:
                return card
    return cards[0] if len(cards) == 1 else None


def _is_direct_hotel_search(
    *,
    hotel_id: str,
    place_id: str,
    hotel_matches: list[dict] | None,
    destination: str,
    cards: list[dict],
) -> bool:
    if place_id:
        return False
    if hotel_id or hotel_matches:
        return True
    choice = _pick_choice_hotel(
        cards,
        hotel_id=hotel_id,
        destination=destination,
        hotel_matches=hotel_matches,
    )
    if not choice:
        return False
    dest_l = (destination or "").strip().lower()
    name_l = (choice.get("name") or "").lower()
    if dest_l and (dest_l == name_l or dest_l in name_l or name_l in dest_l):
        return True
    return _looks_like_hotel_query(destination)


def organize_hotel_search_results(
    client,
    cards: list[dict],
    *,
    hotel_id: str,
    place_id: str,
    destination: str,
    hotel_matches: list[dict] | None,
    rate_kwargs: dict,
) -> dict:
    """When the partner searched a hotel by name, split results into choice / recommended / nearby."""
    empty = {
        "hotel_search_mode": False,
        "choice_hotel": None,
        "choice_hotel_name": "",
        "recommended_hotels": [],
        "nearby_hotels": [],
        "cards": cards,
    }
    if not _is_direct_hotel_search(
        hotel_id=hotel_id,
        place_id=place_id,
        hotel_matches=hotel_matches,
        destination=destination,
        cards=cards,
    ):
        return empty

    choice = _pick_choice_hotel(
        cards,
        hotel_id=hotel_id,
        destination=destination,
        hotel_matches=hotel_matches,
    )
    if not choice:
        return empty

    choice_id = str(choice["hotel_id"])
    pool: list[dict] = [c for c in cards if str(c.get("hotel_id")) != choice_id]
    city = (choice.get("city") or "").strip()
    country_code = (choice.get("country_code") or "").strip().upper()

    if city and country_code:
        try:
            payload = client.search_rates(
                city_name=city,
                country_code=country_code,
                limit=40,
                **rate_kwargs,
            )
            seen = {choice_id}
            for card in _build_cards(payload):
                cid = str(card.get("hotel_id"))
                if cid in seen:
                    continue
                seen.add(cid)
                pool.append(card)
        except LiteAPIError:
            pass

    pool = [c for c in pool if str(c.get("hotel_id")) != choice_id]

    recommended = sorted(
        pool,
        key=lambda c: (
            -(c.get("review_score") or 0),
            c.get("price") is None,
            c.get("price") or 999999,
        ),
    )[:6]

    recommended_ids = {str(c["hotel_id"]) for c in recommended}
    nearby_pool = [c for c in pool if str(c.get("hotel_id")) not in recommended_ids]

    clat, clng = choice.get("lat"), choice.get("lng")
    nearby: list[dict] = []
    if clat is not None and clng is not None:
        for card in nearby_pool:
            if card.get("lat") is None or card.get("lng") is None:
                continue
            enriched = dict(card)
            enriched["distance_km"] = round(
                _haversine_km(float(clat), float(clng), float(card["lat"]), float(card["lng"])),
                1,
            )
            nearby.append(enriched)
        nearby.sort(key=lambda c: c.get("distance_km", 999))
        nearby = nearby[:8]
    else:
        nearby = nearby_pool[:8]

    total = 1 + len(recommended) + len(nearby)
    return {
        "hotel_search_mode": True,
        "choice_hotel": choice,
        "choice_hotel_name": choice.get("name") or destination,
        "recommended_hotels": recommended,
        "nearby_hotels": nearby,
        "cards": [],
        "result_count": total,
    }


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


# Nuitee /data/hotels rejects hotelName without a geo scope (country/place/etc).
# Markets: GCC + Egypt only.
_HOTEL_NAME_COUNTRY_CODES = SEARCH_MARKET_COUNTRY_ORDER
_AUTOCOMPLETE_CACHE_TTL = 120


def _hotel_suggestion(h: dict) -> dict | None:
    hotel_id = str(h.get("id") or h.get("hotelId") or "").strip()
    name = (h.get("name") or "").strip()
    if not hotel_id or not name:
        return None
    city = h.get("city") or h.get("cityName") or ""
    country = (h.get("country") or h.get("countryCode") or "").strip()
    address = h.get("address") or ", ".join(x for x in [city, country] if x)
    cc = country_code_from_address(address) or (
        country[:2].upper() if len(country) >= 2 else ""
    )
    return {
        "type": "hotel",
        "hotelId": hotel_id,
        "placeId": "",
        "displayName": name,
        "formattedAddress": address,
        "countryCode": cc,
    }


def _looks_like_hotel_query(q: str) -> bool:
    """Heuristic: multi-word / hotel keywords → hotel lookup; short city names skip it."""
    text = (q or "").strip().lower()
    if len(text) >= 18:
        return True
    tokens = [t for t in text.replace(",", " ").split() if t]
    if len(tokens) >= 3:
        return True
    hotel_words = (
        "hotel", "resort", "anantara", "hilton", "marriott", "hyatt",
        "rixos", "atlantis", "palace", "suites", "inn", "motel",
    )
    return any(w in text for w in hotel_words)


def _preferred_hotel_countries(prefer_country: str | None = None) -> tuple[str, ...]:
    prefer = (prefer_country or "").strip().upper()[:2]
    ordered: list[str] = []
    if prefer and prefer in SEARCH_MARKET_COUNTRY_CODES:
        ordered.append(prefer)
    for cc in _HOTEL_NAME_COUNTRY_CODES:
        if cc not in ordered:
            ordered.append(cc)
    return tuple(ordered)


def _in_search_market_suggestion(item: dict) -> bool:
    cc = (item.get("countryCode") or "").strip().upper()[:2]
    if is_search_market_country(cc):
        return True
    return is_search_market_country(
        country_code_from_address(item.get("formattedAddress") or item.get("displayName") or "")
    )


def lookup_hotels_by_name(
    client,
    hotel_name: str,
    *,
    limit_per_country: int = 4,
    prefer_country: str | None = None,
    max_countries: int | None = None,
    timeout: int = 12,
    max_results: int = 8,
) -> list[dict]:
    """Resolve hotels by name across Magic Sands markets (parallel, early-exit)."""
    q = (hotel_name or "").strip()
    if len(q) < 2:
        return []

    countries = list(_preferred_hotel_countries(prefer_country))
    if max_countries is not None:
        countries = countries[: max(1, max_countries)]

    seen: set[str] = set()
    hotels: list[dict] = []

    def _fetch(cc: str) -> list[dict]:
        try:
            payload = client.list_hotels(
                hotel_name=q,
                country_code=cc,
                limit=limit_per_country,
                timeout=timeout,
            )
        except LiteAPIError:
            return []
        return list(payload.get("data") or [])

    # Parallel country lookups — was previously 6 sequential Nuitee calls.
    with ThreadPoolExecutor(max_workers=min(4, len(countries) or 1)) as pool:
        futures = {pool.submit(_fetch, cc): cc for cc in countries}
        for fut in as_completed(futures):
            for h in fut.result():
                hotel_id = str(h.get("id") or h.get("hotelId") or "").strip()
                if not hotel_id or hotel_id in seen:
                    continue
                seen.add(hotel_id)
                hotels.append(h)
                if len(hotels) >= max_results:
                    break
            if len(hotels) >= max_results:
                break

    return hotels[:max_results]


@require_GET
def places_autocomplete(request):
    """Suggest destinations (places) and hotels by name via Nuitee."""
    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    prefer = (
        (request.GET.get("nationality") or request.GET.get("country_code") or "")
        .strip()
        .upper()[:2]
    )
    cache_key = f"ms_places_ac_v3_city_or_hotel:{q.lower().replace(' ', '_')}:{prefer}"
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({"results": cached})

    try:
        client = get_client()
    except LiteAPIError as exc:
        return JsonResponse({"results": [], "error": str(exc)}, status=502)

    want_hotels = _looks_like_hotel_query(q)

    def _fetch_places() -> list[dict]:
        try:
            return client.search_places(q)[:8]
        except LiteAPIError:
            return []

    def _fetch_hotels() -> list[dict]:
        # Hotels only when the query looks like a property name.
        if not want_hotels:
            return []
        return lookup_hotels_by_name(
            client,
            q,
            limit_per_country=3,
            prefer_country=prefer or "OM",
            max_countries=4,
            timeout=10,
            max_results=6,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_places = pool.submit(_fetch_places)
        fut_hotels = pool.submit(_fetch_hotels)
        places = fut_places.result()
        hotel_rows = fut_hotels.result()

    place_items: list[dict] = []
    for p in places:
        if not p.get("placeId"):
            continue
        address = p.get("formattedAddress") or ""
        place_items.append(
            {
                "type": "place",
                "hotelId": "",
                "placeId": p.get("placeId"),
                "displayName": p.get("displayName"),
                "formattedAddress": address,
                "countryCode": country_code_from_address(address),
            }
        )

    hotel_items: list[dict] = []
    for h in hotel_rows:
        item = _hotel_suggestion(h)
        if item:
            hotel_items.append(item)

    # City search → destinations only. Hotel search → hotels first, then places.
    results = (hotel_items + place_items) if want_hotels else place_items

    # Hard filter: GCC + Egypt only.
    results = [r for r in results if _in_search_market_suggestion(r)][:10]
    cache.set(cache_key, results, _AUTOCOMPLETE_CACHE_TTL)
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


def build_hotel_detail_context(request, hotel_id: str) -> dict:
    """Shared hotel + live rates context for public and partner detail pages."""
    search_data = request.session.get("search") or {}
    checkin = request.GET.get("checkin") or search_data.get("checkin")
    checkout = request.GET.get("checkout") or search_data.get("checkout")
    adults = int(request.GET.get("adults") or search_data.get("adults") or 2)
    nationality = normalize_nationality(
        request.GET.get("nationality")
        or search_data.get("nationality")
        or settings.DEFAULT_GUEST_NATIONALITY
    )
    if request.GET.get("occupancies"):
        occupancies = parse_occupancies_from_request(request.GET)
    elif search_data.get("occupancies"):
        occupancies = normalize_occupancies(search_data.get("occupancies"))
    else:
        occupancies = normalize_occupancies(adults=adults)

    if not checkin or not checkout:
        d1, d2 = _default_dates()
        checkin, checkout = d1, d2

    client = get_client()
    hotel = client.get_hotel(hotel_id)
    rates_payload = client.search_rates(
        checkin=checkin,
        checkout=checkout,
        occupancies=occupancies,
        hotel_ids=[hotel_id],
        guest_nationality=nationality,
        max_rates_per_hotel=None,
        include_hotel_data=True,
    )
    reviews_ctx = _build_reviews_context(client, hotel_id, hotel)

    rate_block = next(
        (r for r in (rates_payload.get("data") or []) if r.get("hotelId") == hotel_id),
        (rates_payload.get("data") or [None])[0],
    ) or {}

    rate_rows = build_rate_rows(rate_block, hotel)
    for row in rate_rows:
        row["taxes_json"] = json.dumps(row.get("taxes") or [])
        row["cancel_json"] = json.dumps(row.get("cancel_policies") or [])
        nightly = _build_nightly_fares(checkin, checkout, row.get("amount_value"))
        row["nightly_fares"] = nightly
        breakup = {
            "room_name": row.get("room_name") or "Room",
            "board": row.get("board") or "Room Only",
            "board_type": row.get("board_type") or "",
            "board_basis": _board_basis_label(row.get("board") or "", row.get("board_type") or ""),
            "currency": row.get("currency") or "",
            "amount": row.get("amount"),
            "refundable_label": row.get("refundable_label") or "",
            "is_refundable": bool(row.get("is_refundable")),
            "occupancy_number": row.get("occupancy_number") or 1,
            "nightly_fares": nightly,
            "taxes": row.get("taxes") or [],
            "checkin": checkin,
            "checkout": checkout,
            "nights": len(nightly),
        }
        row["breakup_json"] = json.dumps(breakup)

    # Legacy grouped structure (kept for any older template bits).
    rooms: dict[str, dict] = {}
    for row in rate_rows:
        key = str(row.get("room_key") or row.get("room_name") or "room")
        room = rooms.setdefault(
            key,
            {
                "name": row.get("room_name") or "Room",
                "image": row.get("image"),
                "offers": [],
            },
        )
        room["offers"].append(
            {
                "offer_id": row.get("offer_id"),
                "board": row.get("board") or "",
                "amount": row.get("amount"),
                "currency": row.get("currency"),
                "refundable": row.get("refundable"),
            }
        )

    images = hotel.get("hotelImages") or []
    gallery_items = _build_gallery_items(images)
    main_photo = hotel.get("main_photo") or next(
        (i.get("url") for i in images if i.get("defaultImage")),
        (images[0].get("url") if images else None),
    )
    if not main_photo and gallery_items:
        main_photo = gallery_items[0]["url"]
    gallery = [i["url"] for i in gallery_items]
    photo_count = len(gallery_items)
    # Featured bento: 1 large + up to 4 thumbs (last can be "see all").
    gallery_feature = gallery_items[0] if gallery_items else None
    gallery_thumbs = gallery_items[1:5]
    gallery_categories = ["All"]
    for item in gallery_items:
        if item["category"] not in gallery_categories:
            gallery_categories.append(item["category"])

    start = _parse_date(checkin)
    end = _parse_date(checkout)
    nights = (end - start).days if start and end and end > start else 1
    totals = occupancy_totals(occupancies)
    board_options = sorted(
        {row["board"] for row in rate_rows if row.get("board")},
        key=str.lower,
    )
    room_options = sorted(
        {row["room_name"] for row in rate_rows if row.get("room_name")},
        key=str.lower,
    )
    loc = hotel.get("location") if isinstance(hotel.get("location"), dict) else {}
    hotel_lat = hotel.get("latitude") or loc.get("latitude")
    hotel_lng = hotel.get("longitude") or loc.get("longitude")

    # Facilities / amenities for TBO-style hotel page.
    facility_names: list[str] = []
    for fac in hotel.get("hotelFacilities") or []:
        if isinstance(fac, str) and fac.strip():
            facility_names.append(fac.strip())
        elif isinstance(fac, dict) and fac.get("name"):
            facility_names.append(str(fac["name"]).strip())
    for fac in hotel.get("facilities") or []:
        if isinstance(fac, dict) and fac.get("name"):
            name = str(fac["name"]).strip()
            if name and name not in facility_names:
                facility_names.append(name)
        elif isinstance(fac, str) and fac.strip() and fac.strip() not in facility_names:
            facility_names.append(fac.strip())

    highlight_amenities = _pick_highlight_amenities(facility_names, limit=5)

    review_score = None
    raw_rating = hotel.get("rating")
    try:
        if raw_rating is not None and raw_rating != "":
            review_score = float(raw_rating)
    except (TypeError, ValueError):
        review_score = None
    review_display = None
    if review_score is not None:
        review_display = int(round(review_score * 10)) if review_score <= 10 else int(round(review_score))
    guest_rating_label = _guest_rating_label(review_score)
    review_count = hotel.get("reviewCount") or hotel.get("review_count")

    times = hotel.get("checkinCheckoutTimes") if isinstance(hotel.get("checkinCheckoutTimes"), dict) else {}
    checkin_time = (
        times.get("checkin")
        or times.get("checkinStart")
        or times.get("checkin_start")
        or ""
    )
    checkout_time = (
        times.get("checkout")
        or times.get("checkoutEnd")
        or times.get("checkout_end")
        or ""
    )

    desc = (hotel.get("hotelDescription") or "").strip()
    detail_sections = _parse_hotel_detail_sections(desc)
    policy_bullets = _policy_bullets(hotel, times)
    if policy_bullets:
        # Append / replace policies section for TBO-style details block.
        detail_sections = [
            s for s in detail_sections
            if not re.search(r"polic|check[- ]?in", s.get("title") or "", re.I)
        ]
        detail_sections.append(
            {"title": "Policies & Check-In Instructions", "items": policy_bullets, "is_list": True}
        )

    amenity_groups = _group_amenities(facility_names)

    # Strip simple HTML tags for a one-line highlight.
    highlight = re.sub(r"<[^>]+>", " ", desc)
    highlight = re.sub(r"\s+", " ", highlight).strip()
    if len(highlight) > 110:
        highlight = highlight[:107].rsplit(" ", 1)[0] + "…"

    stars = _normalize_stars(hotel.get("starRating") or hotel.get("stars") or hotel.get("star_rating")) or 0
    extra_photos = max(0, photo_count - 1) if photo_count else 0

    # Price bounds for sticky rates filter — exact lowest → highest for this hotel.
    amounts: list[float] = []
    for r in rate_rows:
        raw = r.get("amount_value")
        if raw is None or raw == "":
            raw = r.get("amount")
        try:
            val = float(str(raw).replace(",", "").strip())
        except (TypeError, ValueError):
            continue
        if val > 0:
            amounts.append(val)
    if amounts:
        rate_price_min = int(min(amounts))
        rate_price_max = int(max(amounts))
        if rate_price_max < rate_price_min:
            rate_price_max = rate_price_min
    else:
        rate_price_min = 0
        rate_price_max = 0

    return {
        "hotel": hotel,
        "hotel_id": hotel_id,
        "main_photo": main_photo,
        "gallery": gallery,
        "gallery_items": gallery_items,
        "gallery_feature": gallery_feature,
        "gallery_thumbs": gallery_thumbs,
        "gallery_categories": gallery_categories,
        "photo_count": photo_count,
        "extra_photos": extra_photos,
        "rooms": list(rooms.values()),
        "rate_rows": rate_rows,
        "rate_count": len(rate_rows),
        "board_options": board_options,
        "room_options": room_options,
        "rate_price_min": rate_price_min,
        "rate_price_max": rate_price_max,
        "checkin": checkin,
        "checkout": checkout,
        "nights": nights,
        "adults": totals["adults"],
        "children_count": totals["children"],
        "rooms_count": totals["rooms"],
        "occupancies": occupancies,
        "occupancy_summary": (
            f"{totals['rooms']} Room(s) | {totals['adults']} Adult(s), "
            f"{totals['children']} Child(ren)"
        ),
        "nationality": nationality,
        "sandbox": bool(rates_payload.get("sandbox")),
        "hotel_lat": hotel_lat,
        "hotel_lng": hotel_lng,
        "facility_names": facility_names,
        "amenity_groups": amenity_groups,
        "detail_sections": detail_sections,
        "highlight_amenities": highlight_amenities,
        "review_score": review_score,
        "review_display": review_display,
        "guest_rating_label": guest_rating_label,
        "review_count": review_count,
        "checkin_time": checkin_time,
        "checkout_time": checkout_time,
        "hotel_highlight": highlight,
        "hotel_stars": stars,
        "hotel_important_info": hotel.get("hotelImportantInformation") or "",
        **reviews_ctx,
    }


@require_GET
def hotel_detail(request, hotel_id: str):
    try:
        context = build_hotel_detail_context(request, hotel_id)
    except LiteAPIError as exc:
        messages.error(request, f"Could not load hotel: {exc}")
        return redirect("book_home")

    return render(request, "hotels/hotel_detail.html", context)

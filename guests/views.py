from __future__ import annotations

from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from bookings.models import Booking
from hotels.liteapi import (
    NATIONALITY_CHOICES,
    LiteAPIError,
    get_client,
    normalize_nationality,
)
from hotels.views import _build_cards, _default_dates, _parse_date

from .forms import GuestLoginForm, GuestProfileForm, GuestRegisterForm
from .models import GuestProfile

User = get_user_model()


def _is_guest_user(user) -> bool:
    return user.is_authenticated and user.is_active and not user.is_staff


def _guest_required(view):
    """Allow only non-staff guest accounts into the portal."""

    @login_required(login_url="guest_login")
    def _wrapped(request, *args, **kwargs):
        if request.user.is_staff:
            messages.info(request, "Staff accounts use the booking admin.")
            return redirect("admin_hub")
        return view(request, *args, **kwargs)

    return _wrapped


def _get_or_create_profile(user) -> GuestProfile:
    profile, _ = GuestProfile.objects.get_or_create(user=user)
    return profile


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
    if _is_guest_user(request.user):
        return redirect("guest_dashboard")
    # Staff sessions were sending people back to the admin hub.
    # Sign them out so the guest front-end login is always reachable.
    if request.user.is_authenticated and request.user.is_staff:
        logout(request)
        messages.info(
            request,
            "Signed out of admin. Use a guest account below for the front-end booking portal.",
        )

    form = GuestLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = _authenticate_guest(
            request, form.cleaned_data["email"], form.cleaned_data["password"]
        )
        if user:
            login(request, user)
            if not form.cleaned_data.get("remember"):
                request.session.set_expiry(0)
            next_url = request.GET.get("next") or reverse("guest_dashboard")
            return redirect(next_url)
        messages.error(request, "Invalid email or password.")

    return render(request, "guests/login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def guest_register(request):
    if _is_guest_user(request.user):
        return redirect("guest_dashboard")

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
        return redirect("guest_dashboard")

    return render(request, "guests/register.html", {"form": form})


@require_POST
def guest_logout(request):
    logout(request)
    return redirect("guest_login")


@_guest_required
@require_http_methods(["GET"])
def dashboard(request):
    checkin, checkout = _default_dates()
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
    default_nat = normalize_nationality(
        request.GET.get("nationality") or profile.nationality or settings.DEFAULT_GUEST_NATIONALITY
    )
    return render(
        request,
        "guests/dashboard.html",
        {
            "profile": profile,
            "checkin": request.GET.get("checkin", checkin),
            "checkout": request.GET.get("checkout", checkout),
            "adults": request.GET.get("adults", "2"),
            "destination": request.GET.get("destination", ""),
            "place_id": request.GET.get("place_id", ""),
            "country_code": request.GET.get("country_code", ""),
            "query": request.GET.get("q", ""),
            "nationality": default_nat,
            "nationality_choices": NATIONALITY_CHOICES,
            "min_date": date.today().isoformat(),
            "recent_bookings": bookings,
            "stats": stats,
        },
    )


@_guest_required
@require_http_methods(["GET"])
def search_home(request):
    checkin, checkout = _default_dates()
    profile = _get_or_create_profile(request.user)
    default_nat = normalize_nationality(
        request.GET.get("nationality") or profile.nationality or settings.DEFAULT_GUEST_NATIONALITY
    )
    return render(
        request,
        "guests/search.html",
        {
            "checkin": request.GET.get("checkin", checkin),
            "checkout": request.GET.get("checkout", checkout),
            "adults": request.GET.get("adults", "2"),
            "destination": request.GET.get("destination", ""),
            "place_id": request.GET.get("place_id", ""),
            "country_code": request.GET.get("country_code", ""),
            "query": request.GET.get("q", ""),
            "nationality": default_nat,
            "nationality_choices": NATIONALITY_CHOICES,
            "min_date": date.today().isoformat(),
            "cards": None,
            "searched": False,
        },
    )


@_guest_required
@require_http_methods(["GET", "POST"])
def search_results(request):
    data = request.POST if request.method == "POST" else request.GET
    checkin = (data.get("checkin") or "").strip()
    checkout = (data.get("checkout") or "").strip()
    adults = int(data.get("adults") or 2)
    place_id = (data.get("place_id") or "").strip()
    destination = (data.get("destination") or "").strip()
    country_code = (data.get("country_code") or "").strip().upper()
    query = (data.get("q") or "").strip()
    profile = _get_or_create_profile(request.user)
    nationality = normalize_nationality(
        data.get("nationality") or profile.nationality or settings.DEFAULT_GUEST_NATIONALITY
    )

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
    if not destination and not query:
        messages.error(request, "Enter a destination or hotel vibe search.")
        return redirect("guest_search")

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

    cards: list[dict] = []
    sandbox = None
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
        sandbox = payload.get("sandbox")
    except LiteAPIError as exc:
        messages.error(request, f"Search failed: {exc}")
        return redirect("guest_search")

    nights = (end - start).days
    prices = [c["price"] for c in cards if c.get("price") is not None]
    price_min = int(min(prices)) if prices else 0
    price_max = int(max(prices)) + 1 if prices else 1000

    return render(
        request,
        "guests/search.html",
        {
            "checkin": checkin,
            "checkout": checkout,
            "adults": adults,
            "destination": destination or query,
            "place_id": place_id,
            "country_code": country_code,
            "query": query,
            "nationality": nationality,
            "nationality_choices": NATIONALITY_CHOICES,
            "min_date": date.today().isoformat(),
            "cards": cards,
            "searched": True,
            "sandbox": sandbox,
            "result_count": len(cards),
            "nights": nights,
            "price_min": price_min,
            "price_max": price_max,
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

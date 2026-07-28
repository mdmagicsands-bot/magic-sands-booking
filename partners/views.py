from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from bookings.models import Booking

from marketing.views import _ctx as marketing_ctx

from .models import PartnerRegistration


def _is_staff(user):
    return user.is_authenticated and user.is_staff


def _authenticate_staff(request, username_or_email: str, password: str):
    user = authenticate(request, username=username_or_email, password=password)
    if user is None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        match = User.objects.filter(email__iexact=username_or_email).first()
        if match:
            user = authenticate(request, username=match.username, password=password)
    if user is not None and user.is_staff and user.is_active:
        return user
    return None


def _authenticate_partner(request, email: str, password: str):
    """Non-staff partner accounts for the Nuitee booking portal."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    email = (email or "").strip().lower()
    user = authenticate(request, username=email, password=password)
    if user is None:
        match = User.objects.filter(email__iexact=email).first()
        if match:
            user = authenticate(request, username=match.username, password=password)
    if user is not None and user.is_active and not user.is_staff:
        return user
    return None


def _is_partner_user(user) -> bool:
    return user.is_authenticated and user.is_active and not user.is_staff


DEMO_PARTNER_EMAIL = "demo@magicsandsdmc.com"
DEMO_PARTNER_PASSWORD = "Demo123"


def _ensure_demo_partner():
    """Keep a local demo portal user available for testing (not a real partner)."""
    from django.contrib.auth import get_user_model

    from guests.models import GuestProfile

    User = get_user_model()
    user, _ = User.objects.update_or_create(
        username=DEMO_PARTNER_EMAIL,
        defaults={
            "email": DEMO_PARTNER_EMAIL,
            "is_staff": False,
            "is_superuser": False,
            "is_active": True,
            "first_name": "Demo",
            "last_name": "Partner",
        },
    )
    user.set_password(DEMO_PARTNER_PASSWORD)
    user.save()
    GuestProfile.objects.get_or_create(user=user)
    return user


def _marketing_url(path: str = "/") -> str:
    base = (getattr(settings, "MARKETING_SITE_URL", "") or "https://www.magicsandsdmc.com").rstrip(
        "/"
    )
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


@require_http_methods(["GET", "POST"])
def partner_login(request):
    """Demo / partner front-end login → Magic Sands search portal (/partner/search/)."""
    if settings.DEBUG:
        _ensure_demo_partner()

    if _is_partner_user(request.user):
        return redirect("guest_search")

    # One-click demo (GET) — avoids stale CSRF from admin sessions / cached forms.
    if request.method == "GET" and request.GET.get("demo") == "1":
        if request.user.is_authenticated:
            logout(request)
        user = _authenticate_partner(request, DEMO_PARTNER_EMAIL, DEMO_PARTNER_PASSWORD)
        if user is None and settings.DEBUG:
            _ensure_demo_partner()
            user = _authenticate_partner(request, DEMO_PARTNER_EMAIL, DEMO_PARTNER_PASSWORD)
        if user:
            login(request, user)
            return redirect("guest_search")
        messages.error(request, "Demo login is unavailable. Run: python manage.py seed_portal_users")
        return redirect("partner_login")

    # Staff sessions must not trap the partner login page.
    # Do this only on GET after demo handling, and re-render so CSRF matches the new session.
    if request.method == "GET" and request.user.is_authenticated and request.user.is_staff:
        logout(request)
        messages.info(
            request,
            "Signed out of admin. Use the demo login below to test the booking portal.",
        )
        return redirect("partner_login")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        remember = request.POST.get("remember") == "on"
        user = _authenticate_partner(request, email, password)
        if user:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            return redirect(request.GET.get("next") or "guest_search")
        if _authenticate_staff(request, email, password):
            messages.error(
                request,
                "That account is website admin. Use Admin login instead.",
            )
        else:
            messages.error(request, "Invalid email or password. Use Continue with demo login.")

    return render(
        request,
        "partners/login.html",
        {
            "demo_email": DEMO_PARTNER_EMAIL,
            "demo_password": DEMO_PARTNER_PASSWORD,
        },
    )


@csrf_exempt
@require_POST
def gateway_partner_login(request):
    """
    Receives login POSTs from Hostinger (magicsandsdmc.com/partner-login/).
    Authenticates a partner account and redirects into /partner/search/.
    """
    email = (request.POST.get("email") or request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    remember = request.POST.get("remember") in ("on", "1", "true", "True")
    user = _authenticate_partner(request, email, password)
    if user:
        login(request, user)
        if not remember:
            request.session.set_expiry(0)
        return redirect("guest_search")

    # Send user back to Hostinger login with an error flag
    return redirect(_marketing_url("/partner-login/?error=1"))


def _parse_year(value: str):
    value = (value or "").strip()
    if not value:
        return None
    try:
        year = int(value)
    except ValueError:
        return None
    if 1800 <= year <= 2100:
        return year
    return None


def _save_partner_registration(request, *, redirect_error, redirect_ok):
    """Shared create logic for on-app and Hostinger gateway posts."""
    company = (request.POST.get("company_name") or "").strip()
    contact = (request.POST.get("contact_name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    accepted = request.POST.get("accepted_terms") in ("on", "1", "true", "True")

    if not company or not contact or not email or not accepted:
        return redirect(redirect_error)

    business_types = request.POST.getlist("business_types")
    if not business_types:
        raw = (request.POST.get("business_types") or "").strip()
        business_types = [p.strip() for p in raw.split(",") if p.strip()]

    telephone = (request.POST.get("telephone") or request.POST.get("phone") or "").strip()
    mobile = (request.POST.get("mobile") or "").strip()

    reg = PartnerRegistration(
        company_name=company,
        trade_license_number=(request.POST.get("trade_license_number") or "").strip(),
        vat_tax_number=(request.POST.get("vat_tax_number") or "").strip(),
        year_established=_parse_year(request.POST.get("year_established")),
        website=(request.POST.get("website") or "").strip(),
        company_registration_country=(
            request.POST.get("company_registration_country") or ""
        ).strip(),
        office_address=(request.POST.get("office_address") or "").strip(),
        country=(request.POST.get("country") or "").strip(),
        city=(request.POST.get("city") or "").strip(),
        postal_code=(request.POST.get("postal_code") or "").strip(),
        telephone=telephone,
        whatsapp=(request.POST.get("whatsapp") or "").strip(),
        contact_name=contact,
        designation=(request.POST.get("designation") or "").strip(),
        email=email,
        mobile=mobile,
        phone=telephone or mobile,
        markets_served=(request.POST.get("markets_served") or "").strip(),
        main_destinations_sold=(request.POST.get("main_destinations_sold") or "").strip(),
        business_types=", ".join(business_types),
        annual_passenger_volume=(request.POST.get("annual_passenger_volume") or "").strip(),
        preferred_currency=(request.POST.get("preferred_currency") or "").strip(),
        accepted_terms=True,
        message=(request.POST.get("message") or "").strip(),
    )

    file_map = {
        "trade_license_file": "trade_license_file",
        "passport_id_file": "passport_id_file",
        "vat_certificate_file": "vat_certificate_file",
        "company_profile_file": "company_profile_file",
        "logo_file": "logo_file",
    }
    for field_name, input_name in file_map.items():
        uploaded = request.FILES.get(input_name)
        if uploaded:
            setattr(reg, field_name, uploaded)

    reg.save()
    from .emails import send_partner_registration_emails

    send_partner_registration_emails(reg)
    return redirect(redirect_ok)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def gateway_partner_register(request):
    """
    Partner registration:
    - GET renders the multi-step form on this app
    - POST saves the full application (also used by Hostinger gateway)
    """
    if request.method == "GET":
        return render(
            request,
            "partners/register.html",
            marketing_ctx(
                success=request.GET.get("ok") == "1",
                error=request.GET.get("error") == "1",
                header_color=True,
                currencies=["USD", "EUR", "GBP", "AED", "OMR", "SAR", "QAR", "BHD", "KWD", "EGP"],
            ),
        )

    # Hostinger posts go back to Hostinger; on-app posts stay here.
    referer = request.META.get("HTTP_REFERER") or ""
    from_hostinger = "magicsandsdmc.com" in referer and "partner-register" in referer
    if from_hostinger:
        return _save_partner_registration(
            request,
            redirect_error=_marketing_url("/partner-register/?error=1"),
            redirect_ok=_marketing_url("/partner-register/?ok=1"),
        )

    return _save_partner_registration(
        request,
        redirect_error=f"{reverse('partner_register')}?error=1",
        redirect_ok=f"{reverse('partner_register')}?ok=1",
    )


@require_http_methods(["GET", "POST"])
def admin_login(request):
    """Website admin login — opens the Marketing / Booking hub after sign-in."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_hub")

    # Partner sessions should not open the admin login by accident.
    if _is_partner_user(request.user):
        logout(request)

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = _authenticate_staff(request, username, password)
        if user:
            login(request, user)
            request.session.set_expiry(0)
            return redirect(request.GET.get("next") or "admin_hub")
        # Helpful hint if they used the partner demo on the admin form.
        partner_try = _authenticate_partner(request, username, password)
        if partner_try:
            messages.error(
                request,
                "That account is a partner login. Use Partner login for the hotel booking portal.",
            )
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "partners/admin_login.html")


@require_POST
def partner_logout(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("admin_login")


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def admin_hub(request):
    """Post-login chooser: Marketing CMS or Booking system."""
    from marketing.models import ContactMessage

    unread = ContactMessage.objects.filter(is_read=False).count()
    booking_pending = Booking.objects.filter(status=Booking.Status.PENDING_PAYMENT).count()
    partner_pending = PartnerRegistration.objects.filter(
        status=PartnerRegistration.Status.PENDING
    ).count()
    return render(
        request,
        "partners/admin_hub.html",
        {
            "unread_messages": unread,
            "booking_pending": booking_pending,
            "partner_pending": partner_pending,
        },
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def dashboard(request):
    qs = Booking.objects.all()
    stats = {
        "total": qs.count(),
        "confirmed": qs.filter(status=Booking.Status.CONFIRMED).count(),
        "pending": qs.filter(status=Booking.Status.PENDING_PAYMENT).count(),
        "failed": qs.filter(status=Booking.Status.FAILED).count(),
        "cancelled": qs.filter(status=Booking.Status.CANCELLED).count(),
        "partner_requests": PartnerRegistration.objects.filter(
            status=PartnerRegistration.Status.PENDING
        ).count(),
    }
    revenue = (
        qs.filter(status=Booking.Status.CONFIRMED)
        .aggregate(total=Sum("amount"))
        .get("total")
    )
    recent = qs[:8]
    pending_partners = PartnerRegistration.objects.filter(
        status=PartnerRegistration.Status.PENDING
    )[:5]
    return render(
        request,
        "partners/dashboard.html",
        {
            "stats": stats,
            "revenue": revenue,
            "recent": recent,
            "pending_partners": pending_partners,
            "marketing_site_url": settings.MARKETING_SITE_URL,
        },
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def partner_requests(request):
    status = (request.GET.get("status") or "").strip()
    qs = PartnerRegistration.objects.all()
    if status:
        qs = qs.filter(status=status)
    return render(
        request,
        "partners/registrations.html",
        {
            "registrations": qs[:200],
            "status": status,
            "status_choices": PartnerRegistration.Status.choices,
        },
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def partner_request_detail(request, registration_id: int):
    reg = get_object_or_404(PartnerRegistration, pk=registration_id)
    return render(
        request,
        "partners/registration_detail.html",
        {
            "reg": reg,
            "status_choices": PartnerRegistration.Status.choices,
        },
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
@require_POST
def partner_request_status(request, registration_id: int):
    reg = get_object_or_404(PartnerRegistration, pk=registration_id)
    new_status = (request.POST.get("status") or "").strip()
    valid = {c[0] for c in PartnerRegistration.Status.choices}
    if new_status in valid:
        from django.utils import timezone

        reg.status = new_status
        reg.reviewed_at = timezone.now()
        reg.save(update_fields=["status", "reviewed_at"])
        messages.success(request, f"Registration marked {reg.get_status_display()}.")
    else:
        messages.error(request, "Invalid status.")
    next_url = request.POST.get("next") or reverse("partner_requests")
    return redirect(next_url)


def _booking_list_response(request, *, forced_status: str | None = None, list_title: str | None = None):
    status = forced_status if forced_status is not None else (request.GET.get("status") or "").strip()
    q = (request.GET.get("q") or "").strip()
    qs = Booking.objects.all()
    if status:
        qs = qs.filter(status=status)
    if q:
        qs = qs.filter(
            Q(guest_email__icontains=q)
            | Q(guest_first_name__icontains=q)
            | Q(guest_last_name__icontains=q)
            | Q(hotel_name__icontains=q)
            | Q(liteapi_booking_id__icontains=q)
            | Q(hotel_confirmation_code__icontains=q)
        )
    titles = {
        "pending_payment": "Pending payment",
        "confirmed": "Confirmed bookings",
        "cancelled": "Cancellations",
        "failed": "Failed / errors",
    }
    return render(
        request,
        "partners/bookings.html",
        {
            "bookings": qs[:200],
            "status": status,
            "q": q,
            "status_choices": Booking.Status.choices,
            "list_title": list_title or titles.get(status, "All bookings"),
        },
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def booking_list(request):
    return _booking_list_response(request)


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def booking_list_pending(request):
    return _booking_list_response(
        request,
        forced_status=Booking.Status.PENDING_PAYMENT,
        list_title="Pending payment",
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def booking_list_confirmed(request):
    return _booking_list_response(
        request,
        forced_status=Booking.Status.CONFIRMED,
        list_title="Confirmed bookings",
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def booking_list_cancelled(request):
    return _booking_list_response(
        request,
        forced_status=Booking.Status.CANCELLED,
        list_title="Cancellations",
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def booking_list_failed(request):
    return _booking_list_response(
        request,
        forced_status=Booking.Status.FAILED,
        list_title="Failed / errors",
    )


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def booking_detail(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id)
    return render(request, "partners/booking_detail.html", {"booking": booking})


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
@require_POST
def booking_update_status(request, booking_id: int):
    booking = get_object_or_404(Booking, pk=booking_id)
    new_status = (request.POST.get("status") or "").strip()
    valid = {c[0] for c in Booking.Status.choices}
    if new_status in valid:
        booking.status = new_status
        booking.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Booking updated to {booking.get_status_display()}.")
    else:
        messages.error(request, "Invalid status.")
    return redirect("partner_booking_detail", booking_id=booking.pk)


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def admin_module_page(request, module_key: str):
    from .menu import MODULE_PAGES

    page = MODULE_PAGES.get(module_key)
    if not page:
        return redirect("booking_admin_dashboard")
    return render(
        request,
        "partners/module.html",
        {
            "module": page,
            "module_key": module_key,
        },
    )

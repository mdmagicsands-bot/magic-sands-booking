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


def _marketing_url(path: str = "/") -> str:
    base = (getattr(settings, "MARKETING_SITE_URL", "") or "https://www.magicsandsdmc.com").rstrip(
        "/"
    )
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}{path}"


@require_http_methods(["GET", "POST"])
def partner_login(request):
    """On-Railway fallback partner login (same branding as Hostinger page)."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_hub")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        remember = request.POST.get("remember") == "on"
        user = _authenticate_staff(request, email, password)
        if user:
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            return redirect(request.GET.get("next") or "admin_hub")
        messages.error(request, "Invalid email or password, or account is not a partner.")

    return render(request, "partners/login.html")


@csrf_exempt
@require_POST
def gateway_partner_login(request):
    """
    Receives login POSTs from Hostinger (magicsandsdmc.com/partner-login/).
    Authenticates on Railway and redirects into /admin/.
    """
    email = (request.POST.get("email") or request.POST.get("username") or "").strip()
    password = request.POST.get("password") or ""
    remember = request.POST.get("remember") in ("on", "1", "true", "True")
    user = _authenticate_staff(request, email, password)
    if user:
        login(request, user)
        if not remember:
            request.session.set_expiry(0)
        return redirect("admin_hub")

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
            {
                "success": request.GET.get("ok") == "1",
                "error": request.GET.get("error") == "1",
                "currencies": ["USD", "EUR", "GBP", "AED", "OMR", "SAR", "QAR", "BHD", "KWD", "EGP"],
            },
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

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = _authenticate_staff(request, username, password)
        if user:
            login(request, user)
            request.session.set_expiry(0)
            return redirect(request.GET.get("next") or "admin_hub")
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


@login_required(login_url="admin_login")
@user_passes_test(_is_staff, login_url="admin_login")
def booking_list(request):
    status = (request.GET.get("status") or "").strip()
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
    return render(
        request,
        "partners/bookings.html",
        {
            "bookings": qs[:200],
            "status": status,
            "q": q,
            "status_choices": Booking.Status.choices,
        },
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

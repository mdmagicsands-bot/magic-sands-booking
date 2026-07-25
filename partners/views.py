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


@csrf_exempt
@require_http_methods(["GET", "POST"])
def gateway_partner_register(request):
    """
    Receives partner registration from Hostinger.
    GET shows a Railway fallback form; POST saves a pending registration.
    """
    if request.method == "GET":
        return render(request, "partners/register.html")

    company = (request.POST.get("company_name") or "").strip()
    contact = (request.POST.get("contact_name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    phone = (request.POST.get("phone") or "").strip()
    country = (request.POST.get("country") or "").strip()
    website = (request.POST.get("website") or "").strip()
    message = (request.POST.get("message") or "").strip()

    if not company or not contact or not email:
        return redirect(_marketing_url("/partner-register/?error=1"))

    PartnerRegistration.objects.create(
        company_name=company,
        contact_name=contact,
        email=email,
        phone=phone,
        country=country,
        website=website,
        message=message,
    )
    return redirect(_marketing_url("/partner-register/?ok=1"))


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
    return redirect("partner_requests")


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

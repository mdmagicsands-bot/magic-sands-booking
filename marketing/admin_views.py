from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    DestinationForm,
    MarketingSettingsForm,
    OfficeForm,
    ServiceForm,
    TestimonialForm,
    WhyChooseForm,
)
from .models import (
    ContactMessage,
    Destination,
    MarketingSettings,
    Office,
    Service,
    Testimonial,
    WhyChooseItem,
)


def _is_staff(user):
    return user.is_authenticated and user.is_staff


def staff_required(view):
    return login_required(login_url="admin_login")(
        user_passes_test(_is_staff, login_url="admin_login")(view)
    )


@staff_required
def marketing_dashboard(request):
    return render(
        request,
        "marketing/admin/dashboard.html",
        {
            "counts": {
                "destinations": Destination.objects.count(),
                "services": Service.objects.count(),
                "testimonials": Testimonial.objects.count(),
                "offices": Office.objects.count(),
                "messages": ContactMessage.objects.filter(is_read=False).count(),
                "why": WhyChooseItem.objects.count(),
            },
            "recent_messages": ContactMessage.objects.all()[:5],
        },
    )


@staff_required
@require_http_methods(["GET", "POST"])
def marketing_settings(request):
    settings_obj = MarketingSettings.get_solo()
    if request.method == "POST":
        form = MarketingSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Marketing settings saved.")
            return redirect("marketing_admin_settings")
    else:
        form = MarketingSettingsForm(instance=settings_obj)
    return render(request, "marketing/admin/settings_form.html", {"form": form})


def _crud_list(request, model, template, context_key):
    return render(
        request,
        template,
        {context_key: model.objects.all(), "title": model._meta.verbose_name_plural.title()},
    )


def _crud_edit(request, model, form_class, instance, success_url_name, template, label):
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            if hasattr(obj, "sync_role_from_dates"):
                obj.sync_role_from_dates()
            obj.save()
            messages.success(request, f"{label} saved.")
            return redirect(success_url_name)
    else:
        form = form_class(instance=instance)
    return render(
        request,
        template,
        {
            "form": form,
            "object": instance,
            "label": label,
            "is_create": instance is None or instance.pk is None,
        },
    )


@staff_required
def destination_list(request):
    return _crud_list(
        request, Destination, "marketing/admin/destination_list.html", "items"
    )


@staff_required
@require_http_methods(["GET", "POST"])
def destination_create(request):
    return _crud_edit(
        request,
        Destination,
        DestinationForm,
        Destination(),
        "marketing_admin_destinations",
        "marketing/admin/destination_form.html",
        "Destination",
    )


@staff_required
@require_http_methods(["GET", "POST"])
def destination_edit(request, pk: int):
    obj = get_object_or_404(Destination, pk=pk)
    return _crud_edit(
        request,
        Destination,
        DestinationForm,
        obj,
        "marketing_admin_destinations",
        "marketing/admin/destination_form.html",
        "Destination",
    )


@staff_required
@require_POST
def destination_delete(request, pk: int):
    obj = get_object_or_404(Destination, pk=pk)
    obj.delete()
    messages.success(request, "Destination deleted.")
    return redirect("marketing_admin_destinations")


@staff_required
def service_list(request):
    return _crud_list(request, Service, "marketing/admin/service_list.html", "items")


@staff_required
@require_http_methods(["GET", "POST"])
def service_create(request):
    return _crud_edit(
        request,
        Service,
        ServiceForm,
        Service(),
        "marketing_admin_services",
        "marketing/admin/service_form.html",
        "Service",
    )


@staff_required
@require_http_methods(["GET", "POST"])
def service_edit(request, pk: int):
    obj = get_object_or_404(Service, pk=pk)
    return _crud_edit(
        request,
        Service,
        ServiceForm,
        obj,
        "marketing_admin_services",
        "marketing/admin/service_form.html",
        "Service",
    )


@staff_required
@require_POST
def service_delete(request, pk: int):
    obj = get_object_or_404(Service, pk=pk)
    obj.delete()
    messages.success(request, "Service deleted.")
    return redirect("marketing_admin_services")


@staff_required
def testimonial_list(request):
    return _crud_list(
        request, Testimonial, "marketing/admin/testimonial_list.html", "items"
    )


@staff_required
@require_http_methods(["GET", "POST"])
def testimonial_create(request):
    return _crud_edit(
        request,
        Testimonial,
        TestimonialForm,
        Testimonial(),
        "marketing_admin_testimonials",
        "marketing/admin/testimonial_form.html",
        "Testimonial",
    )


@staff_required
@require_http_methods(["GET", "POST"])
def testimonial_edit(request, pk: int):
    obj = get_object_or_404(Testimonial, pk=pk)
    return _crud_edit(
        request,
        Testimonial,
        TestimonialForm,
        obj,
        "marketing_admin_testimonials",
        "marketing/admin/testimonial_form.html",
        "Testimonial",
    )


@staff_required
@require_POST
def testimonial_delete(request, pk: int):
    obj = get_object_or_404(Testimonial, pk=pk)
    obj.delete()
    messages.success(request, "Testimonial deleted.")
    return redirect("marketing_admin_testimonials")


@staff_required
def office_list(request):
    return _crud_list(request, Office, "marketing/admin/office_list.html", "items")


@staff_required
@require_http_methods(["GET", "POST"])
def office_create(request):
    return _crud_edit(
        request,
        Office,
        OfficeForm,
        Office(),
        "marketing_admin_offices",
        "marketing/admin/office_form.html",
        "Office",
    )


@staff_required
@require_http_methods(["GET", "POST"])
def office_edit(request, pk: int):
    obj = get_object_or_404(Office, pk=pk)
    return _crud_edit(
        request,
        Office,
        OfficeForm,
        obj,
        "marketing_admin_offices",
        "marketing/admin/office_form.html",
        "Office",
    )


@staff_required
@require_POST
def office_delete(request, pk: int):
    obj = get_object_or_404(Office, pk=pk)
    obj.delete()
    messages.success(request, "Office deleted.")
    return redirect("marketing_admin_offices")


@staff_required
def why_list(request):
    return _crud_list(request, WhyChooseItem, "marketing/admin/why_list.html", "items")


@staff_required
@require_http_methods(["GET", "POST"])
def why_create(request):
    return _crud_edit(
        request,
        WhyChooseItem,
        WhyChooseForm,
        WhyChooseItem(),
        "marketing_admin_why",
        "marketing/admin/why_form.html",
        "Why choose item",
    )


@staff_required
@require_http_methods(["GET", "POST"])
def why_edit(request, pk: int):
    obj = get_object_or_404(WhyChooseItem, pk=pk)
    return _crud_edit(
        request,
        WhyChooseItem,
        WhyChooseForm,
        obj,
        "marketing_admin_why",
        "marketing/admin/why_form.html",
        "Why choose item",
    )


@staff_required
@require_POST
def why_delete(request, pk: int):
    obj = get_object_or_404(WhyChooseItem, pk=pk)
    obj.delete()
    messages.success(request, "Item deleted.")
    return redirect("marketing_admin_why")


@staff_required
def message_list(request):
    return render(
        request,
        "marketing/admin/message_list.html",
        {"items": ContactMessage.objects.all()[:300]},
    )


@staff_required
@require_http_methods(["GET", "POST"])
def message_detail(request, pk: int):
    obj = get_object_or_404(ContactMessage, pk=pk)
    if not obj.is_read:
        obj.is_read = True
        obj.save(update_fields=["is_read"])
    if request.method == "POST" and request.POST.get("action") == "delete":
        obj.delete()
        messages.success(request, "Message deleted.")
        return redirect("marketing_admin_messages")
    return render(request, "marketing/admin/message_detail.html", {"item": obj})

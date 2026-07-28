"""Staff login and partner registration routes for marketing-only deploys."""

from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path(
        "gateway/partner-register/",
        views.gateway_partner_register,
        name="gateway_partner_register",
    ),
    path("partner-register/", views.gateway_partner_register, name="partner_register"),
    path("admin/login/", views.admin_login, name="admin_login"),
    path("admin/logout/", views.partner_logout, name="partner_logout"),
    path(
        "admin/",
        RedirectView.as_view(url="/admin/marketing/", permanent=False),
        name="admin_hub",
    ),
]

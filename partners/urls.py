from django.urls import path

from . import views

urlpatterns = [
    # Hostinger → Railway gateways (CSRF exempt form posts)
    path("gateway/partner-login/", views.gateway_partner_login, name="gateway_partner_login"),
    path(
        "gateway/partner-register/",
        views.gateway_partner_register,
        name="gateway_partner_register",
    ),
    # On-app pages
    path("partner-login/", views.partner_login, name="partner_login"),
    path("partner-register/", views.gateway_partner_register, name="partner_register"),
    path("admin/login/", views.admin_login, name="admin_login"),
    path("admin/logout/", views.partner_logout, name="partner_logout"),
    path("admin/", views.dashboard, name="partner_dashboard"),
    path("admin/bookings/", views.booking_list, name="partner_bookings"),
    path("admin/bookings/<int:booking_id>/", views.booking_detail, name="partner_booking_detail"),
    path(
        "admin/bookings/<int:booking_id>/status/",
        views.booking_update_status,
        name="partner_booking_status",
    ),
    path("admin/partners/", views.partner_requests, name="partner_requests"),
    path(
        "admin/partners/<int:registration_id>/status/",
        views.partner_request_status,
        name="partner_request_status",
    ),
]

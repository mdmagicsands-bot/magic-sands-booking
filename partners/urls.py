from django.urls import path

from . import nuitee_admin, views
from .menu import MODULE_PAGES

module_urls = [
    path(
        f"admin/modules/{key.replace('admin_mod_', '').replace('_', '-')}/",
        views.admin_module_page,
        {"module_key": key},
        name=key,
    )
    for key in MODULE_PAGES.keys()
]

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
    path("admin/", views.admin_hub, name="admin_hub"),
    path("admin/booking/", views.dashboard, name="partner_dashboard"),
    path("admin/search/", nuitee_admin.live_hotel_search, name="admin_live_search"),
    path(
        "admin/inventory/nuitee/",
        nuitee_admin.nuitee_inventory,
        name="admin_mod_nuitee_hotels",
    ),
    path(
        "admin/settings/liteapi/",
        nuitee_admin.liteapi_settings,
        name="admin_liteapi_settings",
    ),
    path("admin/bookings/", views.booking_list, name="partner_bookings"),
    path(
        "admin/bookings/pending/",
        views.booking_list_pending,
        name="partner_bookings_pending",
    ),
    path(
        "admin/bookings/confirmed/",
        views.booking_list_confirmed,
        name="partner_bookings_confirmed",
    ),
    path(
        "admin/bookings/cancelled/",
        views.booking_list_cancelled,
        name="partner_bookings_cancelled",
    ),
    path(
        "admin/bookings/failed/",
        views.booking_list_failed,
        name="partner_bookings_failed",
    ),
    path("admin/bookings/<int:booking_id>/", views.booking_detail, name="partner_booking_detail"),
    path(
        "admin/bookings/<int:booking_id>/status/",
        views.booking_update_status,
        name="partner_booking_status",
    ),
    path("admin/partners/", views.partner_requests, name="partner_requests"),
    path(
        "admin/partners/<int:registration_id>/",
        views.partner_request_detail,
        name="partner_request_detail",
    ),
    path(
        "admin/partners/<int:registration_id>/status/",
        views.partner_request_status,
        name="partner_request_status",
    ),
    *module_urls,
]

from django.urls import path

from . import admin_views, views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("services/", views.services, name="services"),
    path("destinations/", views.destinations, name="destinations"),
    path("destinations/<slug:slug>/", views.destination_detail, name="destination_detail"),
    path("testimonials/", views.testimonials, name="testimonials"),
    path("contact/", views.contact, name="contact"),
    # Marketing CMS (staff)
    path("admin/marketing/", admin_views.marketing_dashboard, name="marketing_admin"),
    path(
        "admin/marketing/settings/",
        admin_views.marketing_settings,
        name="marketing_admin_settings",
    ),
    path(
        "admin/marketing/destinations/",
        admin_views.destination_list,
        name="marketing_admin_destinations",
    ),
    path(
        "admin/marketing/destinations/new/",
        admin_views.destination_create,
        name="marketing_admin_destination_new",
    ),
    path(
        "admin/marketing/destinations/<int:pk>/",
        admin_views.destination_edit,
        name="marketing_admin_destination_edit",
    ),
    path(
        "admin/marketing/destinations/<int:pk>/delete/",
        admin_views.destination_delete,
        name="marketing_admin_destination_delete",
    ),
    path(
        "admin/marketing/services/",
        admin_views.service_list,
        name="marketing_admin_services",
    ),
    path(
        "admin/marketing/services/new/",
        admin_views.service_create,
        name="marketing_admin_service_new",
    ),
    path(
        "admin/marketing/services/<int:pk>/",
        admin_views.service_edit,
        name="marketing_admin_service_edit",
    ),
    path(
        "admin/marketing/services/<int:pk>/delete/",
        admin_views.service_delete,
        name="marketing_admin_service_delete",
    ),
    path(
        "admin/marketing/testimonials/",
        admin_views.testimonial_list,
        name="marketing_admin_testimonials",
    ),
    path(
        "admin/marketing/testimonials/new/",
        admin_views.testimonial_create,
        name="marketing_admin_testimonial_new",
    ),
    path(
        "admin/marketing/testimonials/<int:pk>/",
        admin_views.testimonial_edit,
        name="marketing_admin_testimonial_edit",
    ),
    path(
        "admin/marketing/testimonials/<int:pk>/delete/",
        admin_views.testimonial_delete,
        name="marketing_admin_testimonial_delete",
    ),
    path(
        "admin/marketing/offices/",
        admin_views.office_list,
        name="marketing_admin_offices",
    ),
    path(
        "admin/marketing/offices/new/",
        admin_views.office_create,
        name="marketing_admin_office_new",
    ),
    path(
        "admin/marketing/offices/<int:pk>/",
        admin_views.office_edit,
        name="marketing_admin_office_edit",
    ),
    path(
        "admin/marketing/offices/<int:pk>/delete/",
        admin_views.office_delete,
        name="marketing_admin_office_delete",
    ),
    path("admin/marketing/why/", admin_views.why_list, name="marketing_admin_why"),
    path(
        "admin/marketing/why/new/",
        admin_views.why_create,
        name="marketing_admin_why_new",
    ),
    path(
        "admin/marketing/why/<int:pk>/",
        admin_views.why_edit,
        name="marketing_admin_why_edit",
    ),
    path(
        "admin/marketing/why/<int:pk>/delete/",
        admin_views.why_delete,
        name="marketing_admin_why_delete",
    ),
    path(
        "admin/marketing/messages/",
        admin_views.message_list,
        name="marketing_admin_messages",
    ),
    path(
        "admin/marketing/messages/<int:pk>/",
        admin_views.message_detail,
        name="marketing_admin_message_detail",
    ),
]

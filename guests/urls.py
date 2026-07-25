from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.guest_login, name="guest_login"),
    path("register/", views.guest_register, name="guest_register"),
    path("logout/", views.guest_logout, name="guest_logout"),
    path("", views.dashboard, name="guest_dashboard"),
    path("search/", views.search_home, name="guest_search"),
    path("search/results/", views.search_results, name="guest_search_results"),
    path("bookings/", views.bookings_list, name="guest_bookings"),
    path("bookings/<int:booking_id>/", views.booking_detail, name="guest_booking_detail"),
    path("saved/", views.saved_hotels, name="guest_saved"),
    path("profile/", views.profile, name="guest_profile"),
    path("support/", views.support, name="guest_support"),
]

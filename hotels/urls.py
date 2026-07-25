from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="book_home"),
    path("api/places/", views.places_autocomplete, name="places_autocomplete"),
    path("search/", views.search, name="search"),
    path("<str:hotel_id>/", views.hotel_detail, name="hotel_detail"),
]

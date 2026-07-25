from django.urls import path

from . import views

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("payment/return/", views.payment_return, name="payment_return"),
    path("confirmation/<int:booking_id>/", views.confirmation, name="confirmation"),
]

from django.urls import path

from . import views

urlpatterns = [
    path("prebook/", views.prebook_check, name="prebook_check"),
    path("wizard/<int:booking_id>/", views.booking_wizard, name="booking_wizard"),
    path("wizard/<int:booking_id>/pay-credit/", views.partner_credit_pay, name="partner_credit_pay"),
    path("checkout/", views.checkout, name="checkout"),
    path("payment/return/", views.payment_return, name="payment_return"),
    path("confirmation/<int:booking_id>/", views.confirmation, name="confirmation"),
    path("voucher/<int:booking_id>/", views.booking_voucher, name="booking_voucher"),
]

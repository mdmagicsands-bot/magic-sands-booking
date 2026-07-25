from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "liteapi_booking_id",
        "hotel_name",
        "guest_email",
        "user",
        "check_in",
        "check_out",
        "amount",
        "currency",
        "status",
        "created_at",
    )
    list_filter = ("status", "currency")
    search_fields = (
        "liteapi_booking_id",
        "prebook_id",
        "hotel_name",
        "hotel_id",
        "guest_email",
        "guest_first_name",
        "guest_last_name",
        "hotel_confirmation_code",
        "user__email",
    )
    readonly_fields = (
        "offer_id",
        "prebook_id",
        "transaction_id",
        "liteapi_booking_id",
        "raw_prebook",
        "raw_book",
        "created_at",
        "updated_at",
    )

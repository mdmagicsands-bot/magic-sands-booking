from django.contrib import admin

from .models import GuestProfile


@admin.register(GuestProfile)
class GuestProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "nationality", "preferred_currency", "created_at")
    search_fields = ("user__email", "user__username", "phone")

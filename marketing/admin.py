from django.contrib import admin

from .models import (
    ContactMessage,
    Destination,
    MarketingSettings,
    Office,
    Service,
    Testimonial,
    WhyChooseItem,
)


@admin.register(MarketingSettings)
class MarketingSettingsAdmin(admin.ModelAdmin):
    list_display = ("brand", "hero_title", "updated_at")


@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "is_published")
    list_filter = ("is_published",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "short", "slug")


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "sort_order", "is_published")
    list_filter = ("is_published",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "sort_order", "is_published", "created_at")
    list_filter = ("is_published",)
    search_fields = ("name", "quote")


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("label", "phone", "email", "sort_order", "is_published")
    list_filter = ("is_published",)


@admin.register(WhyChooseItem)
class WhyChooseItemAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "is_published")
    list_filter = ("is_published",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "company", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "company", "message")
    readonly_fields = ("created_at",)

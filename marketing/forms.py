from django import forms

from .models import (
    Destination,
    MarketingSettings,
    Office,
    Service,
    Testimonial,
    WhyChooseItem,
)


class MarketingSettingsForm(forms.ModelForm):
    class Meta:
        model = MarketingSettings
        fields = [
            "brand",
            "brand_full",
            "tagline",
            "hero_title",
            "hero_lede",
            "about_blurb",
            "elevating_title",
            "elevating_text",
            "about_intro_title",
            "about_intro",
            "about_expertise",
            "about_story",
            "about_boutique",
            "about_why",
            "about_why_detail",
            "motto",
            "mission",
            "values_intro",
        ]
        widgets = {
            "hero_lede": forms.Textarea(attrs={"rows": 3}),
            "about_blurb": forms.Textarea(attrs={"rows": 3}),
            "elevating_text": forms.Textarea(attrs={"rows": 4}),
            "about_intro_title": forms.Textarea(attrs={"rows": 3}),
            "about_intro": forms.Textarea(attrs={"rows": 3}),
            "about_expertise": forms.Textarea(attrs={"rows": 3}),
            "about_story": forms.Textarea(attrs={"rows": 3}),
            "about_boutique": forms.Textarea(attrs={"rows": 3}),
            "about_why": forms.Textarea(attrs={"rows": 3}),
            "about_why_detail": forms.Textarea(attrs={"rows": 4}),
            "mission": forms.Textarea(attrs={"rows": 3}),
            "values_intro": forms.Textarea(attrs={"rows": 3}),
        }


class DestinationForm(forms.ModelForm):
    class Meta:
        model = Destination
        fields = [
            "name",
            "slug",
            "short",
            "summary",
            "teaser",
            "image_url",
            "banner_url",
            "accent",
            "sort_order",
            "is_published",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 4}),
            "teaser": forms.Textarea(attrs={"rows": 2}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["title", "slug", "text", "image_url", "sort_order", "is_published"]
        widgets = {"text": forms.Textarea(attrs={"rows": 4})}


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ["name", "role", "quote", "sort_order", "is_published"]
        widgets = {"quote": forms.Textarea(attrs={"rows": 4})}


class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = ["label", "address", "phone", "email", "sort_order", "is_published"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class WhyChooseForm(forms.ModelForm):
    class Meta:
        model = WhyChooseItem
        fields = ["title", "text", "icon_url", "sort_order", "is_published"]
        widgets = {"text": forms.Textarea(attrs={"rows": 3})}

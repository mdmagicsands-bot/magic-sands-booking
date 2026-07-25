from django.db import models


class MarketingSettings(models.Model):
    """Singleton-style site copy for the marketing homepage/about hero."""

    brand = models.CharField(max_length=120, default="Magic Sands")
    brand_full = models.CharField(max_length=180, default="Magic Sands DMC")
    tagline = models.CharField(max_length=180, default="YOUR GUIDE TO ARABIA")
    hero_title = models.CharField(max_length=255, default="Elevating the extraordinary")
    hero_lede = models.TextField(blank=True)
    about_blurb = models.TextField(blank=True)
    elevating_title = models.CharField(max_length=255, default="Elevating the extraordinary")
    elevating_text = models.TextField(blank=True)
    about_intro_title = models.TextField(blank=True)
    about_intro = models.TextField(blank=True)
    about_expertise = models.TextField(blank=True)
    about_story = models.TextField(blank=True)
    about_boutique = models.TextField(blank=True)
    about_why = models.TextField(blank=True)
    about_why_detail = models.TextField(blank=True)
    motto = models.CharField(max_length=255, blank=True)
    mission = models.TextField(blank=True)
    values_intro = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Marketing settings"
        verbose_name_plural = "Marketing settings"

    def __str__(self):
        return "Marketing settings"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if obj:
            return obj
        return cls.objects.create()


class Destination(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    short = models.CharField(max_length=60)
    summary = models.TextField()
    teaser = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    banner_url = models.URLField(blank=True)
    accent = models.CharField(max_length=20, default="#1b6b74")
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Service(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=120)
    text = models.TextField()
    image_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    quote = models.TextField()
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"{self.name}: {self.quote[:48]}"


class Office(models.Model):
    label = models.CharField(max_length=160)
    address = models.TextField()
    phone = models.CharField(max_length=60, blank=True)
    email = models.EmailField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "label"]

    def __str__(self):
        return self.label


class WhyChooseItem(models.Model):
    title = models.CharField(max_length=160)
    text = models.TextField()
    icon_url = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=160)
    email = models.EmailField()
    company = models.CharField(max_length=180, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"

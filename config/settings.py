"""
Django settings for Magic Sands Booking.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")
_raw_hosts = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]
# In DEBUG, allow LAN / tunnel hosts so phones can open the site.
ALLOWED_HOSTS = ["*"] if DEBUG and ("*" in _raw_hosts or not _raw_hosts) else _raw_hosts
if DEBUG and "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS = list(
        {
            *_raw_hosts,
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            ".ngrok-free.app",
            ".ngrok.io",
            ".loca.lt",
            ".trycloudflare.com",
        }
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "marketing",
    "hotels",
    "bookings",
    "partners",
    "guests",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "hotels.context_processors.branding",
                "partners.context_processors.booking_admin_nav",
                "guests.context_processors.guest_portal_nav",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Muscat"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# LiteAPI / Nuitee Connect
LITEAPI_API_KEY = os.getenv("LITEAPI_API_KEY", "")
LITEAPI_PUBLIC_KEY = os.getenv("LITEAPI_PUBLIC_KEY", "sandbox")
LITEAPI_API_BASE = os.getenv("LITEAPI_API_BASE", "https://api.liteapi.travel/v3.0")
LITEAPI_BOOK_BASE = os.getenv("LITEAPI_BOOK_BASE", "https://book.liteapi.travel/v3.0")
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
DEFAULT_GUEST_NATIONALITY = os.getenv("DEFAULT_GUEST_NATIONALITY", "OM")

SITE_NAME = "Magic Sands Booking"
LOGIN_URL = "admin_login"
LOGIN_REDIRECT_URL = "admin_hub"
LOGOUT_REDIRECT_URL = "admin_login"

# Public URLs
# Hostinger (marketing): partner-login + partner-register only
# Railway (this app): booking UI, admin, gateways
MARKETING_SITE_URL = os.getenv("MARKETING_SITE_URL", "https://www.magicsandsdmc.com").rstrip("/")
PUBLIC_BOOKING_URL = os.getenv("PUBLIC_BOOKING_URL", "http://127.0.0.1:8001").rstrip("/")

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "https://www.magicsandsdmc.com,https://magicsandsdmc.com,http://127.0.0.1:8001,http://localhost:8001",
    ).split(",")
    if o.strip()
]
# Cloudflare quick tunnels (mobile / remote preview in DEBUG)
if DEBUG:
    for origin in (
        "https://*.trycloudflare.com",
        "http://*.trycloudflare.com",
    ):
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

# Email — configure SMTP later for production partner registration alerts
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in ("1", "true", "yes")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@magicsandsdmc.com")
PARTNER_REGISTRATION_NOTIFY_EMAIL = os.getenv(
    "PARTNER_REGISTRATION_NOTIFY_EMAIL",
    "oman@magicsandsdmc.com",
)
PARTNER_REGISTRATION_EMAILS_ENABLED = os.getenv(
    "PARTNER_REGISTRATION_EMAILS_ENABLED", "True"
).lower() in ("1", "true", "yes")
EMAIL_FILE_PATH = os.getenv("EMAIL_FILE_PATH", str(BASE_DIR / "tmp" / "emails"))

"""
Django settings for Magic Sands Booking.
Local development uses SQLite; production (Railway) uses PostgreSQL via DATABASE_URL.
"""

from pathlib import Path
import os
import sys

import dj_database_url
from dotenv import load_dotenv

from config.site_profile import resolve_site_profile

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


DEBUG = _env_bool("DEBUG", default=True)

ON_RAILWAY = bool(os.getenv("RAILWAY_ENVIRONMENT_NAME") or os.getenv("RAILWAY_SERVICE_ID"))

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-dev-only-change-me"
    elif "collectstatic" in sys.argv or "migrate" in sys.argv:
        SECRET_KEY = "django-insecure-railway-build-step-only"
    elif ON_RAILWAY:
        # Allow Railway boot/healthcheck; set a real SECRET_KEY in the dashboard.
        SECRET_KEY = "django-insecure-railway-set-secret-key-in-dashboard"
    else:
        raise RuntimeError("SECRET_KEY environment variable is required in production.")

_raw_hosts = _env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
if DEBUG and ("*" in _raw_hosts or not _raw_hosts):
    ALLOWED_HOSTS = ["*"]
elif DEBUG:
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
else:
    ALLOWED_HOSTS = _raw_hosts

SITE_PROFILE = resolve_site_profile(on_railway=ON_RAILWAY)
MARKETING_ONLY = SITE_PROFILE == "marketing"

if ON_RAILWAY:
    for env_name in ("RAILWAY_PUBLIC_DOMAIN", "RAILWAY_PRIVATE_DOMAIN"):
        railway_host = os.getenv(env_name, "").strip()
        if railway_host and railway_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(railway_host)
    for railway_wildcard in (".up.railway.app", ".railway.app", ".railway.internal"):
        if railway_wildcard not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(railway_wildcard)
    for internal_host in ("127.0.0.1", "localhost"):
        if internal_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(internal_host)

CSRF_TRUSTED_ORIGINS = _env_list(
    "CSRF_TRUSTED_ORIGINS",
    "https://www.magicsandsdmc.com,https://magicsandsdmc.com,http://127.0.0.1:8001,http://localhost:8001",
)
for host in ALLOWED_HOSTS:
    if host.startswith(".") or host in {"127.0.0.1", "localhost", "*"}:
        continue
    origin = f"https://{host}"
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

if DEBUG:
    for origin in ("https://*.trycloudflare.com", "http://*.trycloudflare.com"):
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

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
    "config.middleware.HealthCheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
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

database_url = os.getenv("DATABASE_URL")
if database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=600,
            ssl_require=not DEBUG,
        )
    }
else:
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
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Muscat")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

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

MARKETING_SITE_URL = os.getenv("MARKETING_SITE_URL", "https://www.magicsandsdmc.com").rstrip("/")
_default_booking_url = (
    "http://127.0.0.1:8001"
    if DEBUG
    else os.getenv("BOOKING_SITE_URL", "https://book.magicsandsdmc.com")
)
PUBLIC_BOOKING_URL = os.getenv("PUBLIC_BOOKING_URL", _default_booking_url).rstrip("/")

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", default=EMAIL_PORT != 465)
EMAIL_USE_SSL = _env_bool("EMAIL_USE_SSL", default=EMAIL_PORT == 465)
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    if EMAIL_PORT == 465:
        EMAIL_USE_TLS = False
    else:
        EMAIL_USE_SSL = False
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "30"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@magicsandsdmc.com")
PARTNER_REGISTRATION_NOTIFY_EMAIL = os.getenv(
    "PARTNER_REGISTRATION_NOTIFY_EMAIL",
    "oman@magicsandsdmc.com",
)
PARTNER_REGISTRATION_EMAILS_ENABLED = _env_bool("PARTNER_REGISTRATION_EMAILS_ENABLED", default=True)
EMAIL_FILE_PATH = os.getenv("EMAIL_FILE_PATH", str(BASE_DIR / "tmp" / "emails"))

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    # Railway terminates TLS at the edge; internal healthchecks use HTTP.
    SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", default=False)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

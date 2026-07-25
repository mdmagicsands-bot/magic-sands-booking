from django.conf import settings


def branding(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "LITEAPI_PUBLIC_KEY": settings.LITEAPI_PUBLIC_KEY,
    }

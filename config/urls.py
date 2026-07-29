from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from config.booking_redirect import redirect_to_booking_site
from config.health import health

urlpatterns = [
    path("health/", health, name="health"),
    path("django-admin/", admin.site.urls),
    path("", include("marketing.urls")),
]

if settings.MARKETING_ONLY:
    urlpatterns += [
        path("", include("partners.marketing_urls")),
        path("partner-login/", redirect_to_booking_site, name="partner_login"),
        path("gateway/partner-login/", redirect_to_booking_site),
        path("hotels/", redirect_to_booking_site),
        path("hotels/<path:rest>", redirect_to_booking_site),
        path("book/", redirect_to_booking_site),
        path("book/<path:rest>", redirect_to_booking_site),
        path("partner/", redirect_to_booking_site),
        path("partner/<path:rest>", redirect_to_booking_site),
        path("account/", redirect_to_booking_site),
        path("account/<path:rest>", redirect_to_booking_site),
    ]
else:
    urlpatterns += [
        path("", include("partners.urls")),
        path("partner/", include("guests.urls")),
        path("account/", RedirectView.as_view(url="/partner/", permanent=False)),
        path(
            "account/<path:rest>",
            RedirectView.as_view(url="/partner/%(rest)s", permanent=False),
        ),
        path("hotels/", include("hotels.urls")),
        path("book/", include("bookings.urls")),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

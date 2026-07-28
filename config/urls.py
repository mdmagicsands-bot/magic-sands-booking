from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from config.health import health

urlpatterns = [
    path("health/", health, name="health"),
    path("django-admin/", admin.site.urls),
    path("", include("partners.urls")),
    path("", include("marketing.urls")),
    # Partner front-end portal (Nuitee hotel search + user dashboard)
    path("partner/", include("guests.urls")),
    # Legacy /account/ → /partner/
    path("account/", RedirectView.as_view(url="/partner/", permanent=False)),
    path("account/<path:rest>", RedirectView.as_view(url="/partner/%(rest)s", permanent=False)),
    path("hotels/", include("hotels.urls")),
    path("book/", include("bookings.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

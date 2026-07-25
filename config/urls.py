from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("partners.urls")),
    path("", include("marketing.urls")),
    path("account/", include("guests.urls")),
    path("hotels/", include("hotels.urls")),
    path("book/", include("bookings.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

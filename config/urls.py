from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("partners.urls")),
    path("", include("marketing.urls")),
    path("hotels/", include("hotels.urls")),
    path("book/", include("bookings.urls")),
]

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("integrations.urls")),
    path("", include("organizations.urls")),
    path("", include("campaigns.urls")),
    path("", include("contributions.urls")),
    path("", include("reports.urls")),
    path("", include("accounts.urls")),
]

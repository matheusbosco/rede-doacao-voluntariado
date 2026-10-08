from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("integrations.urls")),
    path("api/v1/", include("api.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger e Redoc carregam seus assets de CDN por padrão.
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="api-docs"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="api-redoc"),
    path("", include("organizations.urls")),
    path("", include("campaigns.urls")),
    path("", include("contributions.urls")),
    path("", include("reports.urls")),
    path("", include("accounts.urls")),
]

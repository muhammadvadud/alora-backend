from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .health import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    # Health check
    path("health/", health_check, name="health_check"),
    # OpenAPI darsligi
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # API yo'llari
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/team/", include("apps.accounts.team_urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/", include("apps.usage.urls")),
    path("api/v1/pricing/", include("apps.pricing.urls")),
    path("api/v1/knowledge/", include("apps.knowledge.urls")),
    path("api/v1/", include("apps.chat.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/settings/", include("apps.prompts.urls")),
]

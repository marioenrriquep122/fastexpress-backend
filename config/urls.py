"""Rutas raíz del proyecto."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # API versionada: si cambian las reglas se crea /api/v2/ sin romper el frontend
    path("api/v1/", include("principal.urls")),
    # Documentación interactiva para Frontend y QA
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

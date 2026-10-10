"""
Rutas de la API v1. Cada módulo aporta sus propias urls.

Para agregar un módulo nuevo (p. ej. "envios"), se crea
principal/modulos/envios/ con la misma estructura y se incluye aquí.
"""

from django.urls import include, path

from principal.core.views import HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path("", include("principal.modulos.cotizaciones.urls")),
]

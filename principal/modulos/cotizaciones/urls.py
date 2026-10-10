from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.cotizacion_views import CotizacionViewSet
from .views.tarifa_views import TarifasView

router = DefaultRouter()
router.register("cotizaciones", CotizacionViewSet, basename="cotizacion")

urlpatterns = [
    path("tarifas/", TarifasView.as_view(), name="tarifas"),
    path("", include(router.urls)),
]

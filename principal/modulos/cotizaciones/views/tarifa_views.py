from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from principal.modulos.cotizaciones.services.tarifa_service import obtener_tarifas_vigentes


class TarifasView(APIView):
    """GET /api/v1/tarifas/ -> reglas vigentes para mostrarlas en el frontend."""

    @extend_schema(summary="Consultar tarifas y reglas vigentes", responses={200: dict})
    def get(self, request):
        return Response(obtener_tarifas_vigentes())

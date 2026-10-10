"""
Vistas de cotizaciones.

Flujo de cada endpoint:
    1. el serializer valida la entrada
    2. el servicio aplica la lógica de negocio (y guarda si toca)
    3. el serializer convierte el resultado a JSON

Las vistas son "delgadas": nada de cálculos aquí.
"""

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from principal.core.serializers import ErrorSerializer
from principal.modulos.cotizaciones.serializers.cotizacion_serializers import (
    CotizacionEntradaSerializer,
    CotizacionFiltroSerializer,
    CotizacionSerializer,
)
from principal.modulos.cotizaciones.services import cotizacion_service

RESPUESTAS_ERROR = {
    400: OpenApiResponse(ErrorSerializer, description="DATOS_INVALIDOS / PESO_INVALIDO"),
    422: OpenApiResponse(ErrorSerializer, description="LIMITE_EXCEDIDO (peso > 20 kg)"),
}


class CotizacionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    - GET  /api/v1/cotizaciones/           lista (filtros: ?tipo_cliente=VIP&tipo_envio=EXPRESS)
    - GET  /api/v1/cotizaciones/{id}/      detalle
    - POST /api/v1/cotizaciones/           calcula y GUARDA
    - POST /api/v1/cotizaciones/calcular/  calcula SIN guardar

    No hay PUT/PATCH/DELETE: una cotización emitida es un registro histórico.
    """

    serializer_class = CotizacionSerializer

    def get_queryset(self):
        filtros = CotizacionFiltroSerializer(data=self.request.query_params)
        filtros.is_valid(raise_exception=True)
        return cotizacion_service.listar_cotizaciones(**filtros.validated_data)

    @extend_schema(summary="Listar cotizaciones", parameters=[CotizacionFiltroSerializer])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Detalle de una cotización")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Calcular y registrar una cotización",
        request=CotizacionEntradaSerializer,
        responses={201: CotizacionSerializer, **RESPUESTAS_ERROR},
    )
    def create(self, request, *args, **kwargs):
        entrada = CotizacionEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        cotizacion = cotizacion_service.registrar_cotizacion(
            entrada.validated_data["peso_kg"],
            entrada.validated_data["tipo_cliente"],
            entrada.validated_data["tipo_envio"],
        )
        return Response(CotizacionSerializer(cotizacion).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Simular una cotización (no se guarda)",
        request=CotizacionEntradaSerializer,
        responses={200: CotizacionSerializer, **RESPUESTAS_ERROR},
    )
    @action(detail=False, methods=["post"])
    def calcular(self, request):
        entrada = CotizacionEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        cotizacion = cotizacion_service.simular_cotizacion(
            entrada.validated_data["peso_kg"],
            entrada.validated_data["tipo_cliente"],
            entrada.validated_data["tipo_envio"],
        )
        return Response(CotizacionSerializer(cotizacion).data)

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
RESPUESTA_404 = {404: OpenApiResponse(ErrorSerializer, description="La cotización no existe")}

# Acciones en las que el cuerpo de la petición son los 3 datos de entrada
ACCIONES_CON_ENTRADA = ("create", "update", "partial_update", "calcular")


class CotizacionViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    CRUD de cotizaciones (base: /api/v1/cotizaciones/).

    - GET    /                lista paginada (filtros: ?tipo_cliente=VIP&tipo_envio=EXPRESS)
    - GET    /{id}/           detalle
    - POST   /                calcula y GUARDA
    - PUT    /{id}/           reemplaza los 3 datos de entrada y RECALCULA
    - PATCH  /{id}/           cambia solo algunos datos de entrada y RECALCULA
    - DELETE /{id}/           elimina (204 sin cuerpo)
    - POST   /calcular/       calcula SIN guardar (vista previa)

    El cliente nunca envía totales, descuentos ni recargos: solo peso, tipo de
    cliente y tipo de envío. El desglose siempre lo calcula el servidor.
    """

    serializer_class = CotizacionSerializer

    def get_serializer_class(self):
        # En escritura se reciben solo los 3 datos de entrada; en lectura se devuelve el desglose.
        # Esto también hace que la API navegable de DRF y Swagger muestren el formulario correcto.
        if self.action in ACCIONES_CON_ENTRADA:
            return CotizacionEntradaSerializer
        return CotizacionSerializer

    def get_queryset(self):
        filtros = CotizacionFiltroSerializer(data=self.request.query_params)
        filtros.is_valid(raise_exception=True)
        return cotizacion_service.listar_cotizaciones(**filtros.validated_data)

    @extend_schema(summary="Listar cotizaciones", parameters=[CotizacionFiltroSerializer])
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Detalle de una cotización",
        responses={200: CotizacionSerializer, **RESPUESTA_404},
    )
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
        summary="Actualizar una cotización (PUT: los 3 datos son obligatorios; PATCH: solo los que cambian)",
        request=CotizacionEntradaSerializer,
        responses={200: CotizacionSerializer, **RESPUESTAS_ERROR, **RESPUESTA_404},
    )
    def update(self, request, *args, **kwargs):
        # partial_update (PATCH) del mixin llama a este método con partial=True
        parcial = kwargs.pop("partial", False)
        cotizacion = self.get_object()

        entrada = CotizacionEntradaSerializer(data=request.data, partial=parcial)
        entrada.is_valid(raise_exception=True)

        # En PATCH, lo que no se envía conserva el valor actual
        datos = {
            "peso_kg": cotizacion.peso_kg,
            "tipo_cliente": cotizacion.tipo_cliente,
            "tipo_envio": cotizacion.tipo_envio,
            **entrada.validated_data,
        }
        cotizacion = cotizacion_service.actualizar_cotizacion(
            cotizacion,
            datos["peso_kg"],
            datos["tipo_cliente"],
            datos["tipo_envio"],
        )
        return Response(CotizacionSerializer(cotizacion).data)

    @extend_schema(
        summary="Eliminar una cotización",
        request=None,
        responses={204: None, **RESPUESTA_404},
    )
    def destroy(self, request, *args, **kwargs):
        cotizacion_service.eliminar_cotizacion(self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

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

"""
Serializers del módulo de cotizaciones.

- CotizacionEntradaSerializer: valida el FORMATO de lo que manda el frontend.
- CotizacionFiltroSerializer: valida los filtros del listado.
- CotizacionSerializer: convierte el modelo Cotizacion a JSON.

Las REGLAS DE NEGOCIO (peso > 0 y <= 20 kg) las valida el servicio. Por eso
25 kg pasa el serializer y el servicio lo rechaza con LIMITE_EXCEDIDO (422).
"""

from rest_framework import serializers

from principal.constantes.cotizacion import TipoCliente, TipoEnvio
from principal.modelos import Cotizacion


class CotizacionEntradaSerializer(serializers.Serializer):
    peso_kg = serializers.DecimalField(
        label="Peso (kg)",
        max_digits=8,
        decimal_places=2,
        help_text="Peso del paquete en kg. Rango válido: 0.01 a 20.00.",
    )
    tipo_cliente = serializers.ChoiceField(
        label="Tipo de cliente",
        choices=TipoCliente.choices,
        help_text="NUEVO (0 %), FRECUENTE (10 %) o VIP (20 %) de descuento.",
    )
    tipo_envio = serializers.ChoiceField(
        label="Tipo de envío",
        choices=TipoEnvio.choices,
        help_text="ESTANDAR (sin recargo) o EXPRESS (+25 % sobre el subtotal).",
    )


class CotizacionFiltroSerializer(serializers.Serializer):
    """
    Valida los query params del listado GET /cotizaciones/.

    Paginación (DRF, no en este serializer): ?page=1&page_size=20 (máx. 100).
    """

    id = serializers.IntegerField(label="ID de cotización", min_value=1, required=False)
    peso_kg = serializers.DecimalField(
        label="Peso (kg)",
        max_digits=8,
        decimal_places=2,
        required=False,
        help_text="Coincidencia exacta (ej. 10.00).",
    )
    creado_en = serializers.DateField(
        label="Fecha de creación",
        required=False,
        help_text="Día calendario ISO (YYYY-MM-DD); filtra cotizaciones creadas ese día.",
    )
    tipo_cliente = serializers.ChoiceField(label="Tipo de cliente", choices=TipoCliente.choices, required=False)
    tipo_envio = serializers.ChoiceField(label="Tipo de envío", choices=TipoEnvio.choices, required=False)


class CotizacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotizacion
        fields = [
            "id",
            "peso_kg",
            "tipo_cliente",
            "tipo_envio",
            "costo_base",
            "tarifa_por_kg",
            "costo_peso",
            "subtotal",
            "porcentaje_descuento",
            "descuento",
            "porcentaje_recargo",
            "recargo",
            "total",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = fields

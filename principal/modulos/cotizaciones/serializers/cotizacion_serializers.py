"""
Serializers del módulo de cotizaciones.

- CotizacionEntradaSerializer: valida el FORMATO de lo que manda el frontend.
- CotizacionSerializer: convierte el modelo Cotizacion a JSON.

Las REGLAS DE NEGOCIO (peso > 0 y <= 20 kg) las valida el servicio. Por eso
25 kg pasa el serializer y el servicio lo rechaza con LIMITE_EXCEDIDO (422).
"""

from rest_framework import serializers

from principal.constantes.cotizacion import TipoCliente, TipoEnvio
from principal.modelos import Cotizacion


class CotizacionEntradaSerializer(serializers.Serializer):
    peso_kg = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Peso del paquete en kg. Rango válido: 0.01 a 20.00.",
    )
    tipo_cliente = serializers.ChoiceField(choices=TipoCliente.choices)
    tipo_envio = serializers.ChoiceField(choices=TipoEnvio.choices)


class CotizacionFiltroSerializer(serializers.Serializer):
    """Valida los filtros del listado (?tipo_cliente=VIP&tipo_envio=EXPRESS)."""

    tipo_cliente = serializers.ChoiceField(choices=TipoCliente.choices, required=False)
    tipo_envio = serializers.ChoiceField(choices=TipoEnvio.choices, required=False)


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
        ]
        read_only_fields = fields

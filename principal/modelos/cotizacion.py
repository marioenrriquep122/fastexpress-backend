"""
Tabla `cotizaciones`.

Se guarda el desglose completo (no solo el total) para tener trazabilidad:
si mañana cambian las tarifas, las cotizaciones viejas conservan los
valores con los que se calcularon.
"""

from decimal import Decimal

from django.db import models

from principal.constantes.cotizacion import PESO_MAXIMO_KG, PESO_MINIMO_KG, TipoCliente, TipoEnvio

from .base import ModeloBase


class Cotizacion(ModeloBase):
    # Datos que envía el usuario
    peso_kg = models.DecimalField("peso (kg)", max_digits=5, decimal_places=2)
    tipo_cliente = models.CharField(max_length=10, choices=TipoCliente.choices)
    tipo_envio = models.CharField(max_length=10, choices=TipoEnvio.choices)

    # Desglose calculado por el servicio
    costo_base = models.DecimalField(max_digits=10, decimal_places=2)
    tarifa_por_kg = models.DecimalField(max_digits=10, decimal_places=2)
    costo_peso = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    porcentaje_descuento = models.DecimalField(max_digits=4, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2)
    porcentaje_recargo = models.DecimalField(max_digits=4, decimal_places=2)
    recargo = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "cotizaciones"
        verbose_name = "cotización"
        verbose_name_plural = "cotizaciones"
        ordering = ["-creado_en", "-id"]
        indexes = [models.Index(fields=["tipo_cliente", "tipo_envio"], name="idx_cotizacion_tipos")]
        # Defensa en profundidad: la BD también rechaza datos fuera de las reglas
        constraints = [
            models.CheckConstraint(
                condition=models.Q(peso_kg__gte=PESO_MINIMO_KG, peso_kg__lte=PESO_MAXIMO_KG),
                name="cotizacion_peso_en_rango",
            ),
            models.CheckConstraint(
                condition=models.Q(tipo_cliente__in=TipoCliente.values),
                name="cotizacion_tipo_cliente_valido",
            ),
            models.CheckConstraint(
                condition=models.Q(tipo_envio__in=TipoEnvio.values),
                name="cotizacion_tipo_envio_valido",
            ),
            models.CheckConstraint(
                condition=models.Q(total__gte=Decimal("0")),
                name="cotizacion_total_no_negativo",
            ),
        ]

    def __str__(self) -> str:
        return f"#{self.pk} - {self.peso_kg} kg {self.tipo_cliente}/{self.tipo_envio} = ${self.total}"

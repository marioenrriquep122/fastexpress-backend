"""
Constantes de negocio del módulo de cotizaciones (BR-01 a BR-04).

Están en principal/constantes/ (y no dentro del módulo) porque las usan
tanto los modelos (restricciones de la BD) como los servicios (cálculo).
Si cambia una tarifa, se cambia solo aquí.
"""

from decimal import Decimal

from django.db import models


class TipoCliente(models.TextChoices):
    """BR-03: tipos de cliente."""

    NUEVO = "NUEVO", "Nuevo"
    FRECUENTE = "FRECUENTE", "Frecuente"
    VIP = "VIP", "VIP"


class TipoEnvio(models.TextChoices):
    """BR-04: tipos de envío."""

    ESTANDAR = "ESTANDAR", "Estándar"
    EXPRESS = "EXPRESS", "Express"


# BR-01: costo base de toda orden (USD)
COSTO_BASE = Decimal("5.00")

# BR-02: cálculo por peso
PESO_MINIMO_KG = Decimal("0.01")
LIMITE_TRAMO_LIGERO_KG = Decimal("5.00")  # 0.01 a 5.00 kg  -> 2.00 por kg
PESO_MAXIMO_KG = Decimal("20.00")  # 5.01 a 20.00 kg -> 4.00 por kg
TARIFA_KG_LIGERO = Decimal("2.00")
TARIFA_KG_PESADO = Decimal("4.00")

# BR-03: descuento por tipo de cliente
DESCUENTO_NUEVO = Decimal("0.00")
DESCUENTO_FRECUENTE = Decimal("0.10")
DESCUENTO_VIP = Decimal("0.20")

# BR-04: recargo por tipo de envío
RECARGO_ESTANDAR = Decimal("0.00")
RECARGO_EXPRESS = Decimal("0.25")

# Precisión monetaria
CENTAVO = Decimal("0.01")

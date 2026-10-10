"""
PRUEBAS DE CAJA BLANCA - Cobertura de caminos independientes.

Función bajo prueba: principal/modulos/cotizaciones/services/calculadora_service.py -> calcular_cotizacion
Complejidad ciclomática: V(G) = 9  (ver docs/CAJA_BLANCA.md)
=> Se necesitan 9 casos, uno por cada camino independiente (C1..C9).
"""

from decimal import Decimal

import pytest

from principal.modulos.cotizaciones.exceptions import (
    LimiteExcedidoError,
    PesoInvalidoError,
    TipoClienteInvalidoError,
    TipoEnvioInvalidoError,
)
from principal.modulos.cotizaciones.services.calculadora_service import calcular_cotizacion

pytestmark = pytest.mark.caja_blanca


def test_C1_peso_cero_o_negativo_es_rechazado():
    """C1: N1 -> N2 -> FIN  (D1 verdadero)"""
    with pytest.raises(PesoInvalidoError):
        calcular_cotizacion(Decimal("0"), "NUEVO", "ESTANDAR")


def test_C2_peso_mayor_a_20_es_rechazado():
    """C2: N1 -> N3 -> N4 -> FIN  (D2 verdadero)"""
    with pytest.raises(LimiteExcedidoError):
        calcular_cotizacion(Decimal("20.01"), "NUEVO", "ESTANDAR")


def test_C3_camino_base_ligero_nuevo_estandar():
    """C3: N1-N3-N5-N6-N8-N9-N15-N16-N20-N21  (camino base)"""
    r = calcular_cotizacion(Decimal("2.00"), "NUEVO", "ESTANDAR")
    assert r["tarifa_por_kg"] == Decimal("2.00")
    assert r["subtotal"] == Decimal("9.00")
    assert r["total"] == Decimal("9.00")


def test_C4_tramo_pesado():
    """C4: ...N5 -> N7 (D3 falso)..."""
    r = calcular_cotizacion(Decimal("10.00"), "NUEVO", "ESTANDAR")
    assert r["tarifa_por_kg"] == Decimal("4.00")
    assert r["total"] == Decimal("45.00")


def test_C5_cliente_frecuente():
    """C5: ...N8 -> N10 -> N11 (D4 falso, D5 verdadero)..."""
    r = calcular_cotizacion(Decimal("2.00"), "FRECUENTE", "ESTANDAR")
    assert r["descuento"] == Decimal("0.90")
    assert r["total"] == Decimal("8.10")


def test_C6_cliente_vip():
    """C6: ...N10 -> N12 -> N13 (D5 falso, D6 verdadero)..."""
    r = calcular_cotizacion(Decimal("2.00"), "VIP", "ESTANDAR")
    assert r["descuento"] == Decimal("1.80")
    assert r["total"] == Decimal("7.20")


def test_C7_tipo_cliente_invalido():
    """C7: ...N12 -> N14 -> FIN (D6 falso)"""
    with pytest.raises(TipoClienteInvalidoError):
        calcular_cotizacion(Decimal("2.00"), "PREMIUM", "ESTANDAR")


def test_C8_envio_express():
    """C8: ...N15 -> N17 -> N18 -> N20 (D7 falso, D8 verdadero)"""
    r = calcular_cotizacion(Decimal("2.00"), "NUEVO", "EXPRESS")
    assert r["recargo"] == Decimal("2.25")
    assert r["total"] == Decimal("11.25")


def test_C9_tipo_envio_invalido():
    """C9: ...N17 -> N19 -> FIN (D8 falso)"""
    with pytest.raises(TipoEnvioInvalidoError):
        calcular_cotizacion(Decimal("2.00"), "NUEVO", "AEREO")

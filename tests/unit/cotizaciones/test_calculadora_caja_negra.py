"""
PRUEBAS DE CAJA NEGRA sobre la calculadora.

Se diseñan SOLO desde la especificación (BR-01 a BR-04), sin mirar el código:
- Particiones de Equivalencia (PE) del peso
- Análisis de Valores Límite (BVA) del peso
- Valores límite del monto total resultante
- Tabla de Decisión: Tipo de Cliente x Tipo de Envío

Los IDs (PE-xx, BVA-xx, TD-xx) coinciden con docs/CAJA_NEGRA.md.
"""

from decimal import Decimal

import pytest

from principal.modulos.cotizaciones.exceptions import LimiteExcedidoError, PesoInvalidoError
from principal.modulos.cotizaciones.services.calculadora_service import calcular_cotizacion, redondear

pytestmark = pytest.mark.caja_negra


# ---------------------------------------------------------------------------
# Particiones de Equivalencia - Peso (cliente NUEVO, envío ESTANDAR)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "caso, peso, total_esperado",
    [
        ("PE-02 tramo ligero (0.01-5.00)", "3.00", "11.00"),
        ("PE-03 tramo pesado (5.01-20.00)", "12.00", "53.00"),
    ],
)
def test_particiones_validas_peso(caso, peso, total_esperado):
    assert calcular_cotizacion(Decimal(peso), "NUEVO", "ESTANDAR")["total"] == Decimal(total_esperado)


@pytest.mark.parametrize(
    "caso, peso, excepcion",
    [
        ("PE-01 peso negativo", "-3.00", PesoInvalidoError),
        ("PE-04 peso mayor a 20", "35.00", LimiteExcedidoError),
    ],
)
def test_particiones_invalidas_peso(caso, peso, excepcion):
    with pytest.raises(excepcion):
        calcular_cotizacion(Decimal(peso), "NUEVO", "ESTANDAR")


# ---------------------------------------------------------------------------
# BVA - Peso (cliente NUEVO, envío ESTANDAR)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "caso, peso, tarifa, total",
    [
        ("BVA-02 minimo", "0.01", "2.00", "5.02"),
        ("BVA-03 minimo+", "0.02", "2.00", "5.04"),
        ("BVA-04 limite ligero-", "4.99", "2.00", "14.98"),
        ("BVA-05 limite ligero", "5.00", "2.00", "15.00"),
        ("BVA-06 limite pesado", "5.01", "4.00", "25.04"),
        ("BVA-07 limite pesado+", "5.02", "4.00", "25.08"),
        ("BVA-08 maximo-", "19.99", "4.00", "84.96"),
        ("BVA-09 maximo", "20.00", "4.00", "85.00"),
    ],
)
def test_bva_peso_valido(caso, peso, tarifa, total):
    r = calcular_cotizacion(Decimal(peso), "NUEVO", "ESTANDAR")
    assert r["tarifa_por_kg"] == Decimal(tarifa)
    assert r["total"] == Decimal(total)


def test_bva_01_peso_cero_invalido():
    with pytest.raises(PesoInvalidoError):
        calcular_cotizacion(Decimal("0.00"), "NUEVO", "ESTANDAR")


def test_bva_10_peso_justo_sobre_el_maximo_rechazado():
    with pytest.raises(LimiteExcedidoError):
        calcular_cotizacion(Decimal("20.01"), "NUEVO", "ESTANDAR")


# ---------------------------------------------------------------------------
# BVA - Monto total (extremos posibles del resultado)
# ---------------------------------------------------------------------------
def test_monto_minimo_posible():
    """BVA-M1: menor peso + mayor descuento + sin recargo."""
    assert calcular_cotizacion(Decimal("0.01"), "VIP", "ESTANDAR")["total"] == Decimal("4.02")


def test_monto_maximo_posible():
    """BVA-M2: mayor peso + sin descuento + con recargo."""
    assert calcular_cotizacion(Decimal("20.00"), "NUEVO", "EXPRESS")["total"] == Decimal("106.25")


def test_monto_nunca_es_negativo_ni_cero():
    for peso in ("0.01", "5.00", "5.01", "20.00"):
        for cliente in ("NUEVO", "FRECUENTE", "VIP"):
            for envio in ("ESTANDAR", "EXPRESS"):
                assert calcular_cotizacion(Decimal(peso), cliente, envio)["total"] > 0


# ---------------------------------------------------------------------------
# Tabla de Decisión: Tipo de Cliente x Tipo de Envío (peso 10 kg, subtotal 45)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "regla, cliente, envio, descuento, recargo, total",
    [
        ("TD-01", "NUEVO", "ESTANDAR", "0.00", "0.00", "45.00"),
        ("TD-02", "NUEVO", "EXPRESS", "0.00", "11.25", "56.25"),
        ("TD-03", "FRECUENTE", "ESTANDAR", "4.50", "0.00", "40.50"),
        ("TD-04", "FRECUENTE", "EXPRESS", "4.50", "11.25", "51.75"),
        ("TD-05", "VIP", "ESTANDAR", "9.00", "0.00", "36.00"),
        ("TD-06", "VIP", "EXPRESS", "9.00", "11.25", "47.25"),
    ],
)
def test_tabla_decision(regla, cliente, envio, descuento, recargo, total):
    r = calcular_cotizacion(Decimal("10.00"), cliente, envio)
    assert r["subtotal"] == Decimal("45.00")
    assert r["descuento"] == Decimal(descuento)
    assert r["recargo"] == Decimal(recargo)
    assert r["total"] == Decimal(total)


# ---------------------------------------------------------------------------
# Redondeo monetario
# ---------------------------------------------------------------------------
def test_redondeo_half_up():
    assert redondear(Decimal("1.005")) == Decimal("1.01")
    assert redondear(Decimal("1.004")) == Decimal("1.00")


def test_redondeo_en_descuento_con_tres_decimales():
    # 0.03 kg -> subtotal 5.06; FRECUENTE 10% = 0.506 -> 0.51; total 4.55
    r = calcular_cotizacion(Decimal("0.03"), "FRECUENTE", "ESTANDAR")
    assert r["descuento"] == Decimal("0.51")
    assert r["total"] == Decimal("4.55")


def test_acepta_peso_como_string_o_entero():
    assert calcular_cotizacion("2.5", "NUEVO", "ESTANDAR")["total"] == Decimal("10.00")
    assert calcular_cotizacion(3, "NUEVO", "ESTANDAR")["total"] == Decimal("11.00")

"""Pruebas del servicio de cotizaciones, el modelo, las restricciones de la BD y los signals."""

from decimal import Decimal

import pytest
from django.db import IntegrityError

from principal.modelos import Cotizacion
from principal.modulos.cotizaciones.exceptions import LimiteExcedidoError
from principal.modulos.cotizaciones.services import cotizacion_service as services

pytestmark = pytest.mark.django_db


def test_registrar_cotizacion_persiste_desglose_completo():
    c = services.registrar_cotizacion(Decimal("10.00"), "VIP", "EXPRESS")
    c.refresh_from_db()
    assert c.subtotal == Decimal("45.00")
    assert c.descuento == Decimal("9.00")
    assert c.recargo == Decimal("11.25")
    assert c.total == Decimal("47.25")
    assert str(c) == f"#{c.pk} - 10.00 kg VIP/EXPRESS = $47.25"


def test_registrar_cotizacion_invalida_no_deja_registro():
    with pytest.raises(LimiteExcedidoError):
        services.registrar_cotizacion(Decimal("25.00"), "NUEVO", "ESTANDAR")
    assert Cotizacion.objects.count() == 0


def test_simular_cotizacion_devuelve_instancia_sin_guardar():
    c = services.simular_cotizacion(Decimal("1.00"), "NUEVO", "ESTANDAR")
    assert c.pk is None
    assert c.total == Decimal("7.00")
    assert Cotizacion.objects.count() == 0


def test_listar_cotizaciones_con_filtros():
    services.registrar_cotizacion(Decimal("1.00"), "NUEVO", "ESTANDAR")
    services.registrar_cotizacion(Decimal("1.00"), "VIP", "EXPRESS")
    services.registrar_cotizacion(Decimal("1.00"), "VIP", "ESTANDAR")

    assert services.listar_cotizaciones().count() == 3
    assert services.listar_cotizaciones(tipo_cliente="VIP").count() == 2
    assert services.listar_cotizaciones(tipo_envio="EXPRESS").count() == 1
    assert services.listar_cotizaciones(tipo_cliente="VIP", tipo_envio="ESTANDAR").count() == 1

    vip = services.listar_cotizaciones(tipo_cliente="VIP").first()
    assert services.listar_cotizaciones(pk=vip.pk).count() == 1
    assert services.listar_cotizaciones(peso_kg=Decimal("1.00")).count() == 3


def _datos_base(**cambios):
    datos = dict(
        peso_kg=Decimal("1.00"), tipo_cliente="NUEVO", tipo_envio="ESTANDAR",
        costo_base=Decimal("5.00"), tarifa_por_kg=Decimal("2.00"), costo_peso=Decimal("2.00"),
        subtotal=Decimal("7.00"), porcentaje_descuento=Decimal("0"), descuento=Decimal("0"),
        porcentaje_recargo=Decimal("0"), recargo=Decimal("0"), total=Decimal("7.00"),
    )
    datos.update(cambios)
    return datos


@pytest.mark.parametrize(
    "cambio",
    [
        {"peso_kg": Decimal("25.00")},
        {"peso_kg": Decimal("0.00")},
        {"tipo_cliente": "PREMIUM"},
        {"tipo_envio": "AEREO"},
        {"total": Decimal("-1.00")},
    ],
)
def test_base_de_datos_rechaza_datos_fuera_de_reglas(cambio):
    """Defensa en profundidad: aunque alguien se salte la API, la BD protege."""
    with pytest.raises(IntegrityError):
        Cotizacion.objects.create(**_datos_base(**cambio))


def test_signal_registra_en_log_al_emitir_cotizacion(caplog):
    with caplog.at_level("INFO", logger="principal"):
        c = services.registrar_cotizacion(Decimal("2.00"), "NUEVO", "ESTANDAR")
    assert f"Cotización emitida #{c.pk}" in caplog.text


def test_signal_no_registra_al_actualizar(caplog):
    c = services.registrar_cotizacion(Decimal("2.00"), "NUEVO", "ESTANDAR")
    with caplog.at_level("INFO", logger="principal"):
        c.save()
    assert "Cotización emitida" not in caplog.text

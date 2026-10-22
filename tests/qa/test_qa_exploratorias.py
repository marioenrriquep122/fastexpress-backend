"""
PRUEBAS DE QA (independientes del equipo de backend).

Casos adicionales disenados por QA a partir de la especificacion y de pruebas
exploratorias. Los IDs (QA-xx, DEF-xxx) coinciden con el Informe Tecnico de Calidad.

- Los casos que documentan un DEFECTO abierto se marcan xfail(strict=True):
  la suite sigue verde, pero si alguien corrige el defecto la prueba pasa a
  XPASS y falla, avisando que hay que quitar la marca y cerrar el defecto.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from principal.modelos import Cotizacion
from principal.modulos.cotizaciones.exceptions import PesoInvalidoError
from principal.modulos.cotizaciones.services.calculadora_service import calcular_cotizacion

URL_LISTA = reverse("cotizacion-list")
URL_CALCULAR = reverse("cotizacion-calcular")


def detalle(pk):
    return reverse("cotizacion-detail", args=[pk])


def entrada(peso, cliente="NUEVO", envio="ESTANDAR"):
    return {"peso_kg": peso, "tipo_cliente": cliente, "tipo_envio": envio}


# ===========================================================================
# 1. Caja negra a nivel HTTP: particiones y limites de PESO por la API
# ===========================================================================
@pytest.mark.caja_negra
@pytest.mark.django_db
@pytest.mark.parametrize(
    "caso, peso, status, codigo",
    [
        ("QA-01 peso 0.00 (limite inferior - 1)", "0.00", 400, "PESO_INVALIDO"),
        ("QA-02 peso negativo -0.01", "-0.01", 400, "PESO_INVALIDO"),
        ("QA-03 peso con 3 decimales 0.001", "0.001", 400, "DATOS_INVALIDOS"),
        ("QA-04 peso 20.01 (limite superior + 1)", "20.01", 422, "LIMITE_EXCEDIDO"),
        ("QA-05 peso enorme 999999.99", "999999.99", 422, "LIMITE_EXCEDIDO"),
        ("QA-06 peso con 7 digitos enteros", "1000000", 400, "DATOS_INVALIDOS"),
        ("QA-07 peso texto vacio", "", 400, "DATOS_INVALIDOS"),
        ("QA-08 peso NaN", "NaN", 400, "DATOS_INVALIDOS"),
        ("QA-09 peso booleano", True, 400, "DATOS_INVALIDOS"),
    ],
)
def test_api_peso_invalido(api_client, caso, peso, status, codigo):
    resp = api_client.post(URL_LISTA, entrada(peso), format="json")
    assert resp.status_code == status, caso
    assert resp.data["codigo"] == codigo
    assert Cotizacion.objects.count() == 0  # un error nunca debe guardar


@pytest.mark.caja_negra
@pytest.mark.django_db
@pytest.mark.parametrize(
    "caso, peso, tarifa, total",
    [
        ("QA-10 minimo 0.01", "0.01", "2.00", "5.02"),
        ("QA-11 limite ligero 5.00", "5.00", "2.00", "15.00"),
        ("QA-12 primer valor pesado 5.01", "5.01", "4.00", "25.04"),
        ("QA-13 maximo 20.00", "20.00", "4.00", "85.00"),
    ],
)
def test_api_peso_limites_validos(api_client, caso, peso, tarifa, total):
    resp = api_client.post(URL_CALCULAR, entrada(peso), format="json")
    assert resp.status_code == 200, caso
    assert resp.data["tarifa_por_kg"] == tarifa
    assert resp.data["total"] == total


# ===========================================================================
# 2. Caja negra HTTP: tipos de cliente / envio
# ===========================================================================
@pytest.mark.caja_negra
@pytest.mark.django_db
@pytest.mark.parametrize(
    "caso, cliente, envio, campo",
    [
        ("QA-14 cliente en minusculas", "vip", "ESTANDAR", "tipo_cliente"),
        ("QA-15 cliente vacio", "", "ESTANDAR", "tipo_cliente"),
        ("QA-16 envio en minusculas", "VIP", "express", "tipo_envio"),
        ("QA-17 envio inexistente", "VIP", "AEREO", "tipo_envio"),
    ],
)
def test_api_tipos_invalidos(api_client, caso, cliente, envio, campo):
    resp = api_client.post(URL_LISTA, entrada("2.00", cliente, envio), format="json")
    assert resp.status_code == 400, caso
    assert resp.data["codigo"] == "DATOS_INVALIDOS"
    assert campo in resp.data["detalle"]


# ===========================================================================
# 3. Combinacion de reglas en el punto critico 5.01 kg (tabla de decision x BVA)
# ===========================================================================
@pytest.mark.caja_negra
@pytest.mark.parametrize(
    "caso, cliente, envio, descuento, recargo, total",
    [
        # subtotal = 5.00 + 5.01*4.00 = 25.04
        ("QA-18", "NUEVO", "ESTANDAR", "0.00", "0.00", "25.04"),
        ("QA-19", "NUEVO", "EXPRESS", "0.00", "6.26", "31.30"),
        ("QA-20", "FRECUENTE", "ESTANDAR", "2.50", "0.00", "22.54"),
        ("QA-21", "FRECUENTE", "EXPRESS", "2.50", "6.26", "28.80"),
        ("QA-22", "VIP", "ESTANDAR", "5.01", "0.00", "20.03"),
        ("QA-23", "VIP", "EXPRESS", "5.01", "6.26", "26.29"),
    ],
)
def test_tabla_decision_en_limite_5_01(caso, cliente, envio, descuento, recargo, total):
    r = calcular_cotizacion(Decimal("5.01"), cliente, envio)
    assert r["subtotal"] == Decimal("25.04")
    assert r["descuento"] == Decimal(descuento), caso
    assert r["recargo"] == Decimal(recargo), caso
    assert r["total"] == Decimal(total), caso


# ===========================================================================
# 4. Seguridad funcional: el cliente no puede imponer el total
# ===========================================================================
@pytest.mark.api
@pytest.mark.django_db
def test_QA_24_campos_calculados_enviados_por_cliente_se_ignoran(api_client):
    body = {**entrada("10.00", "VIP", "EXPRESS"), "total": "0.01", "descuento": "999"}
    resp = api_client.post(URL_LISTA, body, format="json")
    assert resp.status_code == 201
    assert resp.data["total"] == "47.25"


# ===========================================================================
# 5. Ciclo de vida CRUD (PUT/PATCH recalculan, errores no corrompen datos)
# ===========================================================================
@pytest.mark.api
@pytest.mark.django_db
def test_QA_25_patch_recalcula_solo_lo_enviado(api_client):
    pk = api_client.post(URL_LISTA, entrada("2.00"), format="json").data["id"]
    resp = api_client.patch(detalle(pk), {"tipo_envio": "EXPRESS"}, format="json")
    assert resp.status_code == 200
    assert resp.data["peso_kg"] == "2.00"
    assert resp.data["total"] == "11.25"


@pytest.mark.api
@pytest.mark.django_db
def test_QA_26_patch_con_peso_excedido_no_modifica_registro(api_client):
    pk = api_client.post(URL_LISTA, entrada("2.00"), format="json").data["id"]
    resp = api_client.patch(detalle(pk), {"peso_kg": "25.00"}, format="json")
    assert resp.status_code == 422
    assert api_client.get(detalle(pk)).data["total"] == "9.00"


@pytest.mark.api
@pytest.mark.django_db
def test_QA_27_put_sin_todos_los_campos_es_rechazado(api_client):
    pk = api_client.post(URL_LISTA, entrada("2.00"), format="json").data["id"]
    resp = api_client.put(detalle(pk), {"peso_kg": "3.00"}, format="json")
    assert resp.status_code == 400


@pytest.mark.api
@pytest.mark.django_db
def test_QA_28_json_mal_formado(api_client):
    resp = api_client.post(URL_LISTA, "no es json", content_type="application/json")
    assert resp.status_code == 400
    assert resp.data["codigo"] == "PARSE_ERROR"


@pytest.mark.api
@pytest.mark.django_db
def test_QA_29_delete_de_inexistente_es_404(api_client):
    assert api_client.delete(detalle(999999)).status_code == 404


# ===========================================================================
# 6. Defectos abiertos en la funcion core (caja blanca)
# ===========================================================================
@pytest.mark.caja_blanca
def test_QA_30_core_rechaza_peso_menor_al_minimo():
    """DEF-001 cerrado: el core aplica PESO_MINIMO_KG (0.01 kg)."""
    with pytest.raises(PesoInvalidoError):
        calcular_cotizacion("0.001", "NUEVO", "ESTANDAR")


@pytest.mark.caja_blanca
def test_QA_31_core_rechaza_nan_con_error_de_negocio():
    """DEF-002 cerrado: NaN se rechaza con PesoInvalidoError."""
    with pytest.raises(PesoInvalidoError):
        calcular_cotizacion("NaN", "NUEVO", "ESTANDAR")

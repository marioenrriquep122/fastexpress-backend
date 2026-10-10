"""
PRUEBAS DE INTEGRACIÓN DE LA API (caja negra a nivel HTTP).

Verifican que los endpoints respondan con el status y formato correctos,
que se guarde en la base de datos cuando corresponde y que los errores
salgan con el formato estándar {"codigo", "detalle"}.
"""

from decimal import Decimal

import pytest
from django.urls import reverse

from principal.modelos import Cotizacion

pytestmark = [pytest.mark.api, pytest.mark.django_db]

URL_LISTA = reverse("cotizacion-list")
URL_CALCULAR = reverse("cotizacion-calcular")
URL_TARIFAS = reverse("tarifas")


# ---------------------------------------------------------------------------
# POST /cotizaciones/calcular/  (simulación, no guarda)
# ---------------------------------------------------------------------------
def test_calcular_devuelve_desglose_y_no_guarda(api_client, payload_valido):
    resp = api_client.post(URL_CALCULAR, payload_valido, format="json")

    assert resp.status_code == 200
    assert resp.data["subtotal"] == "45.00"
    assert resp.data["descuento"] == "4.50"
    assert resp.data["recargo"] == "11.25"
    assert resp.data["total"] == "51.75"
    assert Cotizacion.objects.count() == 0


# ---------------------------------------------------------------------------
# POST /cotizaciones/  (calcula y guarda)
# ---------------------------------------------------------------------------
def test_crear_guarda_en_base_de_datos(api_client, payload_valido):
    resp = api_client.post(URL_LISTA, payload_valido, format="json")

    assert resp.status_code == 201
    assert resp.data["id"] is not None
    assert resp.data["total"] == "51.75"
    guardada = Cotizacion.objects.get(pk=resp.data["id"])
    assert guardada.total == Decimal("51.75")
    assert guardada.tipo_cliente == "FRECUENTE"


@pytest.mark.parametrize(
    "peso, codigo_http, codigo_error",
    [
        ("0.00", 400, "PESO_INVALIDO"),
        ("-1.00", 400, "PESO_INVALIDO"),
        ("20.01", 422, "LIMITE_EXCEDIDO"),
        ("100.00", 422, "LIMITE_EXCEDIDO"),
    ],
)
def test_crear_rechaza_peso_fuera_de_rango_sin_guardar(api_client, peso, codigo_http, codigo_error):
    resp = api_client.post(
        URL_LISTA, {"peso_kg": peso, "tipo_cliente": "NUEVO", "tipo_envio": "ESTANDAR"}, format="json"
    )
    assert resp.status_code == codigo_http
    assert resp.data["codigo"] == codigo_error
    assert Cotizacion.objects.count() == 0


@pytest.mark.parametrize(
    "payload, campo_con_error",
    [
        ({"peso_kg": "abc", "tipo_cliente": "NUEVO", "tipo_envio": "ESTANDAR"}, "peso_kg"),
        ({"peso_kg": "5.005", "tipo_cliente": "NUEVO", "tipo_envio": "ESTANDAR"}, "peso_kg"),
        ({"peso_kg": "5.00", "tipo_cliente": "PREMIUM", "tipo_envio": "ESTANDAR"}, "tipo_cliente"),
        ({"peso_kg": "5.00", "tipo_cliente": "NUEVO", "tipo_envio": "AEREO"}, "tipo_envio"),
        ({"tipo_cliente": "NUEVO", "tipo_envio": "ESTANDAR"}, "peso_kg"),
        ({"peso_kg": "5.00", "tipo_envio": "ESTANDAR"}, "tipo_cliente"),
        ({"peso_kg": "5.00", "tipo_cliente": "NUEVO"}, "tipo_envio"),
    ],
)
def test_validaciones_de_formato(api_client, payload, campo_con_error):
    resp = api_client.post(URL_CALCULAR, payload, format="json")
    assert resp.status_code == 400
    assert resp.data["codigo"] == "DATOS_INVALIDOS"
    assert campo_con_error in resp.data["detalle"]


# ---------------------------------------------------------------------------
# GET /cotizaciones/ y /cotizaciones/{id}/
# ---------------------------------------------------------------------------
def test_listar_cotizaciones_paginado_y_ordenado(api_client, payload_valido):
    api_client.post(URL_LISTA, payload_valido, format="json")
    api_client.post(URL_LISTA, {**payload_valido, "tipo_cliente": "VIP"}, format="json")

    resp = api_client.get(URL_LISTA)

    assert resp.status_code == 200
    assert resp.data["count"] == 2
    assert resp.data["results"][0]["tipo_cliente"] == "VIP"  # la más reciente primero


def test_listar_con_filtros(api_client, payload_valido):
    api_client.post(URL_LISTA, payload_valido, format="json")
    api_client.post(URL_LISTA, {**payload_valido, "tipo_cliente": "VIP"}, format="json")

    resp = api_client.get(URL_LISTA, {"tipo_cliente": "VIP"})

    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["tipo_cliente"] == "VIP"


def test_listar_con_filtro_invalido_devuelve_400(api_client):
    resp = api_client.get(URL_LISTA, {"tipo_envio": "AEREO"})
    assert resp.status_code == 400
    assert resp.data["codigo"] == "DATOS_INVALIDOS"


def test_listar_respeta_page_size(api_client, payload_valido):
    for _ in range(3):
        api_client.post(URL_LISTA, payload_valido, format="json")
    resp = api_client.get(URL_LISTA, {"page_size": 2})
    assert len(resp.data["results"]) == 2
    assert resp.data["next"] is not None


def test_calcular_no_tiene_id_ni_fecha(api_client, payload_valido):
    resp = api_client.post(URL_CALCULAR, payload_valido, format="json")
    assert resp.data["id"] is None
    assert resp.data["creado_en"] is None


def test_detalle_de_cotizacion(api_client, payload_valido):
    creada = api_client.post(URL_LISTA, payload_valido, format="json").data
    resp = api_client.get(reverse("cotizacion-detail", args=[creada["id"]]))
    assert resp.status_code == 200
    assert resp.data["total"] == "51.75"


def test_detalle_inexistente_devuelve_404_con_formato_estandar(api_client):
    resp = api_client.get(reverse("cotizacion-detail", args=[9999]))
    assert resp.status_code == 404
    assert resp.data["codigo"] == "NOT_FOUND"


def test_no_se_permite_modificar_ni_borrar(api_client, payload_valido):
    creada = api_client.post(URL_LISTA, payload_valido, format="json").data
    url = reverse("cotizacion-detail", args=[creada["id"]])
    assert api_client.put(url, payload_valido, format="json").status_code == 405
    assert api_client.delete(url).status_code == 405


# ---------------------------------------------------------------------------
# GET /tarifas/
# ---------------------------------------------------------------------------
def test_tarifas_expone_reglas_vigentes(api_client):
    resp = api_client.get(URL_TARIFAS)
    assert resp.status_code == 200
    assert resp.data["costo_base"] == "5.00"
    assert resp.data["peso"]["maximo_kg"] == "20.00"
    assert resp.data["descuentos_cliente"]["VIP"] == "0.20"
    assert resp.data["recargos_envio"]["EXPRESS"] == "0.25"


# ---------------------------------------------------------------------------
# Documentación
# ---------------------------------------------------------------------------
def test_esquema_openapi_disponible(api_client):
    assert api_client.get(reverse("schema")).status_code == 200

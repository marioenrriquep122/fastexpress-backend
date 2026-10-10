"""Pruebas de los componentes transversales: errores, admin, health check y comandos."""

from io import StringIO

import pytest
from django.contrib.admin.sites import AdminSite
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse

from principal.admin.cotizacion_admin import CotizacionAdmin
from principal.core.exceptions.handler import manejador_excepciones
from principal.modelos import Cotizacion


# ---------------------------------------------------------------------------
# Manejador global de errores
# ---------------------------------------------------------------------------
def test_permission_denied_de_django_sale_con_formato_estandar():
    respuesta = manejador_excepciones(PermissionDenied(), {})
    assert respuesta.status_code == 403
    assert respuesta.data["codigo"] == "PERMISSION_DENIED"


def test_error_inesperado_no_se_oculta():
    """Un error de programación debe llegar como 500, no se 'traga'."""
    assert manejador_excepciones(ValueError("bug"), {}) is None


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
def test_admin_de_cotizaciones_es_solo_lectura():
    admin = CotizacionAdmin(Cotizacion, AdminSite())
    request = RequestFactory().get("/admin/")
    assert admin.has_add_permission(request) is False
    assert {"total", "peso_kg"} <= set(admin.get_readonly_fields(request))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_health_check(api_client):
    resp = api_client.get(reverse("health"))
    assert resp.status_code == 200
    assert resp.data == {"estado": "ok", "base_de_datos": "ok"}


# ---------------------------------------------------------------------------
# Comando de datos demo
# ---------------------------------------------------------------------------
@pytest.mark.django_db
def test_comando_cargar_datos_demo():
    salida = StringIO()
    call_command("cargar_datos_demo", stdout=salida)
    assert Cotizacion.objects.count() == 10

    call_command("cargar_datos_demo", "--limpiar", stdout=salida)
    assert Cotizacion.objects.count() == 10
    assert "Listo" in salida.getvalue()

"""
Manejador global de errores de la API (configurado en REST_FRAMEWORK).

Todas las respuestas de error tienen el mismo formato:

    {"codigo": "LIMITE_EXCEDIDO", "detalle": "Envío rechazado: ..."}
"""

import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .base import ErrorNegocio

logger = logging.getLogger(__name__)


def manejador_excepciones(exc, context):
    # 1. Errores de negocio de cualquier módulo
    if isinstance(exc, ErrorNegocio):
        logger.info("Regla de negocio rechazó la petición: %s - %s", exc.codigo, exc.mensaje)
        return Response({"codigo": exc.codigo, "detalle": exc.mensaje}, status=exc.status_http)

    # 2. Http404 / PermissionDenied de Django -> equivalentes de DRF
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    # 3. Errores de DRF (validación, 404, 405...)
    respuesta = exception_handler(exc, context)
    if respuesta is None:
        return None  # error inesperado: Django responde 500 y queda en el log

    if isinstance(exc, exceptions.ValidationError):
        respuesta.data = {"codigo": "DATOS_INVALIDOS", "detalle": respuesta.data}
        respuesta.status_code = status.HTTP_400_BAD_REQUEST
    else:
        datos = respuesta.data
        detalle = datos.get("detail", datos) if isinstance(datos, dict) else datos
        respuesta.data = {"codigo": exc.default_code.upper(), "detalle": detalle}
    return respuesta

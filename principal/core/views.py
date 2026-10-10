"""Vistas transversales del sistema."""

from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    GET /api/v1/health/

    Indica si la API y la base de datos están respondiendo. Lo usan los
    monitores de disponibilidad y el frontend para saber si el backend vive.
    """

    @extend_schema(summary="Estado de la API y la base de datos", responses={200: dict})
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return Response({"estado": "ok", "base_de_datos": "ok"})

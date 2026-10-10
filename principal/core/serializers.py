"""Serializers compartidos por todos los módulos."""

from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    """Formato estándar de error (se usa para documentar en Swagger)."""

    codigo = serializers.CharField()
    detalle = serializers.JSONField()

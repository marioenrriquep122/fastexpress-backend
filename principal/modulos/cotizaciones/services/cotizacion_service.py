"""
Servicio de cotizaciones: orquesta el cálculo y la persistencia.

Las vistas solo llaman a estas funciones. Aquí se decide si se guarda,
cómo se consulta y qué se filtra.
"""

from django.db import transaction
from django.db.models import QuerySet

from principal.modelos import Cotizacion

from .calculadora_service import calcular_cotizacion


def simular_cotizacion(peso, tipo_cliente: str, tipo_envio: str) -> Cotizacion:
    """Calcula y devuelve una Cotizacion SIN guardarla (vista previa)."""
    return Cotizacion(**calcular_cotizacion(peso, tipo_cliente, tipo_envio))


@transaction.atomic
def registrar_cotizacion(peso, tipo_cliente: str, tipo_envio: str) -> Cotizacion:
    """Calcula la cotización y la guarda en la base de datos."""
    return Cotizacion.objects.create(**calcular_cotizacion(peso, tipo_cliente, tipo_envio))


def listar_cotizaciones(tipo_cliente: str | None = None, tipo_envio: str | None = None) -> QuerySet:
    """Consulta de cotizaciones con filtros opcionales."""
    queryset = Cotizacion.objects.all()
    if tipo_cliente:
        queryset = queryset.filter(tipo_cliente=tipo_cliente)
    if tipo_envio:
        queryset = queryset.filter(tipo_envio=tipo_envio)
    return queryset

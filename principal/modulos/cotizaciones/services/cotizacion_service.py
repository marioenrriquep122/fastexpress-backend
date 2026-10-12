"""
Servicio de cotizaciones: orquesta el cálculo y la persistencia.

Las vistas solo llaman a estas funciones. Aquí se decide si se guarda,
cómo se consulta y qué se filtra.

Todas las operaciones de escritura calculan PRIMERO (calcular_cotizacion
lanza ErrorNegocio si algo viola una regla) y guardan DESPUÉS, así que una
petición rechazada nunca deja datos a medias en la base de datos.
"""

from decimal import Decimal

from django.db.models import QuerySet

from principal.modelos import Cotizacion

from .calculadora_service import calcular_cotizacion

# Tipo aceptado para el peso: el serializer entrega Decimal, pero los
# scripts y las pruebas pueden pasar int/str.
Peso = Decimal | int | str


def simular_cotizacion(peso: Peso, tipo_cliente: str, tipo_envio: str) -> Cotizacion:
    """Calcula y devuelve una Cotizacion SIN guardarla (vista previa)."""
    return Cotizacion(**calcular_cotizacion(peso, tipo_cliente, tipo_envio))


def registrar_cotizacion(peso: Peso, tipo_cliente: str, tipo_envio: str) -> Cotizacion:
    """Calcula la cotización y la guarda en la base de datos."""
    # Un solo INSERT ya es atómico: no hace falta @transaction.atomic.
    return Cotizacion.objects.create(**calcular_cotizacion(peso, tipo_cliente, tipo_envio))


def actualizar_cotizacion(cotizacion: Cotizacion, peso: Peso, tipo_cliente: str, tipo_envio: str) -> Cotizacion:
    """
    Recalcula una cotización existente con los nuevos datos de entrada.

    Todo el desglose (tarifa, descuento, recargo, total) se recalcula con las
    reglas vigentes, nunca se edita a mano.
    """
    for campo, valor in calcular_cotizacion(peso, tipo_cliente, tipo_envio).items():
        setattr(cotizacion, campo, valor)
    cotizacion.save()
    return cotizacion


def eliminar_cotizacion(cotizacion: Cotizacion) -> None:
    """Elimina una cotización."""
    cotizacion.delete()


def listar_cotizaciones(tipo_cliente: str | None = None, tipo_envio: str | None = None) -> QuerySet:
    """Consulta de cotizaciones con filtros opcionales."""
    queryset = Cotizacion.objects.all()
    if tipo_cliente:
        queryset = queryset.filter(tipo_cliente=tipo_cliente)
    if tipo_envio:
        queryset = queryset.filter(tipo_envio=tipo_envio)
    return queryset

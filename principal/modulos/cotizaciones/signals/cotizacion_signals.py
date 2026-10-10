"""
Signals del módulo de cotizaciones.

Se registran en PrincipalConfig.ready(). Dejan trazabilidad en el log cada
vez que se emite una cotización, sin ensuciar el servicio con esa lógica.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from principal.modelos import Cotizacion

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Cotizacion, dispatch_uid="cotizacion_registrada")
def registrar_en_log(sender, instance: Cotizacion, created: bool, **kwargs):
    if created:
        logger.info(
            "Cotización emitida #%s: %s kg %s/%s total=%s",
            instance.pk,
            instance.peso_kg,
            instance.tipo_cliente,
            instance.tipo_envio,
            instance.total,
        )

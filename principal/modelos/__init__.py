# Django busca los modelos en `principal.models` o en este paquete:
# cada modelo nuevo se registra aquí para que makemigrations lo detecte.
from .cotizacion import Cotizacion

__all__ = ["Cotizacion"]

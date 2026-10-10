from django.db import models


class ModeloBase(models.Model):
    """
    Modelo abstracto del que heredan todos los modelos del sistema.

    Centraliza los campos de auditoría para que todas las tablas los
    tengan igual, sin repetirlos en cada modelo.
    """

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

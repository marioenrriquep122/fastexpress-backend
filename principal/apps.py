from django.apps import AppConfig


class PrincipalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "principal"
    verbose_name = "FastExpress"

    def ready(self):
        # Registro de signals de cada módulo. Se importan aquí (y no arriba)
        # porque los modelos deben estar cargados antes.
        from principal.modulos.cotizaciones.signals import cotizacion_signals  # noqa: F401

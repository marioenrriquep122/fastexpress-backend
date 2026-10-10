from django.contrib import admin

from principal.modelos import Cotizacion


@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = (
        "id", "peso_kg", "tipo_cliente", "tipo_envio",
        "subtotal", "descuento", "recargo", "total", "creado_en",
    )
    list_filter = ("tipo_cliente", "tipo_envio")
    date_hierarchy = "creado_en"

    # Una cotización es un registro histórico: se consulta, no se edita
    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

"""
Comando para llenar la base de datos local con cotizaciones de ejemplo.

Uso:
    python manage.py cargar_datos_demo           # agrega los ejemplos
    python manage.py cargar_datos_demo --limpiar # borra todo y vuelve a cargar

Los datos pasan por el mismo servicio que usa la API, así que quedan
calculados con las reglas reales (sirve también para la demo en clase).
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from principal.modelos import Cotizacion
from principal.modulos.cotizaciones.services.cotizacion_service import registrar_cotizacion

EJEMPLOS = [
    # peso, cliente, envío  (cubren los dos tramos y las 6 combinaciones)
    ("0.01", "NUEVO", "ESTANDAR"),
    ("2.00", "NUEVO", "EXPRESS"),
    ("4.99", "FRECUENTE", "ESTANDAR"),
    ("5.00", "FRECUENTE", "EXPRESS"),
    ("5.01", "VIP", "ESTANDAR"),
    ("10.00", "VIP", "EXPRESS"),
    ("12.50", "NUEVO", "ESTANDAR"),
    ("15.00", "FRECUENTE", "EXPRESS"),
    ("19.99", "VIP", "ESTANDAR"),
    ("20.00", "NUEVO", "EXPRESS"),
]


class Command(BaseCommand):
    help = "Carga cotizaciones de ejemplo en la base de datos local."

    def add_arguments(self, parser):
        parser.add_argument("--limpiar", action="store_true", help="Borra las cotizaciones existentes antes de cargar.")

    def handle(self, *args, **options):
        if options["limpiar"]:
            borradas, _ = Cotizacion.objects.all().delete()
            self.stdout.write(f"Se borraron {borradas} cotizaciones.")

        for peso, cliente, envio in EJEMPLOS:
            c = registrar_cotizacion(Decimal(peso), cliente, envio)
            self.stdout.write(f"  {c}")

        self.stdout.write(self.style.SUCCESS(f"Listo: {len(EJEMPLOS)} cotizaciones cargadas."))

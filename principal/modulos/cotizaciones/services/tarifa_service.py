"""Servicio de consulta de las tarifas vigentes (para que el frontend no las quemen)."""

from principal.constantes import cotizacion as c


def obtener_tarifas_vigentes() -> dict:
    return {
        "costo_base": str(c.COSTO_BASE),
        "peso": {
            "minimo_kg": str(c.PESO_MINIMO_KG),
            "maximo_kg": str(c.PESO_MAXIMO_KG),
            "tramos": [
                {
                    "desde_kg": str(c.PESO_MINIMO_KG),
                    "hasta_kg": str(c.LIMITE_TRAMO_LIGERO_KG),
                    "tarifa_por_kg": str(c.TARIFA_KG_LIGERO),
                },
                {
                    "desde_kg": str(c.LIMITE_TRAMO_LIGERO_KG + c.CENTAVO),
                    "hasta_kg": str(c.PESO_MAXIMO_KG),
                    "tarifa_por_kg": str(c.TARIFA_KG_PESADO),
                },
            ],
        },
        "descuentos_cliente": {
            c.TipoCliente.NUEVO.value: str(c.DESCUENTO_NUEVO),
            c.TipoCliente.FRECUENTE.value: str(c.DESCUENTO_FRECUENTE),
            c.TipoCliente.VIP.value: str(c.DESCUENTO_VIP),
        },
        "recargos_envio": {
            c.TipoEnvio.ESTANDAR.value: str(c.RECARGO_ESTANDAR),
            c.TipoEnvio.EXPRESS.value: str(c.RECARGO_EXPRESS),
        },
    }

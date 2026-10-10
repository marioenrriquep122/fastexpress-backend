"""
Algoritmo principal de cálculo de tarifa (BR-01 a BR-04).

Es la función "core" sobre la que QA hace la prueba de CAJA BLANCA.
Es pura: no toca base de datos ni HTTP, por eso se prueba en milisegundos.

Los comentarios [N1], [N2]... son los nodos del Grafo de Flujo de Control
documentado en docs/CAJA_BLANCA.md. Si se cambia la estructura de los
if/elif, hay que actualizar ese documento.

Fórmula (interpretación acordada por el equipo, ver README):
    subtotal  = COSTO_BASE + peso * tarifa_kg
    descuento = subtotal * % cliente
    recargo   = subtotal * % envío   ("sobre la tarifa subtotal")
    total     = subtotal - descuento + recargo
"""

from decimal import ROUND_HALF_UP, Decimal

from principal.constantes.cotizacion import (
    CENTAVO,
    COSTO_BASE,
    DESCUENTO_FRECUENTE,
    DESCUENTO_NUEVO,
    DESCUENTO_VIP,
    LIMITE_TRAMO_LIGERO_KG,
    PESO_MAXIMO_KG,
    RECARGO_ESTANDAR,
    RECARGO_EXPRESS,
    TARIFA_KG_LIGERO,
    TARIFA_KG_PESADO,
    TipoCliente,
    TipoEnvio,
)
from principal.modulos.cotizaciones.exceptions import (
    LimiteExcedidoError,
    PesoInvalidoError,
    TipoClienteInvalidoError,
    TipoEnvioInvalidoError,
)


def redondear(valor: Decimal) -> Decimal:
    """Redondea dinero a 2 decimales, mitad hacia arriba (0.005 -> 0.01)."""
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_cotizacion(peso, tipo_cliente: str, tipo_envio: str) -> dict:
    """
    Aplica BR-01 a BR-04 y devuelve el desglose de la cotización.

    Raises:
        PesoInvalidoError: peso <= 0
        LimiteExcedidoError: peso > 20.00 kg
        TipoClienteInvalidoError / TipoEnvioInvalidoError: tipo desconocido
    """
    peso = Decimal(str(peso))

    # ---- BR-02: validación y tramo de peso --------------------------------
    if peso <= 0:                                                     # [N1] D1
        raise PesoInvalidoError("El peso debe ser mayor a 0 kg.")    # [N2]

    if peso > PESO_MAXIMO_KG:                                         # [N3] D2
        raise LimiteExcedidoError(                                    # [N4]
            f"Envío rechazado: el peso máximo permitido es {PESO_MAXIMO_KG} kg."
        )

    if peso <= LIMITE_TRAMO_LIGERO_KG:                                # [N5] D3
        tarifa_kg = TARIFA_KG_LIGERO                                  # [N6]
    else:
        tarifa_kg = TARIFA_KG_PESADO                                  # [N7]

    # ---- BR-03: descuento por tipo de cliente -----------------------------
    if tipo_cliente == TipoCliente.NUEVO:                             # [N8] D4
        porcentaje_descuento = DESCUENTO_NUEVO                        # [N9]
    elif tipo_cliente == TipoCliente.FRECUENTE:                       # [N10] D5
        porcentaje_descuento = DESCUENTO_FRECUENTE                    # [N11]
    elif tipo_cliente == TipoCliente.VIP:                             # [N12] D6
        porcentaje_descuento = DESCUENTO_VIP                          # [N13]
    else:
        raise TipoClienteInvalidoError(                               # [N14]
            f"Tipo de cliente inválido: '{tipo_cliente}'."
        )

    # ---- BR-04: recargo por tipo de envío ---------------------------------
    if tipo_envio == TipoEnvio.ESTANDAR:                              # [N15] D7
        porcentaje_recargo = RECARGO_ESTANDAR                         # [N16]
    elif tipo_envio == TipoEnvio.EXPRESS:                             # [N17] D8
        porcentaje_recargo = RECARGO_EXPRESS                          # [N18]
    else:
        raise TipoEnvioInvalidoError(                                 # [N19]
            f"Tipo de envío inválido: '{tipo_envio}'."
        )

    # ---- BR-01 + cálculo final --------------------------------------------
    costo_peso = redondear(peso * tarifa_kg)                          # [N20]
    subtotal = COSTO_BASE + costo_peso
    descuento = redondear(subtotal * porcentaje_descuento)
    recargo = redondear(subtotal * porcentaje_recargo)
    total = subtotal - descuento + recargo

    return {
        "peso_kg": peso,
        "tipo_cliente": str(tipo_cliente),
        "tipo_envio": str(tipo_envio),
        "costo_base": COSTO_BASE,
        "tarifa_por_kg": tarifa_kg,
        "costo_peso": costo_peso,
        "subtotal": subtotal,
        "porcentaje_descuento": porcentaje_descuento,
        "descuento": descuento,
        "porcentaje_recargo": porcentaje_recargo,
        "recargo": recargo,
        "total": total,
    }                                                                 # [N21] fin

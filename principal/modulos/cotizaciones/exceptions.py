"""Errores de negocio propios del módulo de cotizaciones."""

from principal.core.exceptions.base import ErrorNegocio


class PesoInvalidoError(ErrorNegocio):
    """El peso es 0 o negativo."""

    codigo = "PESO_INVALIDO"
    status_http = 400


class LimiteExcedidoError(ErrorNegocio):
    """BR-02: peso mayor a 20.00 kg, el envío se rechaza."""

    codigo = "LIMITE_EXCEDIDO"
    status_http = 422


class TipoClienteInvalidoError(ErrorNegocio):
    codigo = "TIPO_CLIENTE_INVALIDO"
    status_http = 400


class TipoEnvioInvalidoError(ErrorNegocio):
    codigo = "TIPO_ENVIO_INVALIDO"
    status_http = 400

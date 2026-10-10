"""
Excepción base de negocio, compartida por todos los módulos.

Cada módulo define sus errores heredando de ErrorNegocio con un `codigo`
estable y un `status_http`. El manejador global (handler.py) los convierte
en respuestas JSON sin que las vistas tengan que hacer try/except.
"""


class ErrorNegocio(Exception):
    codigo = "ERROR_NEGOCIO"
    status_http = 400

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje

"""Entorno de PRUEBAS automatizadas (pytest y GitHub Actions)."""

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "clave-solo-para-pruebas"

# Base de datos en memoria: cada corrida arranca limpia y no toca db.sqlite3
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

# Hasher rápido: crear usuarios en las pruebas no tarda
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Menos ruido en la salida de las pruebas
LOGGING["loggers"]["principal"]["level"] = "WARNING"  # noqa: F405

"""Entorno de DESARROLLO local."""

from .base import *  # noqa: F403
from .base import REST_FRAMEWORK, env_bool

DEBUG = env_bool("DEBUG", True)
SECRET_KEY = SECRET_KEY or "dev-insegura-solo-para-desarrollo-local"  # noqa: F405

# API navegable de DRF con formularios HTML, solo en desarrollo
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]
REST_FRAMEWORK["DEFAULT_PARSER_CLASSES"] = [
    "rest_framework.parsers.JSONParser",
    "rest_framework.parsers.FormParser",
    "rest_framework.parsers.MultiPartParser",
]
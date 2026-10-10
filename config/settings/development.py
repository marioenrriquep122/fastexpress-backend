"""Entorno de DESARROLLO local."""

from .base import *  # noqa: F403
from .base import REST_FRAMEWORK, env_bool

DEBUG = env_bool("DEBUG", True)
SECRET_KEY = SECRET_KEY or "dev-insegura-solo-para-desarrollo-local"  # noqa: F405

# API navegable de DRF (formularios HTML) solo en desarrollo
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

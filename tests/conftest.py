import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def payload_valido():
    return {"peso_kg": "10.00", "tipo_cliente": "FRECUENTE", "tipo_envio": "EXPRESS"}

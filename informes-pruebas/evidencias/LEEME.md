# Evidencias de ejecución

| Archivo | Descripción |
|---|---|
| `pytest_diagnostico_inicial_1_fallida.txt` | Primera corrida tras instalar dependencias (73 passed, 1 failed) |
| `pytest_suite_completa_post_regresion.txt` | Suite final 79 passed, cobertura 100 % |
| `pytest_caja_blanca.txt` | Subconjunto `-m caja_blanca` |
| `pytest_caja_negra_api.txt` | Subconjunto `-m "caja_negra or api"` |
| `pytest_collect.txt` | Árbol de colección pytest |
| `coverage.xml` | Cobertura XML (copia de la corrida final) |
| `ruff_check.txt` | Salida de `ruff check .` (All checks passed) |

Informe HTML de cobertura: **`htmlcov/index.html`** en la raíz del repositorio (generado por pytest-cov, no duplicado aquí).

No se incluyen secretos: `.env` no forma parte de estas evidencias.

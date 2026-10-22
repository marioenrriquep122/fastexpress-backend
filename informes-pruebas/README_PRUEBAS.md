# Guía de ejecución de pruebas (informe RICO)

Esta carpeta documenta cómo reproducir la evaluación de calidad realizada sobre **fastexpress-backend**.

El acrónimo **RICO** en el prompt de evaluación significa: **R**ol, **I**nstrucciones, **C**ontexto y **O**utput, para delimitar metodología y entregables.

---

## 1. Requisitos

| Requisito | Detalle |
|---|---|
| Python | 3.11+ recomendado (probado también con 3.10.11) |
| SO | Windows, Linux o macOS |
| Base de datos en pruebas | SQLite en memoria (`:memory:`), configurada en `config/settings/testing.py` |
| Red | No se requieren servicios externos para la suite automatizada |

---

## 2. Instalación del entorno de pruebas

Desde la raíz del repositorio (donde está `manage.py`):

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements\dev.txt
copy .env.example .env
```

En Linux/macOS sustituir la activación del venv y `copy` por `cp`.

> Las pruebas **no** usan `db.sqlite3` de desarrollo; usan `DJANGO_SETTINGS_MODULE=config.settings.testing`.

---

## 3. Comandos exactos utilizados en la evaluación

```powershell
.\.venv\Scripts\ruff check .
.\.venv\Scripts\pytest
.\.venv\Scripts\pytest -m caja_blanca --no-cov
.\.venv\Scripts\pytest -m "caja_negra or api" --no-cov
.\.venv\Scripts\python informes-pruebas\generar_csv_casos.py
```

---

## 4. Ejecutar solo caja blanca

Incluye los 9 caminos del CFG sobre `calcular_cotizacion` y las pruebas de integración interna (servicio, core, admin, signals):

```powershell
.\.venv\Scripts\pytest -m caja_blanca --no-cov -v
.\.venv\Scripts\pytest tests\integration\cotizaciones\test_cotizacion_service.py tests\integration\core\test_core.py --no-cov -v
```

Marcador definido en `pyproject.toml`: `caja_blanca`.

---

## 5. Ejecutar solo caja negra

Especificación sobre la calculadora (PE, BVA, tabla de decisión) y contrato HTTP de la API:

```powershell
.\.venv\Scripts\pytest -m "caja_negra or api" --no-cov -v
```

---

## 6. Ejecutar toda la suite

```powershell
.\.venv\Scripts\pytest
```

Salida esperada tras la corrección de regresión documentada: **79 passed**, cobertura ≥ 85 %.

---

## 7. Cobertura de código

La configuración en `pyproject.toml` activa ramas y umbral mínimo del 85 %:

```powershell
.\.venv\Scripts\pytest --cov=principal --cov-branch --cov-report=term-missing --cov-report=html --cov-report=xml
```

| Artefacto | Ubicación |
|---|---|
| Informe HTML | `htmlcov/index.html` |
| XML | `coverage.xml` (raíz) y copia en `informes-pruebas/evidencias/coverage.xml` |
| Consola | Incluida en `informes-pruebas/evidencias/pytest_suite_completa_post_regresion.txt` |

Resultado medido en la evaluación: **100 %** líneas sobre el paquete `principal` (308 sentencias, 40 ramas).

---

## 8. Reproducir resultados del informe

1. Crear venv e instalar `requirements/dev.txt`.
2. Ejecutar `pytest` y comparar con `evidencias/pytest_suite_completa_post_regresion.txt`.
3. Abrir `casos_de_prueba.csv` (regenerable con `generar_csv_casos.py`).

---

## 9. Limitaciones conocidas

- No se ejecutaron pruebas manuales contra un servidor `runserver` en puerto 8001; la caja negra HTTP usa `APIClient` de DRF (comportamiento equivalente al WSGI de Django en memoria).
- No hay autenticación ni pruebas de carga/concurrencia.
- Python 3.11 no estaba instalado en el equipo de evaluación; se usó 3.10.11.
- El archivo `.env` es opcional para pytest; es necesario para desarrollo local con `config.settings.development`.

---

## 10. Estructura de entregables

| Archivo | Propósito |
|---|---|
| `informe_ejecutivo.md` | Resumen para stakeholders |
| `informe_caja_blanca.md` | Análisis interno y cobertura |
| `informe_caja_negra.md` | Contrato REST y pruebas por comportamiento |
| `casos_de_prueba.csv` | Matriz unificada de casos |
| `registro_defectos.md` | Defectos verificados |
| `evidencias/` | Salidas de consola y cobertura |

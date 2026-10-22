# Informe ejecutivo de pruebas de software

## 1. Identificación del proyecto

| Campo | Valor |
|---|---|
| Nombre | fastexpress-backend |
| Versión declarada | 1.0.0 (`pyproject.toml`) |
| Dominio funcional | Cotización de envíos y descuentos (FastExpress) |
| Stack | Python, Django 5.2 LTS, Django REST Framework, SQLite/PostgreSQL |
| Punto de entrada | `manage.py` → `config.wsgi` / `config.asgi` |
| API base | `/api/v1/` |
| Documentación interactiva | `/api/docs/` (Swagger) |

---

## 2. Objetivo y alcance

**Objetivo:** Evaluar la calidad del backend mediante pruebas de **caja blanca** (estructura interna, caminos lógicos, cobertura) y **caja negra** (comportamiento observable de la calculadora y de la API REST), con evidencias reproducibles.

**Alcance incluido:**

- Módulo de cotizaciones (`principal/modulos/cotizaciones/`).
- Componentes transversales (`principal/core/`, admin, comando demo, health check).
- Suite automatizada existente en `tests/` y ampliación mínima de pruebas API (PUT/PATCH/DELETE).

**Fuera de alcance:**

- Frontend, despliegue a producción, pruebas de penetración, carga masiva y bases de datos PostgreSQL reales.

---

## 3. Metodología (prompt RICO)

El trabajo siguió el prompt estructurado en **R**ol (auditor QA), **I**nstrucciones (fases 1–7), **C**ontexto (doble perspectiva caja blanca/negra) y **O**utput (entregables en `informes-pruebas/`).

Fases ejecutadas: reconocimiento, planificación basada en código real, ejecución de pruebas automatizadas, medición de cobertura, corrección de desalineación en la suite, regeneración de evidencias e informes.

---

## 4. Entorno de ejecución

| Elemento | Configuración |
|---|---|
| Fecha | 2026-10-16 |
| Python | 3.10.11 (entorno virtual `.venv`) |
| Settings de prueba | `config.settings.testing` |
| Base de datos | SQLite `:memory:` |
| Herramientas | pytest 9.1.1, pytest-django, pytest-cov, ruff 0.17.1 |

Acciones de inicialización realizadas: creación de `.venv`, `pip install -r requirements/dev.txt`, copia de `.env.example` → `.env` (desarrollo local; no requerido por pytest).

---

## 5. Resumen cuantitativo de pruebas

| Métrica | Valor |
|---|---|
| Casos automatizados diseñados (suite final) | 79 |
| Ejecutados | 79 |
| Aprobados (suite final) | 79 |
| Fallidos (diagnóstico inicial, antes de corrección) | 1 |
| Bloqueados | 0 |
| No ejecutados | 0 |

Desglose por metodología (clasificación del CSV):

| Metodología | Casos |
|---|---|
| Caja blanca | 25 |
| Caja negra | 54 |

---

## 6. Resultados por perspectiva

### 6.1 Caja blanca

- **Función crítica:** `calcular_cotizacion` — 9 caminos independientes (V(G) = 9) cubiertos al 100 %.
- **Integración interna:** servicio de cotizaciones, restricciones del modelo, signals, manejador de excepciones, admin de solo lectura, comando `cargar_datos_demo`.
- **Cobertura del paquete `principal`:** 100 % líneas y ramas en la corrida final (ver evidencias).

### 6.2 Caja negra

- **Calculadora:** particiones de equivalencia, BVA de peso y monto, tabla de decisión 3×2 (cliente × envío), redondeo monetario.
- **API REST:** CRUD documentado, validaciones, códigos HTTP, paginación, filtros, `/tarifas/`, `/health/`, esquema OpenAPI.
- **Contrato deducido del código** donde no se usó Swagger manual; rutas verificadas en `principal/modulos/cotizaciones/urls.py` y `config/urls.py`.

---

## 7. Cobertura de código

| Métrica | Resultado |
|---|---|
| Sentencias (`principal`) | 308 / 308 (100 %) |
| Ramas | 40 / 40 (100 %) |
| Umbral configurado | 85 % (`pyproject.toml`) |
| Informe HTML | `htmlcov/index.html` |

---

## 8. Defectos y riesgos

| Tipo | Detalle |
|---|---|
| Defectos de producto | Ninguno confirmado |
| Artefacto corregido | Prueba obsoleta que esperaba 405 en PUT (ver `registro_defectos.md`, ART-001) |
| Riesgo pendiente | Divergencia menor entre README (Python 3.11+) y entorno local 3.10.11 |
| Riesgo pendiente | API pública sin autenticación (diseño declarado, no defecto) |

---

## 9. Conclusiones

El backend implementa de forma coherente las reglas de negocio BR-01 a BR-04, expone un CRUD REST versionado y mantiene una suite automatizada sólida. Tras alinear las pruebas de PUT/PATCH/DELETE con la documentación, la suite completa pasa con cobertura total del código de aplicación bajo `principal/`.

La cobertura elevada **no implica ausencia de defectos** en escenarios no modelados (concurrencia, producción PostgreSQL, integración manual con navegador).

---

## 10. Recomendaciones

1. Instalar Python 3.11+ en equipos de desarrollo para coincidir con `requires-python`.
2. Mantener sincronizados README, Swagger y pruebas cuando cambie el contrato API.
3. Conservar el umbral del 85 % en CI (`.github/workflows/pruebas.yml`).
4. Opcional: añadir pruebas e2e con servidor real (`runserver`) si el frontend lo requiere.

---

## 11. Referencias de evidencia

- `informes-pruebas/evidencias/pytest_diagnostico_inicial_1_fallida.txt`
- `informes-pruebas/evidencias/pytest_suite_completa_post_regresion.txt`
- `informes-pruebas/evidencias/coverage.xml`
- `informes-pruebas/casos_de_prueba.csv`

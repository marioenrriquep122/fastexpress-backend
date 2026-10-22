# Registro de defectos confirmados

**Proyecto:** fastexpress-backend  
**Fecha de evaluación:** 2026-10-16  
**Criterio:** Solo se registran defectos verificados mediante ejecución reproducible.

---

## Resumen

| Estado | Cantidad |
|---|---|
| Defectos de producto confirmados | 2 (severidad baja, abiertos) |
| Defectos de artefacto de prueba (suite desalineada) | 1 (corregido) |

La API se comporta según lo documentado. En la función core `calcular_cotizacion` se encontraron 2 defectos de severidad baja (DEF-001 y DEF-002) que el serializer de la API enmascara.

---

## ART-001 — Prueba de integración desalineada con el contrato API

| Campo | Valor |
|---|---|
| **Identificador** | ART-001 |
| **Título** | `test_no_se_permite_modificar_ni_borrar` esperaba HTTP 405 en PUT/DELETE |
| **Descripción** | La prueba asumía que PUT y DELETE sobre `/api/v1/cotizaciones/{id}/` devolvían 405. El código y el README (sección 5) documentan CRUD completo con PUT/PATCH (200) y DELETE (204). La ejecución inicial devolvió **200** en PUT, provocando el fallo. |
| **Severidad** | Media (bloqueaba la suite y generaba falsa alarma de regresión) |
| **Prioridad** | Alta (corrección de la suite) |
| **Pasos para reproducir (estado inicial)** | 1. Instalar dependencias. 2. Ejecutar `pytest`. 3. Observar fallo en `test_no_se_permite_modificar_ni_borrar`. |
| **Resultado esperado (según contrato documentado)** | PUT recalcula y responde 200; DELETE responde 204. |
| **Resultado real (prueba obsoleta)** | PUT respondía 200 pero la prueba esperaba 405. |
| **Archivo o componente afectado** | `tests/integration/cotizaciones/test_cotizacion_api.py` |
| **Evidencia** | `informes-pruebas/evidencias/pytest_diagnostico_inicial_1_fallida.txt` (copia de la primera corrida) |
| **Estado de la corrección** | **Corregido** — sustituida por casos API-CN-PUT/PATCH/DELETE alineados al README. |
| **Prueba de regresión asociada** | `test_put_reemplaza_datos_y_recalcula`, `test_patch_cambia_solo_campos_enviados_y_recalcula`, `test_delete_existente_devuelve_204_y_luego_404`, `test_delete_lista_sin_id_devuelve_405` |

---

## DEF-001 — La función core no aplica el peso mínimo de 0.01 kg

| Campo | Valor |
|---|---|
| **Identificador** | DEF-001 |
| **Título** | `calcular_cotizacion` acepta pesos entre 0 y 0.01 kg |
| **Descripción** | BR-02 define el rango válido desde 0.01 kg. La función solo valida `peso <= 0`, así que `0.001` kg se acepta y devuelve total 5.00. La constante `PESO_MINIMO_KG` está definida pero no se usa. |
| **Severidad** | Baja (por la API no ocurre: el serializer limita a 2 decimales) |
| **Prioridad** | Media |
| **Pasos para reproducir** | `calcular_cotizacion("0.001", "NUEVO", "ESTANDAR")` |
| **Resultado esperado** | `PesoInvalidoError` |
| **Resultado real** | Retorna total 5.00 |
| **Archivo o componente afectado** | `principal/modulos/cotizaciones/services/calculadora_service.py` (nodo N1) |
| **Corrección sugerida** | `if peso.is_nan() or peso < PESO_MINIMO_KG:` |
| **Estado** | **Abierto** — asignado a backend |
| **Prueba asociada** | `tests/qa/test_qa_exploratorias.py::test_QA_30_core_rechaza_peso_menor_al_minimo` (xfail estricto) |

---

## DEF-002 — Peso "NaN" produce una excepción técnica en la función core

| Campo | Valor |
|---|---|
| **Identificador** | DEF-002 |
| **Título** | `calcular_cotizacion("NaN", …)` lanza `decimal.InvalidOperation` |
| **Descripción** | Al comparar `Decimal("NaN") <= 0` Python lanza `InvalidOperation` en vez del error de negocio `PesoInvalidoError`. |
| **Severidad** | Baja (por la API se rechaza con 400 DATOS_INVALIDOS) |
| **Prioridad** | Baja |
| **Pasos para reproducir** | `calcular_cotizacion("NaN", "NUEVO", "ESTANDAR")` |
| **Resultado esperado** | `PesoInvalidoError` |
| **Resultado real** | `decimal.InvalidOperation` |
| **Archivo o componente afectado** | `principal/modulos/cotizaciones/services/calculadora_service.py` (nodo N1) |
| **Corrección sugerida** | La misma de DEF-001 |
| **Estado** | **Abierto** — asignado a backend |
| **Prueba asociada** | `tests/qa/test_qa_exploratorias.py::test_QA_31_core_rechaza_nan_con_error_de_negocio` (xfail estricto) |

---

## Observaciones (no clasificadas como defecto confirmado)

- **Entorno Python:** el repositorio declara Python ≥ 3.11; la evaluación se ejecutó con **3.10.11** por disponibilidad local. No se observaron incompatibilidades en esta corrida.
- **Autenticación:** la API es pública (sin login). No aplica prueba de autorización por roles.

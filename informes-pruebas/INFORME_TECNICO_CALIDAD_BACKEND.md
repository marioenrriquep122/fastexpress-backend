# Informe técnico de calidad de software — Backend FastExpress

**Proyecto integrador:** Sistema de Calidad y Pruebas de Software  
**Asignatura:** Calidad de Software  
**Componente evaluado:** Backend (`fastexpress-backend`) — Módulo de Cotización de Envíos y Descuentos  
**Rol responsable:** Analista de Calidad / QA Engineer (pruebas de caja negra, caja blanca, automatización y cobertura)  
**Fecha de consolidación:** 2026-10-22  
**Repositorio:** `fastexpress-backend` (Django 5.2 + DRF, API `/api/v1/`)

> **Uso de este documento:** Entregar este archivo (o su contenido) a Claude u otra herramienta para redactar la versión final en Word, fusionar con el informe del frontend o generar tablas/capturas. Toda la evidencia numérica proviene de ejecuciones reales (`pytest`, 2026-10-22).

---

## 0. Alineación con el enunciado del Proyecto Integrador

El documento oficial exige, en la parte de QA:

| Entregable | Ubicación en este informe |
|---|---|
| Plan de pruebas de **caja negra** (PE, BVA, tabla de decisión) | Sección 1 |
| Plan de pruebas de **caja blanca** (CFG, V(G), caminos) | Sección 2 |
| **Reporte de cobertura** (mín. 85 % líneas y ramas) | Sección 3 |
| Automatización (PyTest, API) | Sección 4 |
| Reglas de negocio BR-01 a BR-04 | Sección 0.1 y tablas de expected results |

**Alcance backend:** Reglas de negocio, función `calcular_cotizacion`, servicios, API REST y persistencia. Las pruebas manuales de **UI (frontend)** no forman parte de este informe; la API se probó como interfaz observable para el cliente (caja negra HTTP).

### 0.1 Reglas de negocio (referencia)

| ID | Regla | Implementación principal |
|---|---|---|
| BR-01 | Costo base USD 5.00 | `COSTO_BASE`, desglose en respuesta JSON |
| BR-02 | 0.01–5.00 kg → 2.00/kg; 5.01–20.00 → 4.00/kg; >20 rechazo | `calculadora_service.py`, errores `PESO_INVALIDO` / `LIMITE_EXCEDIDO` |
| BR-03 | NUEVO 0 %, FRECUENTE 10 %, VIP 20 % | Descuento sobre subtotal |
| BR-04 | ESTANDAR 0 %, EXPRESS +25 % sobre subtotal | Recargo sobre subtotal |

**Fórmula acordada (README del repo):**

```
subtotal  = 5.00 + peso × tarifa_kg
descuento = subtotal × % cliente
recargo   = subtotal × % envío
total     = subtotal − descuento + recargo   (Decimal, 2 decimales, half-up)
```

---

## 1. Plan de pruebas de caja negra (Backend + contrato API)

**Diseño:** A partir de la especificación (BR-01 a BR-04), documentado en `docs/CAJA_NEGRA.md`.  
**Ejecución automatizada:** `tests/unit/cotizaciones/test_calculadora_caja_negra.py`, `tests/integration/cotizaciones/test_cotizacion_api.py`, `tests/qa/test_qa_exploratorias.py` (`pytest -m "caja_negra or api"` → **87 passed** en corrida del 2026-10-22).

### 1.1 Particiones de equivalencia — Campo **Peso** (`peso_kg`)

| ID | Clase | Rango / condición | Válida | Valor ejemplo | Resultado esperado (NUEVO, ESTANDAR) | Verificación |
|---|---|---|---|---|---|---|
| PE-01 | No positivo | ≤ 0 | No | 0.00, −3.00 | Error (`PesoInvalidoError` / HTTP 400 `PESO_INVALIDO`) | Automatizado |
| PE-02 | Tramo ligero | 0.01 – 5.00 | Sí | 3.00 | total 11.00 | Automatizado |
| PE-03 | Tramo pesado | 5.01 – 20.00 | Sí | 12.00 | total 53.00 | Automatizado |
| PE-04 | Exceso | > 20.00 | No | 35.00, 20.01 | `LimiteExcedidoError` / HTTP 422 `LIMITE_EXCEDIDO` | Automatizado |
| PE-05 | No numérico | texto | No | "abc" | HTTP 400 `DATOS_INVALIDOS` | Automatizado |
| PE-06 | Precisión | > 2 decimales | No | 5.005 | HTTP 400 `DATOS_INVALIDOS` | Automatizado |
| PE-07 | Ausente | — | No | (sin campo) | HTTP 400 `DATOS_INVALIDOS` | Automatizado |

**Casos QA adicionales (HTTP):** NaN, booleano, cadena vacía, enteros de 7 dígitos (QA-06 a QA-09) — **PASSED**.

### 1.2 Análisis de valores límite (BVA) — **Peso**

| ID | Punto límite | Peso (kg) | Tarifa/kg | Total (NUEVO, ESTANDAR) | Estado prueba |
|---|---|---|---|---|---|
| BVA-01 | mínimo − 1 | 0.00 | — | Rechazo | PASSED |
| BVA-02 | mínimo | 0.01 | 2.00 | 5.02 | PASSED |
| BVA-03 | mínimo + δ | 0.02 | 2.00 | 5.04 | PASSED |
| BVA-04 | límite ligero − δ | 4.99 | 2.00 | 14.98 | PASSED |
| BVA-05 | límite ligero | 5.00 | 2.00 | 15.00 | PASSED |
| BVA-06 | límite pesado | 5.01 | 4.00 | 25.04 | PASSED |
| BVA-07 | límite pesado + δ | 5.02 | 4.00 | 25.08 | PASSED |
| BVA-08 | máximo − δ | 19.99 | 4.00 | 84.96 | PASSED |
| BVA-09 | máximo | 20.00 | 4.00 | 85.00 | PASSED |
| BVA-10 | máximo + 1 | 20.01 | — | `LIMITE_EXCEDIDO` | PASSED |

**Observación de negocio (informe):** Entre 5.00 kg (15.00 USD) y 5.01 kg (25.04 USD) el total aumenta abruptamente porque la tarifa 4.00 se aplica a **todo** el peso (interpretación BR-02 acordada en README).

**Caso límite adicional QA:** Tabla de decisión con peso **5.01 kg** (QA-18 … QA-23) — **PASSED**.

### 1.3 Particiones y BVA — **Monto** (total resultante, no campo de entrada)

El enunciado pide BVA sobre “Monto”; en FastExpress el monto es **calculado** (`total`). Se validan extremos y propiedades:

| ID | Caso | Entrada | Total esperado | Estado |
|---|---|---|---|---|
| BVA-M1 | Mínimo posible | 0.01 kg, VIP, ESTANDAR | 4.02 | PASSED |
| BVA-M2 | Máximo posible | 20.00 kg, NUEVO, EXPRESS | 106.25 | PASSED |
| PE-M1 | Positividad | Combinaciones válidas | total > 0 | PASSED |
| PE-M2 | Redondeo | 0.03 kg, FRECUENTE, ESTANDAR | desc. 0.51; total 4.55 | PASSED |

### 1.4 Tabla de decisión — **Tipo de cliente × Tipo de envío**

Peso fijo **10.00 kg** → subtotal **45.00**.

| ID | Cliente | Envío | Descuento | Recargo | Total | Estado |
|---|---|---|---|---|---|---|
| TD-01 | NUEVO | ESTANDAR | 0.00 | 0.00 | 45.00 | PASSED |
| TD-02 | NUEVO | EXPRESS | 0.00 | 11.25 | 56.25 | PASSED |
| TD-03 | FRECUENTE | ESTANDAR | 4.50 | 0.00 | 40.50 | PASSED |
| TD-04 | FRECUENTE | EXPRESS | 4.50 | 11.25 | 51.75 | PASSED |
| TD-05 | VIP | ESTANDAR | 9.00 | 0.00 | 36.00 | PASSED |
| TD-06 | VIP | EXPRESS | 9.00 | 11.25 | 47.25 | PASSED |
| TD-07 | PREMIUM | ESTANDAR | — | — | `DATOS_INVALIDOS` | PASSED |
| TD-08 | NUEVO | AEREO | — | — | `DATOS_INVALIDOS` | PASSED |

### 1.5 Caja negra a nivel API REST (comportamiento observable)

**Base:** `http://127.0.0.1:8001/api/v1/` (Swagger: `/api/docs/`).

| Acción | Método | Ruta | Códigos probados |
|---|---|---|---|
| Simular sin guardar | POST | `/cotizaciones/calcular/` | 200, 400 |
| Crear | POST | `/cotizaciones/` | 201, 400, 422 |
| Listar / filtrar | GET | `/cotizaciones/` | 200, 400 |
| Detalle | GET | `/cotizaciones/{id}/` | 200, 404 |
| Actualizar | PUT / PATCH | `/cotizaciones/{id}/` | 200, 400, 422 |
| Eliminar | DELETE | `/cotizaciones/{id}/` | 204, 404, 405 (colección) |
| Tarifas | GET | `/tarifas/` | 200 |
| Salud | GET | `/health/` | 200 |

Formato de error estándar: `{"codigo", "detalle"}`. **Seguridad funcional:** campos `total`/`descuento` enviados por el cliente se ignoran (QA-24) — **PASSED**.

---

## 2. Plan de pruebas de caja blanca (Backend — algoritmo core)

**Función bajo prueba:** `calcular_cotizacion(peso, tipo_cliente, tipo_envio)`  
**Archivo:** `principal/modulos/cotizaciones/services/calculadora_service.py`  
**Documentación CFG:** `docs/CAJA_BLANCA.md` (diagrama Mermaid exportable a imagen vía mermaid.live)  
**Pruebas:** `tests/unit/cotizaciones/test_calculadora_caja_blanca.py` + QA core (`test_QA_30`, `test_QA_31`) — **`pytest -m caja_blanca` → 11 passed**.

### 2.1 Grafo de flujo de control (CFG)

Nodos de decisión principales **D1–D8** (N1, N3, N5, N8, N10, N12, N15, N17) y procesos N2, N4, N6–N7, N9, N11, N13–N14, N16, N18–N21. Ver diagrama completo en `docs/CAJA_BLANCA.md`.

**Nota de mantenimiento:** Se añadieron validaciones de parseo numérico, peso mínimo 0.01 kg y rechazo de NaN **antes** del tramo BR-02 documentado en el CFG original. Los **9 caminos independientes** del diseño académico (C1–C9) siguen siendo válidos; las pruebas QA-30/31 cubren las reglas de robustez adicionales.

### 2.2 Complejidad ciclomática V(G)

| Método | Cálculo | Resultado |
|---|---|---|
| Aristas − nodos + 2 | E = 28, N = 21 | **V(G) = 9** |
| Predicados + 1 | P = 8 | **V(G) = 9** |
| Regiones | — | **9** |

**Interpretación:** Se requieren **9 caminos independientes** como mínimo para cubrir sentencias y ramas del núcleo de decisiones; riesgo **bajo** (V(G) ≤ 10).

### 2.3 Caminos independientes y trazabilidad a pruebas

| Camino | Decisiones destacadas | Entrada | Resultado | Test |
|---|---|---|---|---|
| C1 | D1 verdadero | 0, NUEVO, ESTANDAR | `PesoInvalidoError` | test_C1 |
| C2 | D2 verdadero | 20.01, NUEVO, ESTANDAR | `LimiteExcedidoError` | test_C2 |
| C3 | Camino base ligero | 2.00, NUEVO, ESTANDAR | total 9.00 | test_C3 |
| C4 | D3 falso (pesado) | 10.00, NUEVO, ESTANDAR | total 45.00 | test_C4 |
| C5 | D5 verdadero | 2.00, FRECUENTE, ESTANDAR | total 8.10 | test_C5 |
| C6 | D6 verdadero | 2.00, VIP, ESTANDAR | total 7.20 | test_C6 |
| C7 | Cliente inválido | 2.00, PREMIUM, ESTANDAR | `TipoClienteInvalidoError` | test_C7 |
| C8 | D8 verdadero (EXPRESS) | 2.00, NUEVO, EXPRESS | total 11.25 | test_C8 |
| C9 | Envío inválido | 2.00, NUEVO, AEREO | `TipoEnvioInvalidoError` | test_C9 |

**Pruebas white-box complementarias (suite completa):** servicio de cotizaciones, restricciones CHECK en BD, signals, manejador global de excepciones, admin solo lectura, comando `cargar_datos_demo`.

---

## 3. Reporte de cobertura (Code Coverage)

**Herramienta:** pytest-cov / coverage.py  
**Comando:** `pytest --cov=principal --cov-branch`  
**Umbral configurado:** **85 %** (`pyproject.toml`, CI GitHub Actions)  
**Resultado 2026-10-22:**

| Métrica | Valor |
|---|---|
| Casos ejecutados | 114 |
| Aprobados | 114 |
| Fallidos | 0 |
| Cobertura total (`principal`) | **99,46 %** |
| Sentencias | 324 (2 sin cubrir) |
| Ramas | 48 / 48 cubiertas en reporte |

**Archivos de evidencia:**

- Consola: corrida terminal (114 passed, “Required test coverage of 85.0% reached”)
- HTML: `htmlcov/index.html`
- XML: `coverage.xml`
- Resumen: `informes-pruebas/INFORME_EJECUCION_2026-10-22.md`

**Líneas no cubiertas:** `calculadora_service.py` 60-61 (rama `InvalidOperation` al parsear peso; en la práctica la API filtra antes con `DATOS_INVALIDOS`).

**Análisis:** La cobertura supera ampliamente el mínimo del enunciado. Cobertura alta no implica ausencia de defectos en escenarios no modelados (concurrencia, producción PostgreSQL, pruebas manuales de UI).

---

## 4. Automatización y resumen de ejecución

| Suite | Comando | Resultado (2026-10-22) |
|---|---|---|
| Caja blanca | `pytest -m caja_blanca -v` | 11 passed |
| Caja negra + API | `pytest -m "caja_negra or api" -v` | 87 passed |
| Completa + cobertura | `pytest --cov=principal --cov-branch` | 114 passed, 99,46 % |

**Stack de pruebas:** PyTest 9.1.1, pytest-django, pytest-cov; entorno `config.settings.testing`; BD SQLite `:memory:`.

**Matriz extendida:** `informes-pruebas/casos_de_prueba.csv` (regenerable con `informes-pruebas/generar_csv_casos.py`).

---

## 5. Defectos detectados y estado

| ID | Descripción | Severidad | Estado |
|---|---|---|---|
| DEF-001 | Core no aplicaba mínimo 0.01 kg | Media | **Corregido** (QA-30) |
| DEF-002 | NaN no devolvía `PesoInvalidoError` | Media | **Corregido** (QA-31) |
| ART-001 | Prueba API obsoleta (405 en PUT) | Baja (artefacto) | **Corregido** (alineado a CRUD) |

Detalle: `informes-pruebas/registro_defectos.md`.

---

## 6. Conclusiones y recomendaciones (QA Backend)

1. El backend cumple BR-01 a BR-04 según la batería automatizada de caja negra (especificación + HTTP) y caja blanca (CFG, V(G)=9, caminos C1–C9).
2. La cobertura **99,46 %** cumple el requisito del Proyecto Integrador (**≥ 85 %** líneas y ramas).
3. Para el informe Word final: exportar CFG desde `docs/CAJA_BLANCA.md`, adjuntar captura de `htmlcov/index.html` y tabla resumen de esta sección 3.
4. El frontend debe reutilizar el contrato API documentado en README sección 5 y validar UI contra los mismos códigos HTTP; eso corresponde al entregable “Caja Negra (QA + Frontend)” en el documento del curso.

---

## 7. Instrucciones para Claude (u otro asistente)

Al procesar este informe, se solicita:

1. Mantener **tablas y cifras** tal cual (114 tests, 99,46 %, V(G)=9, BR-01 a BR-04).
2. Redactar en **tercera persona** y tono académico si se pasa a Word.
3. **No inventar** endpoints, porcentajes ni resultados de prueba no listados aquí.
4. Separar claramente: **Backend (este documento)** vs **Frontend (UI manual)**.
5. Opcional: fusionar con matrices de `docs/CAJA_NEGRA.md` y diagrama de `docs/CAJA_BLANCA.md`.
6. Incluir portada del Proyecto Integrador (roles, integrantes — completar nombres del equipo).

**Archivos relacionados en el repo:**

- `docs/CAJA_NEGRA.md`, `docs/CAJA_BLANCA.md`
- `informes-pruebas/informe_caja_negra.md`, `informe_caja_blanca.md`, `informe_ejecutivo.md`
- `README.md` (sección 7 Guía para QA)

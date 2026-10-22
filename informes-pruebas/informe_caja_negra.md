# Informe de pruebas de caja negra

## 1. Alcance funcional

Se evaluó el comportamiento observable del sistema **sin usar la implementación como criterio de diseño de casos**, basándose en:

- Reglas de negocio BR-01 a BR-04 (README, sección 1).
- Contrato REST documentado (README, sección 5).
- Matrices de diseño en `docs/CAJA_NEGRA.md`.

La verificación se automatizó mediante pytest y `APIClient` (simula peticiones HTTP sin servidor TCP externo).

---

## 2. Endpoints e interfaces identificados

Base: **`/api/v1/`** (desde `config/urls.py`).

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health/` | Estado API y BD |
| GET | `/cotizaciones/` | Listado paginado y filtros |
| POST | `/cotizaciones/` | Calcular y guardar (201) |
| GET | `/cotizaciones/{id}/` | Detalle |
| PUT | `/cotizaciones/{id}/` | Reemplazar entrada y recalcular |
| PATCH | `/cotizaciones/{id}/` | Actualización parcial |
| DELETE | `/cotizaciones/{id}/` | Eliminar (204) |
| POST | `/cotizaciones/calcular/` | Simular sin persistir |
| GET | `/tarifas/` | Reglas vigentes |
| GET | `/api/schema/`, `/api/docs/` | OpenAPI / Swagger |

**Autenticación:** no implementada (API pública).

**Limitación documental:** los casos HTTP se dedujeron del código y del README; no se realizó sesión manual en Swagger durante esta evaluación.

---

## 3. Contratos y criterios de aceptación (resumen)

| Regla | Criterio observable |
|---|---|
| BR-01 | Costo base 5.00 USD en desglose |
| BR-02 | Tarifa por tramo; rechazo si peso > 20.00 kg (`LIMITE_EXCEDIDO`, 422) |
| BR-03 | Descuentos 0 % / 10 % / 20 % según cliente |
| BR-04 | Recargo 25 % solo EXPRESS, sobre subtotal |
| Entrada API | Solo `peso_kg`, `tipo_cliente`, `tipo_envio`; montos calculados server-side |
| Errores | JSON `{"codigo", "detalle"}` |

---

## 4. Técnicas de diseño aplicadas

| Técnica | Aplicación |
|---|---|
| Particiones de equivalencia (PE) | Peso válido/inválido (`test_calculadora_caja_negra.py`) |
| Análisis de valores límite (BVA) | 0, 0.01, 5.00, 5.01, 20.00, 20.01; montos min/max |
| Tabla de decisión | 3 tipos cliente × 2 tipos envío @ 10 kg |
| Clases de equivalencia HTTP | Payloads válidos, tipos erróneos, campos faltantes |
| Pruebas negativas | 400, 404, 422, 405 según contrato |

---

## 5. Tabla resumida de casos API (caja negra HTTP)

| ID lógico | Objetivo | HTTP esperado | Estado |
|---|---|---|---|
| API-CN-CALC-01 | POST `/calcular/` no persiste | 200 | Aprobado |
| API-CN-POST-01 | POST `/cotizaciones/` persiste | 201 | Aprobado |
| API-CN-POST-02 | Peso 0 / negativo | 400 `PESO_INVALIDO` | Aprobado |
| API-CN-POST-03 | Peso > 20 | 422 `LIMITE_EXCEDIDO` | Aprobado |
| API-CN-VAL-01..07 | Datos inválidos en calcular | 400 `DATOS_INVALIDOS` | Aprobado |
| API-CN-GET-01 | Listado ordenado y paginado | 200 | Aprobado |
| API-CN-GET-02 | Filtros query | 200 | Aprobado |
| API-CN-GET-03 | Filtro inválido | 400 | Aprobado |
| API-CN-GET-04 | Detalle / 404 | 200 / 404 | Aprobado |
| API-CN-PUT-01 | PUT recalcula | 200 | Aprobado |
| API-CN-PATCH-01 | PATCH parcial | 200 | Aprobado |
| API-CN-PUT-02 | PUT incompleto | 400 | Aprobado |
| API-CN-DEL-01..03 | DELETE id / 404 / 405 colección | 204/404/405 | Aprobado |
| API-CN-TAR-01 | GET `/tarifas/` | 200 | Aprobado |
| API-CN-DOC-01 | Esquema OpenAPI | 200 | Aprobado |

Detalle de parametrizaciones en `tests/integration/cotizaciones/test_cotizacion_api.py`. Casos de especificación pura sobre la calculadora: 26 pruebas en `test_calculadora_caja_negra.py`.

---

## 6. Resultados obtenidos

```
pytest -m "caja_negra or api" --no-cov  → 54 passed
```

**Diagnóstico inicial (antes de corrección de suite):**

- Falló 1 caso: `test_no_se_permite_modificar_ni_borrar` (esperaba 405, PUT devolvió 200).
- Causa: desalineación prueba vs contrato CRUD, no fallo funcional del endpoint.

**Tras regresión:** 79/79 aprobados.

Evidencias: `evidencias/pytest_caja_negra_api.txt`, `evidencias/pytest_diagnostico_inicial_1_fallida.txt`.

---

## 7. Códigos HTTP observados

| Código | Contexto verificado |
|---|---|
| 200 | GET, POST calcular, PUT, PATCH |
| 201 | POST crear cotización |
| 204 | DELETE exitoso |
| 400 | Validación, peso inválido, filtros |
| 404 | Recurso inexistente |
| 405 | DELETE sobre colección sin id |
| 422 | Peso > 20 kg en creación |

---

## 8. Validación de entradas inválidas

Comportamiento verificado:

- `peso_kg` no numérico, más de 2 decimales, ≤ 0.
- `tipo_cliente` / `tipo_envio` fuera de enumeración.
- Campos obligatorios ausentes en POST/calcular.
- Filtro `tipo_envio=AEREO` en listado → 400.

---

## 9. Defectos, limitaciones y conclusiones

| Item | Conclusión |
|---|---|
| Defectos de producto en API | No confirmados |
| Prueba obsoleta | Corregida (ART-001) |
| Limitación | Sin pruebas concurrentes ni servidor real en puerto 8001 |
| Limitación | Sin auth/autorización |

**Conclusión:** El comportamiento observable de la API coincide con el contrato documentado en README y con las reglas de negocio, para el conjunto de casos automatizados. Se recomienda ejecutar la matriz manual del README contra Swagger como complemento opcional de aceptación final.

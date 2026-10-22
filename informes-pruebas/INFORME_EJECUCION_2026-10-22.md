# Informe de ejecución de pruebas — 2026-10-22

## 1. Identificación

| Campo | Valor |
|---|---|
| Proyecto | fastexpress-backend |
| Comando | `pytest --cov=principal --cov-branch` |
| Entorno | Windows, Python 3.10.11, `.venv` activo |
| Django | 5.2.18 (`config.settings.testing`) |
| Base de datos de prueba | SQLite `:memory:` |
| Evidencia | Terminal / `informes-pruebas/evidencias/` (corrida completa) |

---

## 2. Resultado global

| Métrica | Valor |
|---|---|
| Casos recogidos | 114 |
| Ejecutados | 114 |
| **Aprobados** | **114** |
| Fallidos | 0 |
| Bloqueados | 0 |
| XFAIL / XPASS | 0 |
| Duración | 3,02 s |
| Umbral de cobertura | 85 % (configurado) |
| **Cobertura total** | **99,46 %** |

**Conclusión:** La suite automatizada completa aprueba y supera el umbral de cobertura exigido por el proyecto.

---

## 3. Ejecuciones parciales (misma sesión)

| Comando | Resultado |
|---|---|
| `pytest -m caja_blanca -v` | 11 passed, 103 deselected |
| `pytest -m "caja_negra or api" -v` | 87 passed, 27 deselected |
| `pytest --cov=principal --cov-branch` | 114 passed, cobertura 99,46 % |

---

## 4. Cobertura por paquete `principal`

| Métrica | Valor |
|---|---|
| Sentencias | 324 total, 2 sin cubrir |
| Ramas | 48 total, 0 parciales sin cubrir |
| Archivos al 100 % | Mayoría (vistas, servicios, modelos, handler, admin, etc.) |

**Líneas no cubiertas:**

| Archivo | Líneas | Observación |
|---|---|---|
| `calculadora_service.py` | 60-61 | Rama `InvalidOperation` al convertir peso no numérico (cubierta en API como `DATOS_INVALIDOS`; pocos casos llaman al core con strings no decimales) |

---

## 5. Caja blanca (11 casos con marcador + integración interna en suite completa)

- **CFG:** `test_C1` … `test_C9` sobre `calcular_cotizacion` — PASSED.
- **QA core:** `test_QA_30` (mínimo 0,01 kg), `test_QA_31` (NaN) — PASSED (defectos DEF-001 y DEF-002 cerrados).
- **Integración:** servicio, restricciones BD, signals, admin, health, comando demo — PASSED en suite completa.

---

## 6. Caja negra (87 casos con `-m "caja_negra or api"` + resto en suite)

- **API REST:** CRUD, calcular, filtros (`id`, `peso_kg`, `creado_en`), paginación, errores 400/404/422/405 — PASSED.
- **QA HTTP:** QA-01 … QA-29 (peso, tipos, PATCH/PUT/DELETE, JSON inválido) — PASSED.
- **Especificación calculadora:** PE, BVA, tabla de decisión (10 kg y 5,01 kg), redondeo — PASSED.

---

## 7. Defectos

| ID | Estado | Notas |
|---|---|---|
| DEF-001 | Cerrado | Peso &lt; 0,01 kg rechazado en core |
| DEF-002 | Cerrado | NaN rechazado con `PesoInvalidoError` |
| ART-001 | Cerrado | Prueba API obsoleta (405 en PUT) alineada al CRUD |

No se registraron defectos nuevos en esta ejecución.

---

## 8. Comandos para reproducir

```powershell
cd C:\Users\danna\Videos\pruebas-cajabw\fastexpress-backend
.\.venv\Scripts\activate
pytest --cov=principal --cov-branch
```

Informe HTML de cobertura: `htmlcov/index.html`

---

## 9. Recomendaciones

1. Mantener `pytest --cov=principal --cov-branch` antes de entregas y en CI.
2. Opcional: añadir un caso unitario que invoque el core con peso no parseable para cubrir líneas 60-61 al 100 %.
3. Documentar en el informe académico la diferencia entre pruebas por marcador y suite completa (114 casos).

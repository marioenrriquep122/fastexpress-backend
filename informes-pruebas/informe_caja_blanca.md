# Informe de pruebas de caja blanca

## 1. Alcance del análisis interno

Se analizó el código bajo el paquete `principal/` con foco en:

- Algoritmo puro de cotización (`calculadora_service.py`).
- Orquestación de persistencia (`cotizacion_service.py`).
- Capa HTTP (`cotizacion_views.py`, serializers).
- Modelo y restricciones (`modelos/cotizacion.py`).
- Infraestructura transversal (excepciones, paginación, health, admin, signals, comando demo).

---

## 2. Componentes, archivos y funciones examinados

| Componente | Archivo principal | Funciones / clases relevantes |
|---|---|---|
| Calculadora | `services/calculadora_service.py` | `redondear`, `calcular_cotizacion` |
| Servicio | `services/cotizacion_service.py` | `simular_cotizacion`, `registrar_cotizacion`, `actualizar_cotizacion`, `eliminar_cotizacion`, `listar_cotizaciones` |
| Vistas | `views/cotizacion_views.py` | `CotizacionViewSet` |
| Excepciones | `exceptions.py`, `core/exceptions/handler.py` | Jerarquía `ErrorNegocio`, `manejador_excepciones` |
| Persistencia | `modelos/cotizacion.py` | Modelo `Cotizacion`, constraints |
| Signals | `signals/cotizacion_signals.py` | Log en creación |

---

## 3. Herramientas utilizadas y justificación

| Herramienta | Uso |
|---|---|
| **pytest** | Framework ya adoptado por el repositorio |
| **pytest-django** | Integración con ORM y `APIClient` |
| **pytest-cov / coverage.py** | Medición de líneas y ramas sobre `principal` |
| **ruff** | Análisis estático (estilo y errores básicos) |

No se añadieron herramientas nuevas; se respetaron `pyproject.toml` y `requirements/dev.txt`.

---

## 4. Estrategia de pruebas

1. **Caminos independientes del CFG** sobre `calcular_cotizacion` (documentado en `docs/CAJA_BLANCA.md`).
2. **Pruebas de servicio** invocando funciones directamente (mocks innecesarios: la calculadora es pura).
3. **Pruebas de defensa en profundidad** insertando datos inválidos en el ORM (`IntegrityError`).
4. **Pruebas de componentes transversales** (admin, handler 403/500, comando management).

---

## 5. Complejidad ciclomática

Para `calcular_cotizacion`:

- Decisiones principales: D1–D8 (peso, tramos, cliente, envío).
- **V(G) = 9** caminos independientes (según documentación del proyecto y estructura `if/elif` actual).
- Cada camino tiene un caso automatizado `test_C1` … `test_C9`.

Funciones con mayor complejidad relativa en el módulo: `calcular_cotizacion` (núcleo) y `CotizacionViewSet.update` (composición PATCH/PUT). Ambas quedaron cubiertas tras la ampliación de pruebas API.

---

## 6. Tabla resumida de casos (núcleo CFG)

| ID | Caso | Camino lógico | Estado |
|---|---|---|---|
| CB-C1 | Peso ≤ 0 | N1→N2 | Aprobado |
| CB-C2 | Peso > 20 | N1→N3→N4 | Aprobado |
| CB-C3 | Tramo ligero, NUEVO, ESTANDAR | Camino base | Aprobado |
| CB-C4 | Tramo pesado | D3 falso → N7 | Aprobado |
| CB-C5 | Cliente FRECUENTE | D5 verdadero | Aprobado |
| CB-C6 | Cliente VIP | D6 verdadero | Aprobado |
| CB-C7 | Cliente inválido | → N14 | Aprobado |
| CB-C8 | EXPRESS | D8 verdadero | Aprobado |
| CB-C9 | Envío inválido | → N19 | Aprobado |

La tabla completa de 79 filas está en `casos_de_prueba.csv` (metodología `caja_blanca`).

---

## 7. Resultados reales de ejecución

```
pytest -m caja_blanca --no-cov  → 9 passed
pytest tests/integration/cotizaciones/test_cotizacion_service.py
     tests/integration/core/test_core.py  → 16 passed
```

Suite completa con cobertura:

```
79 passed in ~1.75s
TOTAL principal: 308 statements, 0 miss, 40 branches, 0 partial → 100%
```

Evidencia: `evidencias/pytest_suite_completa_post_regresion.txt`, `evidencias/coverage.xml`.

---

## 8. Cobertura detallada

| Métrica | Valor |
|---|---|
| Líneas / sentencias | 100 % |
| Ramas | 100 % |
| Funciones críticas sin cubrir | Ninguna en `principal/` |

**Código no cubierto:** Ninguno en el paquete `principal` tras la suite final. Las migraciones están excluidas por configuración (`omit = */migrations/*`).

---

## 9. Defectos encontrados (caja blanca)

No se confirmaron defectos en la lógica interna. El único fallo inicial correspondió a una expectativa incorrecta en una prueba de API (ver `registro_defectos.md`, ART-001), no a un error en `calcular_cotizacion` o en el servicio.

---

## 10. Limitaciones

- Las pruebas de servicio conocen la firma de las funciones (perspectiva blanca); la validación de montos finales también se contrasta con casos de caja negra.
- No se instrumentó análisis de complejidad automatizado (radon); V(G) se tomó del diseño documentado.
- `config/` queda fuera del `source` de coverage; solo se midió `principal`.

---

## 11. Conclusiones

La estructura interna del módulo de cotizaciones es testeable y está cubierta exhaustivamente. Los caminos de error (peso inválido, límite excedido, tipos inválidos) se ejercitan tanto en unitarias como en capa de servicio y API.

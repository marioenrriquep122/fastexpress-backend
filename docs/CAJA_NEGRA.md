# Plan de Pruebas de Caja Negra

Diseñado **solo desde la especificación** (BR-01 a BR-04), sin mirar el código.
**Pruebas automatizadas:** `tests/unit/cotizaciones/test_calculadora_caja_negra.py` (`pytest -m caja_negra`) y `tests/integration/cotizaciones/test_cotizacion_api.py` (nivel HTTP).

Fórmula de referencia usada para los valores esperados:

```
subtotal  = 5.00 + peso × tarifa_kg        (tarifa 2.00 si peso <= 5.00, si no 4.00)
descuento = subtotal × %cliente            (NUEVO 0%, FRECUENTE 10%, VIP 20%)
recargo   = subtotal × %envío              (ESTANDAR 0%, EXPRESS 25%)
total     = subtotal − descuento + recargo (redondeo a 2 decimales, mitad hacia arriba)
```

---

## 1. Particiones de Equivalencia — Peso

| ID | Clase | Rango | Tipo | Valor representativo | Resultado esperado (NUEVO, ESTANDAR) |
|---|---|---|---|---|---|
| PE-01 | Peso no positivo | peso ≤ 0 | Inválida | −3.00 | Error `PESO_INVALIDO` (HTTP 400) |
| PE-02 | Tramo ligero | 0.01 – 5.00 | Válida | 3.00 | total 11.00 |
| PE-03 | Tramo pesado | 5.01 – 20.00 | Válida | 12.00 | total 53.00 |
| PE-04 | Exceso de peso | > 20.00 | Inválida | 35.00 | Error `LIMITE_EXCEDIDO` (HTTP 422) |
| PE-05 | No numérico | texto | Inválida | "abc" | Error `DATOS_INVALIDOS` (HTTP 400) |
| PE-06 | Más de 2 decimales | p. ej. 5.005 | Inválida | 5.005 | Error `DATOS_INVALIDOS` (HTTP 400) |
| PE-07 | Campo ausente | — | Inválida | (sin peso) | Error `DATOS_INVALIDOS` (HTTP 400) |

## 2. Análisis de Valores Límite (BVA) — Peso

| ID | Límite | Peso | Tarifa/kg | Total esperado (NUEVO, ESTANDAR) |
|---|---|---|---|---|
| BVA-01 | mínimo − 1 | 0.00 | — | `PESO_INVALIDO` |
| BVA-02 | mínimo | 0.01 | 2.00 | 5.02 |
| BVA-03 | mínimo + 1 | 0.02 | 2.00 | 5.04 |
| BVA-04 | límite ligero − 1 | 4.99 | 2.00 | 14.98 |
| BVA-05 | límite ligero | 5.00 | 2.00 | 15.00 |
| BVA-06 | límite pesado | 5.01 | 4.00 | 25.04 |
| BVA-07 | límite pesado + 1 | 5.02 | 4.00 | 25.08 |
| BVA-08 | máximo − 1 | 19.99 | 4.00 | 84.96 |
| BVA-09 | máximo | 20.00 | 4.00 | 85.00 |
| BVA-10 | máximo + 1 | 20.01 | — | `LIMITE_EXCEDIDO` |

> **Hallazgo para el informe:** entre 5.00 kg (15.00 USD) y 5.01 kg (25.04 USD) el precio salta 10.04 USD por 10 gramos, porque la tarifa de 4.00 se aplica sobre **todo** el peso, no solo sobre el excedente. Es lo que dice BR-02, pero vale la pena reportarlo como observación de negocio.

## 3. Monto (total a pagar)

La especificación no define reglas propias para un campo "Monto" de entrada; el equipo lo interpreta como el **monto total resultante** y prueba sus extremos y particiones:

| ID | Caso | Entrada | Total esperado |
|---|---|---|---|
| BVA-M1 | Monto mínimo posible | 0.01 kg, VIP, ESTANDAR | 4.02 |
| BVA-M2 | Monto máximo posible | 20.00 kg, NUEVO, EXPRESS | 106.25 |
| PE-M1 | Monto siempre positivo | toda combinación válida | total > 0 |
| PE-M2 | Redondeo de 3 decimales | 0.03 kg, FRECUENTE, ESTANDAR | descuento 0.506 → 0.51; total 4.55 |

> Si el docente define "Monto" como otro campo (p. ej. valor declarado), se agrega como entrada del serializer y estas tablas se ajustan.

## 4. Tabla de Decisión — Tipo de Cliente × Tipo de Envío

Peso fijo 10.00 kg → subtotal = 5.00 + 10 × 4.00 = **45.00**

| Condiciones / Acciones | TD-01 | TD-02 | TD-03 | TD-04 | TD-05 | TD-06 |
|---|---|---|---|---|---|---|
| Cliente = NUEVO | V | V | F | F | F | F |
| Cliente = FRECUENTE | F | F | V | V | F | F |
| Cliente = VIP | F | F | F | F | V | V |
| Envío = EXPRESS | F | V | F | V | F | V |
| **Descuento** | 0.00 | 0.00 | 4.50 | 4.50 | 9.00 | 9.00 |
| **Recargo** | 0.00 | 11.25 | 0.00 | 11.25 | 0.00 | 11.25 |
| **Total** | **45.00** | **56.25** | **40.50** | **51.75** | **36.00** | **47.25** |

Reglas adicionales (entradas inválidas):

| ID | Cliente | Envío | Resultado |
|---|---|---|---|
| TD-07 | PREMIUM | ESTANDAR | `DATOS_INVALIDOS` (campo tipo_cliente) |
| TD-08 | NUEVO | AEREO | `DATOS_INVALIDOS` (campo tipo_envio) |

## 5. Cómo ejecutar

```bash
pytest -m caja_negra --no-cov
pytest -m api --no-cov
```

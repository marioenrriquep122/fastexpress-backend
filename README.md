# FastExpress — Backend (Django REST Framework)

Módulo de **Cotización de Envíos y Descuentos** del Proyecto Integrador de *Calidad de Software*.
Backend organizado por capas: cada capa tiene su carpeta y cada módulo de negocio vive aislado en `principal/modulos/`.

| | |
|---|---|
| Lenguaje | Python 3.11+ |
| Framework | Django 5.2 LTS + Django REST Framework |
| Base de datos | SQLite local (`db.sqlite3`), PostgreSQL opcional |
| Pruebas | PyTest + pytest-django + pytest-cov (unitarias e integración) |
| Calidad de código | Ruff (linter) + EditorConfig |
| Integración continua | GitHub Actions (lint, migraciones, pruebas, cobertura) |
| Documentación API | Swagger en `/api/docs/` |
| Cobertura exigida | **85 % de líneas y ramas** (si baja, `pytest` falla) |

**Equipo y roles**

| Rol | Responsable | Dónde trabaja |
|---|---|---|
| Backend | Mario | `principal/`, `config/` |
| Frontend | su carpeta del frontend (consume la API) |
| QA | `tests/`, `docs/` |

---

## Índice

1. [Qué hace el sistema y reglas de negocio](#1-qué-hace-el-sistema-y-reglas-de-negocio)
2. [Ruta de trabajo: qué hace cada quien y en qué orden](#2-ruta-de-trabajo-qué-hace-cada-quien-y-en-qué-orden)
3. [Instalación y ejecución del backend](#3-instalación-y-ejecución-del-backend)
4. [Estructura del proyecto](#4-estructura-del-proyecto)
5. [API REST (CRUD completo)](#5-api-rest-crud-completo)
6. [Guía para Frontend (Milagro)](#6-guía-para-frontend-milagro)
7. [Guía para QA](#7-guía-para-qa)
8. [Base de datos local](#8-base-de-datos-local)
9. [Pruebas, cobertura y calidad de código](#9-pruebas-cobertura-y-calidad-de-código)
10. [Buenas prácticas aplicadas](#10-buenas-prácticas-aplicadas)
11. [Flujo con Git](#11-flujo-con-git)
12. [Checklist de entrega](#12-checklist-de-entrega)
13. [Problemas comunes](#13-problemas-comunes)

---

## 1. Qué hace el sistema y reglas de negocio

El usuario indica **peso**, **tipo de cliente** y **tipo de envío**; el sistema calcula cuánto cuesta el envío y guarda el desglose.

| Regla | Descripción |
|---|---|
| BR-01 | Costo base 5.00 USD por orden |
| BR-02 | 0.01–5.00 kg: 2.00 por kg · 5.01–20.00 kg: 4.00 por kg · más de 20.00 kg: **rechazo** |
| BR-03 | NUEVO 0 % · FRECUENTE 10 % · VIP 20 % de descuento |
| BR-04 | ESTANDAR 0 % · EXPRESS +25 % de recargo sobre el subtotal |

**Fórmula (interpretación acordada, va en el informe):**

```
subtotal  = 5.00 + peso × tarifa_kg
descuento = subtotal × % cliente
recargo   = subtotal × 25 %          (solo EXPRESS)
total     = subtotal − descuento + recargo
```

Decisiones de interpretación del enunciado:

1. **Tramo de peso:** la tarifa del tramo se aplica a **todo** el peso (7 kg = 7 × 4.00), no por tramos marginales.
2. **Orden:** descuento y recargo se calculan **sobre el mismo subtotal**, así el orden no cambia el resultado. Si el recargo se aplicara después del descuento, FRECUENTE + EXPRESS con 10 kg daría 50.63 en vez de 51.75.
3. **Peso con máximo 2 decimales.** Por la API, un peso como `5.005` se rechaza (`DATOS_INVALIDOS`), así que no existe peso "entre 5.00 y 5.01". Si el servicio se llama directo desde código con `5.005`, se trata como tramo pesado.
4. **Dinero con `Decimal`** (nunca `float`), redondeado a 2 decimales con la mitad hacia arriba.
5. **Monto** (campo que el enunciado pide para BVA) = **total cotizado**. Rango real: de **4.02** (0.01 kg, VIP, ESTANDAR) a **106.25** (20 kg, NUEVO, EXPRESS).

**Ejemplo con 10 kg** (subtotal = 5.00 + 10 × 4.00 = 45.00):

| Cliente | Envío | Descuento | Recargo | Total |
|---|---|---|---|---|
| NUEVO | ESTANDAR | 0.00 | 0.00 | 45.00 |
| NUEVO | EXPRESS | 0.00 | 11.25 | 56.25 |
| FRECUENTE | ESTANDAR | 4.50 | 0.00 | 40.50 |
| FRECUENTE | EXPRESS | 4.50 | 11.25 | 51.75 |
| VIP | ESTANDAR | 9.00 | 0.00 | 36.00 |
| VIP | EXPRESS | 9.00 | 11.25 | 47.25 |

---

## 2. Ruta de trabajo: qué hace cada quien y en qué orden

Sigue el orden de la hoja de ruta del enunciado. Cada paso depende del anterior.

### Semana 1 — Análisis y diseño

| Quién | Qué hace |
|---|---|
| Todos | Leer el enunciado y esta sección 1 (reglas e interpretaciones). Si algo se interpreta distinto, se corrige **aquí** y en el informe. |
| QA | Escribir la primera versión de la matriz de caja negra en `docs/CAJA_NEGRA.md` (antes de que exista el código final). |
| Backend | Dejar el servidor corriendo y Swagger disponible para que los demás vean los endpoints. |

### Semana 2 — Desarrollo e integración

| Quién | Qué hace |
|---|---|
| Backend | Algoritmo core (`calculadora_service.py`) y API CRUD. **Ya implementados.** Avisar al equipo si cambia una regla. |
| Frontend | Seguir la [guía de la sección 6](#6-guía-para-frontend-milagro): pantalla de cotizar, historial, editar y eliminar. |
| QA | Revisar Swagger y confirmar que los endpoints cubren lo que la matriz necesita. |

### Semana 3 — Caja blanca y automatización

| Quién | Qué hace |
|---|---|
| QA | Seguir la [guía de la sección 7](#7-guía-para-qa): CFG, V(G), caminos, pruebas automatizadas y reporte de cobertura. |
| Backend | Ayudar a QA: explicar el código, corregir bugs que aparezcan y **no cambiar la estructura de los `if/elif`** sin avisar (el CFG se dibuja sobre ella). |
| Frontend | Validaciones del cliente (ver sección 6) y manejo de errores. |

### Semana 4 — Consolidación y entrega

| Quién | Qué hace |
|---|---|
| Todos | Ejecutar las pruebas de caja negra contra la interfaz, prueba de integración final y redactar el informe técnico. |
| Todos | Recorrer el [checklist de entrega](#12-checklist-de-entrega). |

---

## 3. Instalación y ejecución del backend

Todo se corre desde la carpeta que contiene `manage.py`.

```bash
# 1. Entorno virtual
python -m venv .venv
.venv\Scripts\activate                 # Windows
# source .venv/bin/activate            # Linux / macOS

# 2. Dependencias de desarrollo
pip install -r requirements/dev.txt

# 3. Configuración local
copy .env.example .env                 # Windows (cp en Linux/macOS)

# 4. Base de datos (cada integrante genera la suya)
python manage.py migrate
python manage.py cargar_datos_demo     # agrega 10 cotizaciones de ejemplo
python manage.py createsuperuser       # opcional, solo para entrar a /admin/

# 5. Servidor (usa config.settings.development por defecto)
python manage.py runserver 8001
```

> Se usa el puerto **8001** para no chocar con otros proyectos Django corriendo en el 8000.
> `cargar_datos_demo --limpiar` borra las cotizaciones existentes y vuelve a cargar los ejemplos.

| URL | Para qué |
|---|---|
| http://127.0.0.1:8001/api/docs/ | **Swagger**: ver y probar los endpoints (*Try it out*) |
| http://127.0.0.1:8001/api/schema/ | Esquema OpenAPI |
| http://127.0.0.1:8001/api/v1/cotizaciones/ | API navegable de DRF |
| http://127.0.0.1:8001/api/v1/health/ | Estado de la API y la BD |
| http://127.0.0.1:8001/admin/ | Panel de Django |

**Variables del `.env`** (el `.env` **no** se sube a GitHub; el ejemplo está en `.env.example`):

| Variable | Para qué | Valor local típico |
|---|---|---|
| `SECRET_KEY` | Clave de Django (obligatoria en producción) | cualquier texto largo |
| `DEBUG` | Modo depuración | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Orígenes del frontend permitidos | `http://localhost:5173,http://localhost:3000` |
| `LOG_LEVEL` | Nivel de log | `INFO` |
| `DB_ENGINE` | `sqlite` (por defecto) o `postgres` | `sqlite` |

**Entornos (settings):** `development` (local), `testing` (BD en memoria; lo usa `pytest`) y `production` (HTTPS, cookies seguras, exige `SECRET_KEY`).

---

## 4. Estructura del proyecto

```
fastexpress-backend/
├── manage.py
├── config/                              # CONFIGURACIÓN DEL PROYECTO
│   ├── settings/
│   │   ├── base.py                      # lo común a todos los entornos
│   │   ├── development.py               # local (DEBUG, API navegable)
│   │   ├── testing.py                   # pruebas (BD en memoria)
│   │   └── production.py                # servidor real (HTTPS, seguridad)
│   ├── urls.py                          # /admin, /api/v1, /api/docs
│   ├── wsgi.py
│   └── asgi.py
│
├── principal/                           # APP PRINCIPAL
│   ├── apps.py                          # PrincipalConfig: registra los signals en ready()
│   ├── urls.py                          # junta las urls de todos los módulos
│   │
│   ├── constantes/                      # reglas y catálogos de negocio
│   │   └── cotizacion.py                # tarifas BR-01..04, TipoCliente, TipoEnvio
│   │
│   ├── core/                            # COMPARTIDO por todos los módulos
│   │   ├── exceptions/
│   │   │   ├── base.py                  # ErrorNegocio (clase base)
│   │   │   └── handler.py               # formato de error uniforme de la API
│   │   ├── pagination.py                # paginación estándar (20 por página, máx. 100)
│   │   ├── serializers.py               # ErrorSerializer
│   │   └── views.py                     # health check
│   │
│   ├── modelos/                         # MODELOS (uno por archivo)
│   │   ├── base.py                      # ModeloBase: creado_en / actualizado_en
│   │   └── cotizacion.py                # tabla "cotizaciones"
│   │
│   ├── admin/
│   │   └── cotizacion_admin.py
│   │
│   ├── management/commands/
│   │   └── cargar_datos_demo.py         # llena la BD con datos de ejemplo
│   │
│   ├── migrations/
│   │
│   └── modulos/                         # MÓDULOS DE NEGOCIO
│       └── cotizaciones/                # <-- AQUÍ ESTÁ EL CRUD
│           ├── exceptions.py            # errores del módulo (LIMITE_EXCEDIDO...)
│           ├── serializers/
│           │   └── cotizacion_serializers.py
│           ├── services/
│           │   ├── calculadora_service.py   # ALGORITMO CORE (caja blanca)
│           │   ├── cotizacion_service.py    # simular, registrar, actualizar, eliminar, listar
│           │   └── tarifa_service.py        # tarifas vigentes
│           ├── views/
│           │   ├── cotizacion_views.py      # ViewSet con GET, POST, PUT, PATCH, DELETE
│           │   └── tarifa_views.py
│           ├── signals/
│           │   └── cotizacion_signals.py    # log de cotizaciones emitidas
│           └── urls.py
│
├── requirements/
│   ├── base.txt                         # para que la app funcione
│   ├── dev.txt                          # + pruebas y linter
│   └── production.txt                   # + gunicorn, PostgreSQL
└── .env.example
```

### Dónde buscar cada cosa

| Necesito... | Voy a... |
|---|---|
| Cambiar una tarifa o un porcentaje | `principal/constantes/cotizacion.py` |
| Cambiar la fórmula de cálculo | `modulos/cotizaciones/services/calculadora_service.py` |
| Agregar un campo a la tabla | `principal/modelos/cotizacion.py` y luego `makemigrations` |
| Cambiar qué se valida en la entrada | `modulos/cotizaciones/serializers/` |
| Agregar o cambiar un endpoint | `modulos/cotizaciones/views/` y su `urls.py` |
| Cambiar el formato de los errores | `principal/core/exceptions/handler.py` |
| Ver qué pasa al guardar una cotización | `modulos/cotizaciones/signals/` |

### Cómo fluye una petición

```
Frontend ─HTTP─> urls.py ─> views/ ─> serializers/ ─> services/ ─> modelos/ ─> BD
                             recibe   valida formato   reglas de     tabla
                                                       negocio
                                                          │
                                                       signals/ (log)
         <─JSON─ views/ <── serializers/ <──────────────── Cotizacion
```

| Capa | Responsabilidad | Lo que NO hace |
|---|---|---|
| `modelos/` | Define tablas y restricciones | No calcula |
| `serializers/` | Valida el **formato** y arma el JSON | No aplica reglas de negocio |
| `services/` | Lógica de negocio, guardar, consultar | No sabe de HTTP |
| `views/` | Recibe la petición, llama al servicio, responde | No calcula |
| `signals/` | Efectos secundarios al guardar (log) | No modifica la respuesta |

> **Quién valida qué:** el serializer rechaza lo que tiene mal formato (`"abc"`, 3 decimales, un tipo que no existe). El servicio rechaza lo que rompe una regla (peso ≤ 0 o > 20 kg). Por eso `25` kg **pasa** el serializer y el servicio lo rechaza con `LIMITE_EXCEDIDO`.

### Cómo agregar un módulo nuevo (escalabilidad)

Si mañana se agrega, por ejemplo, el módulo de **envíos**:

1. Crear `principal/modulos/envios/` con `serializers/`, `services/`, `views/` y `signals/`, más su `urls.py` y su `exceptions.py`.
2. Crear el modelo en `principal/modelos/envio.py` y registrarlo en `principal/modelos/__init__.py`.
3. Si tiene constantes, crear `principal/constantes/envio.py`.
4. Incluir sus rutas en `principal/urls.py`: `path("", include("principal.modulos.envios.urls"))`.
5. Si tiene signals, importarlos en `PrincipalConfig.ready()`.
6. Crear `tests/unit/envios/` y `tests/integration/envios/`.

Ningún módulo toca el código de otro: comparten solo `core/`, `modelos/` y `constantes/`.

---

## 5. API REST (CRUD completo)

Base: `http://127.0.0.1:8001/api/v1/` · Formato: JSON · Sin login (API pública).

| Acción | Método | Ruta | Respuesta |
|---|---|---|---|
| Calcular **sin guardar** (vista previa) | POST | `/cotizaciones/calcular/` | 200 |
| Calcular y **guardar** | POST | `/cotizaciones/` | 201 |
| Listar (paginado, con filtros) | GET | `/cotizaciones/` | 200 |
| Detalle | GET | `/cotizaciones/{id}/` | 200 / 404 |
| Reemplazar los 3 datos y recalcular | PUT | `/cotizaciones/{id}/` | 200 / 400 / 404 / 422 |
| Cambiar solo algunos datos y recalcular | PATCH | `/cotizaciones/{id}/` | 200 / 400 / 404 / 422 |
| Eliminar | DELETE | `/cotizaciones/{id}/` | 204 (sin cuerpo) / 404 |
| Reglas y tarifas vigentes | GET | `/tarifas/` | 200 |
| Estado de la API y la BD | GET | `/health/` | 200 |

**El cliente nunca envía totales, descuentos ni recargos.** Solo manda peso, tipo de cliente y tipo de envío; el servidor calcula todo el desglose.

**Cuerpo para POST, `calcular/` y PUT** (los tres campos son obligatorios):

```json
{ "peso_kg": "10.00", "tipo_cliente": "FRECUENTE", "tipo_envio": "EXPRESS" }
```

En **PATCH** se envía solo lo que cambia, por ejemplo `{ "tipo_envio": "ESTANDAR" }`; lo demás conserva su valor actual y el servidor recalcula todo.

| Campo | Valores permitidos |
|---|---|
| `peso_kg` | Mayor a 0 y máximo 20.00, con máximo 2 decimales |
| `tipo_cliente` | `NUEVO`, `FRECUENTE`, `VIP` |
| `tipo_envio` | `ESTANDAR`, `EXPRESS` |

**Respuesta de una cotización (201 / 200):**

```json
{
  "id": 11,
  "peso_kg": "10.00",
  "tipo_cliente": "FRECUENTE",
  "tipo_envio": "EXPRESS",
  "costo_base": "5.00",
  "tarifa_por_kg": "4.00",
  "costo_peso": "40.00",
  "subtotal": "45.00",
  "porcentaje_descuento": "0.10",
  "descuento": "4.50",
  "porcentaje_recargo": "0.25",
  "recargo": "11.25",
  "total": "51.75",
  "creado_en": "2026-10-12T14:22:19-05:00",
  "actualizado_en": "2026-10-12T14:22:19-05:00"
}
```

En `/calcular/`, `id`, `creado_en` y `actualizado_en` vienen en `null` porque no se guarda nada. Los montos van como **texto** para no perder precisión en JavaScript.

**Listado paginado:** `GET /cotizaciones/?tipo_cliente=VIP&tipo_envio=EXPRESS&page=1&page_size=50`

```json
{ "count": 10, "next": null, "previous": null, "results": [ { "...": "una cotización" } ] }
```

Por defecto 20 por página (máximo 100). Pedir una página que no existe devuelve 404.

**Errores (siempre el mismo formato):**

```json
{ "codigo": "LIMITE_EXCEDIDO", "detalle": "Envío rechazado: el peso máximo permitido es 20.00 kg." }
```

| Código | HTTP | Cuándo |
|---|---|---|
| `DATOS_INVALIDOS` | 400 | Falta un campo, formato incorrecto (`"abc"`, más de 2 decimales), tipo o filtro que no existe. `detalle` es un objeto con el error de cada campo |
| `PESO_INVALIDO` | 400 | Peso ≤ 0 |
| `LIMITE_EXCEDIDO` | 422 | Peso > 20.00 kg |
| `NOT_FOUND` | 404 | La cotización no existe (o la página pedida no existe) |
| `METHOD_NOT_ALLOWED` | 405 | Método que la ruta no admite (por ejemplo `DELETE /cotizaciones/` sin id) |

> `TIPO_CLIENTE_INVALIDO` y `TIPO_ENVIO_INVALIDO` existen en el servicio, pero por la API nunca se ven: el serializer ya rechaza esos valores con `DATOS_INVALIDOS`. Sirven para probar el servicio directamente (caja blanca).

---

## 6. Guía para Frontend (Milagro)

> Esta sección es para quien conecta la interfaz con el backend. No hace falta entender Django: solo levantar el servidor y consumir los endpoints. Sigue los pasos en orden.

### Paso 1. Levantar el backend (la primera vez)

Sigue la [sección 3](#3-instalación-y-ejecución-del-backend), pasos 1 al 4. Si algo falla, avisa a Mario.

### Paso 2. Prender el servidor (cada vez que trabajes)

```bash
.venv\Scripts\activate
python manage.py runserver 8001
```

Déjalo corriendo en esa terminal y abre **otra** terminal para tu frontend.

### Paso 3. Comprobar que funciona

| Abre en el navegador | Debes ver |
|---|---|
| http://127.0.0.1:8001/api/v1/health/ | `{"estado": "ok", "base_de_datos": "ok"}` |
| http://127.0.0.1:8001/api/docs/ | Swagger con todos los endpoints; el botón *Try it out* los prueba |

### Paso 4. Configurar tu frontend

Usa una sola constante para la URL, así si cambia el puerto lo cambias en un solo lugar:

```js
// src/config.js
export const API_URL = "http://127.0.0.1:8001/api/v1";
```

- **CORS:** el backend ya acepta `http://localhost:5173` (Vite) y `http://localhost:3000`. Si tu frontend corre en otro puerto, agrégalo en el `.env` del backend: `CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:TU_PUERTO` y reinicia el servidor.
- No se necesita login ni token.
- Siempre envía el header `Content-Type: application/json`.

### Paso 5. Qué pantalla usa qué endpoint

| Pantalla / acción | Método | Ruta |
|---|---|---|
| Formulario de cotizar con **vista previa** (mientras el usuario escribe) | POST | `/cotizaciones/calcular/` |
| Botón **Guardar cotización** | POST | `/cotizaciones/` |
| Tabla / historial | GET | `/cotizaciones/` (con `?page=` y filtros) |
| Ver el detalle | GET | `/cotizaciones/{id}/` |
| Editar (formulario completo) | PUT | `/cotizaciones/{id}/` |
| Editar (solo un campo) | PATCH | `/cotizaciones/{id}/` |
| Eliminar | DELETE | `/cotizaciones/{id}/` |
| Mostrar tarifas y reglas en pantalla (sin quemarlas en el código) | GET | `/tarifas/` |

Detalle de cuerpos, respuestas y códigos: [sección 5](#5-api-rest-crud-completo).

### Paso 6. Código de ejemplo

```js
import { API_URL } from "./config";

// Función común: si la respuesta no es 2xx, lanza el error {codigo, detalle}
async function pedir(ruta, opciones = {}) {
  const res = await fetch(`${API_URL}${ruta}`, {
    headers: { "Content-Type": "application/json" },
    ...opciones,
  });
  if (res.status === 204) return null;            // DELETE: sin cuerpo
  const cuerpo = await res.json();
  if (!res.ok) throw cuerpo;                      // { codigo, detalle }
  return cuerpo;
}

// Vista previa (no guarda)
export const calcular = (datos) =>
  pedir("/cotizaciones/calcular/", { method: "POST", body: JSON.stringify(datos) });

// Guardar
export const guardar = (datos) =>
  pedir("/cotizaciones/", { method: "POST", body: JSON.stringify(datos) });

// Listar con filtros: listar({ tipo_cliente: "VIP", page: 2 })
export const listar = (filtros = {}) =>
  pedir(`/cotizaciones/?${new URLSearchParams(filtros)}`);

// Detalle
export const obtener = (id) => pedir(`/cotizaciones/${id}/`);

// Editar completo (PUT) o parcial (PATCH)
export const reemplazar = (id, datos) =>
  pedir(`/cotizaciones/${id}/`, { method: "PUT", body: JSON.stringify(datos) });
export const editar = (id, cambios) =>
  pedir(`/cotizaciones/${id}/`, { method: "PATCH", body: JSON.stringify(cambios) });

// Eliminar
export const eliminar = (id) => pedir(`/cotizaciones/${id}/`, { method: "DELETE" });

// Tarifas vigentes
export const tarifas = () => pedir("/tarifas/");
```

### Paso 7. Manejo de errores

Todos los errores llegan con el mismo formato, así que un solo `catch` basta:

```js
try {
  const cotizacion = await guardar(datos);
} catch (error) {
  // error = { codigo: "LIMITE_EXCEDIDO", detalle: "Envío rechazado: ..." }
  mostrarMensaje(error.detalle);
}
```

| Código | Qué mostrar al usuario |
|---|---|
| `DATOS_INVALIDOS` | Revisa los campos. `detalle` trae un objeto, por ejemplo `{ "peso_kg": ["..."] }`: muestra cada mensaje junto a su campo |
| `PESO_INVALIDO` | El peso debe ser mayor a 0 |
| `LIMITE_EXCEDIDO` | El peso máximo es 20 kg: bloquear el envío |
| `NOT_FOUND` | La cotización no existe (quizá ya se eliminó) |

Cuando `detalle` es texto (`PESO_INVALIDO`, `LIMITE_EXCEDIDO`, `NOT_FOUND`) muéstralo tal cual: ya viene en español. Cuando es un objeto (`DATOS_INVALIDOS`), recórrelo por campo.

### Paso 8. Qué debes tener en cuenta

1. **El dinero llega como texto** (`"51.75"`, `"0.10"`). Para mostrarlo usa `Number(valor).toFixed(2)`. **No hagas cuentas en el frontend:** el total siempre lo calcula el backend.
2. **El peso** se envía como texto o número, con máximo 2 decimales (`"10.00"` o `10`).
3. **El listado viene paginado:** la tabla se arma con `results`; `count` sirve para el paginador.
4. **Validaciones en la interfaz** (solo ayudan al usuario; el backend valida igual):
   - Peso: número entre 0.01 y 20.00, máximo 2 decimales.
   - Cliente y envío: `<select>` con los valores permitidos, nunca texto libre.
5. **Orden de cálculo** (por si lo explicas en pantalla): subtotal = 5.00 + peso × tarifa; descuento y recargo se calculan sobre ese mismo subtotal; total = subtotal − descuento + recargo.

### Paso 9. Dónde está el código del CRUD (solo para consultar)

Todo está en `principal/modulos/cotizaciones/`:

| Qué quieres ver | Archivo |
|---|---|
| Las rutas | `urls.py` |
| Los endpoints (GET, POST, PUT, PATCH, DELETE) | `views/cotizacion_views.py` |
| Qué campos se piden y se devuelven | `serializers/cotizacion_serializers.py` |
| Cómo se calcula el total | `services/calculadora_service.py` |
| Guardar, editar, eliminar, listar | `services/cotizacion_service.py` |
| Los errores y sus códigos | `exceptions.py` |

**No modifiques estos archivos.** Si crees que hay un error, avisa a Mario.

---

## 7. Guía para QA

> Todo lo que necesitas para el informe: caja negra, caja blanca y cobertura.
> El código a probar es `calcular_cotizacion()` en `principal/modulos/cotizaciones/services/calculadora_service.py`. Es una **función pura**: no usa base de datos ni HTTP, así que se prueba sin preparar nada.

### 7.1 Pruebas de caja negra (diseño sin mirar el código)

Los resultados esperados de abajo salen de las reglas del enunciado y están verificados contra el sistema.

**a) Particiones de equivalencia del peso**

| Partición | Rango | Tipo | Resultado esperado |
|---|---|---|---|
| P1 | ≤ 0 | Inválida | 400 `PESO_INVALIDO` |
| P2 | 0.01 – 5.00 | Válida | tarifa 2.00 por kg |
| P3 | 5.01 – 20.00 | Válida | tarifa 4.00 por kg |
| P4 | > 20.00 | Inválida | 422 `LIMITE_EXCEDIDO` |
| P5 | No numérico (`"abc"`) o más de 2 decimales | Inválida | 400 `DATOS_INVALIDOS` |

**b) Análisis de valores límite (BVA) del peso** (cliente NUEVO, envío ESTANDAR)

| Peso | Resultado | Tarifa | Total |
|---|---|---|---|
| 0 | Rechazo `PESO_INVALIDO` | — | — |
| 0.01 | Válido | 2.00 | 5.02 |
| 0.02 | Válido | 2.00 | 5.04 |
| 4.99 | Válido | 2.00 | 14.98 |
| 5.00 | Válido | 2.00 | 15.00 |
| 5.01 | Válido | 4.00 | 25.04 |
| 5.02 | Válido | 4.00 | 25.08 |
| 19.99 | Válido | 4.00 | 84.96 |
| 20.00 | Válido | 4.00 | 85.00 |
| 20.01 | Rechazo `LIMITE_EXCEDIDO` | — | — |

**c) Particiones y BVA del Monto** (Monto = total cotizado, ver sección 1)

El total no se ingresa, se calcula; sus límites salen de combinar los extremos:

| Caso | Entrada | Total |
|---|---|---|
| Monto mínimo | 0.01 kg, VIP, ESTANDAR | 4.02 |
| Monto mínimo sin descuento | 0.01 kg, NUEVO, ESTANDAR | 5.02 |
| Monto máximo | 20.00 kg, NUEVO, EXPRESS | 106.25 |

El total nunca es negativo (lo garantiza también una restricción en la base de datos).

**d) Tabla de decisión** (Tipo de cliente × Tipo de envío, con 10 kg)

| # | Cliente | Envío | Descuento | Recargo | Total esperado |
|---|---|---|---|---|---|
| 1 | NUEVO | ESTANDAR | 0 % | 0 % | 45.00 |
| 2 | NUEVO | EXPRESS | 0 % | 25 % | 56.25 |
| 3 | FRECUENTE | ESTANDAR | 10 % | 0 % | 40.50 |
| 4 | FRECUENTE | EXPRESS | 10 % | 25 % | 51.75 |
| 5 | VIP | ESTANDAR | 20 % | 0 % | 36.00 |
| 6 | VIP | EXPRESS | 20 % | 25 % | 47.25 |

### 7.2 Pruebas de caja blanca (CFG y complejidad ciclomática)

En el código, cada línea de decisión lleva un comentario `[N#]` con su nodo del grafo. Si Backend cambia los `if/elif`, hay que rehacer el CFG.

**Puntos de decisión de `calcular_cotizacion`** (8):

| Decisión | Condición | Rama verdadera | Rama falsa |
|---|---|---|---|
| D1 | `peso <= 0` | `PesoInvalidoError` | sigue |
| D2 | `peso > 20.00` | `LimiteExcedidoError` | sigue |
| D3 | `peso <= 5.00` | tarifa 2.00 | tarifa 4.00 |
| D4 | cliente == NUEVO | 0 % | evalúa D5 |
| D5 | cliente == FRECUENTE | 10 % | evalúa D6 |
| D6 | cliente == VIP | 20 % | `TipoClienteInvalidoError` |
| D7 | envío == ESTANDAR | 0 % | evalúa D8 |
| D8 | envío == EXPRESS | 25 % | `TipoEnvioInvalidoError` |

**Complejidad ciclomática:**

```
V(G) = decisiones + 1 = 8 + 1 = 9
```

Por tanto hay **9 caminos independientes** (el mínimo de pruebas para cubrir todas las ramas):

| Camino | Recorre | Entrada de ejemplo | Resultado |
|---|---|---|---|
| C1 | D1 verdadera | peso 0 | `PesoInvalidoError` |
| C2 | D1 falsa, D2 verdadera | peso 25 | `LimiteExcedidoError` |
| C3 | Camino base: D3 verdadera, D4 verdadera, D7 verdadera | 2 kg, NUEVO, ESTANDAR | total 9.00 |
| C4 | Como C3 pero D3 falsa | 10 kg, NUEVO, ESTANDAR | tarifa 4.00, total 45.00 |
| C5 | Como C3 pero D4 falsa, D5 verdadera | 2 kg, FRECUENTE, ESTANDAR | total 8.10 |
| C6 | D4 y D5 falsas, D6 verdadera | 2 kg, VIP, ESTANDAR | total 7.20 |
| C7 | D4, D5 y D6 falsas | 2 kg, `"RARO"`, ESTANDAR | `TipoClienteInvalidoError` |
| C8 | Como C3 pero D7 falsa, D8 verdadera | 2 kg, NUEVO, EXPRESS | total 11.25 |
| C9 | D7 y D8 falsas | 2 kg, NUEVO, `"RARO"` | `TipoEnvioInvalidoError` |

Estos caminos están en `tests/unit/cotizaciones/test_calculadora_caja_blanca.py`. El diagrama del CFG y el desarrollo paso a paso van en `docs/CAJA_BLANCA.md`. Para el informe, el CFG se dibuja con los nodos `[N1]`–`[N21]` del código.

> Los `TipoClienteInvalidoError` y `TipoEnvioInvalidoError` solo se alcanzan llamando a la función directamente. Por la API el serializer los bloquea antes, por eso esos caminos se prueban en pruebas **unitarias**, no por HTTP.

### 7.3 Pruebas de la API (integración)

Qué debe verificarse por HTTP, con el resultado esperado:

| Prueba | Resultado |
|---|---|
| POST `/cotizaciones/` con datos válidos | 201 y desglose completo |
| POST `/cotizaciones/calcular/` | 200, `id` en `null`, no queda registro en la BD |
| POST con peso 0 o negativo | 400 `PESO_INVALIDO` |
| POST con peso 20.01 | 422 `LIMITE_EXCEDIDO` |
| POST con peso `5.005` o `"abc"` | 400 `DATOS_INVALIDOS` |
| POST con tipo de cliente inexistente | 400 `DATOS_INVALIDOS` |
| POST sin campos | 400 `DATOS_INVALIDOS` con un error por campo |
| GET lista con y sin filtros | 200 con `count`, `next`, `previous`, `results` |
| GET con filtro inválido | 400 `DATOS_INVALIDOS` |
| GET `/cotizaciones/{id}/` inexistente | 404 `NOT_FOUND` |
| PUT con los 3 campos | 200 y desglose recalculado |
| PUT incompleto | 400 `DATOS_INVALIDOS` |
| PATCH con un solo campo | 200, lo demás se conserva y se recalcula |
| PATCH con peso 25 | 422 y la cotización **no** cambia |
| DELETE existente | 204 y después GET devuelve 404 |
| DELETE inexistente | 404 `NOT_FOUND` |
| DELETE `/cotizaciones/` (sin id) | 405 `METHOD_NOT_ALLOWED` |

> **Pendiente de revisar:** si las pruebas de integración de `tests/integration/cotizaciones/test_cotizacion_api.py` se escribieron antes del CRUD completo, es probable que alguna espere `405` en PUT, PATCH o DELETE y ahora falle, y que PUT, PATCH y DELETE no tengan pruebas propias. Corre `pytest` y completa lo que falte con la tabla de arriba.

### 7.4 Reporte de cobertura (mínimo 85 % de líneas y ramas)

```bash
pytest
```

Genera la tabla en la terminal, **`htmlcov/index.html`** (reporte visual; de ahí sale la captura para el informe) y `coverage.xml`.

Cómo leerlo:

- `Stmts` / `Miss`: cobertura de **líneas**.
- `Branch` / `BrPart`: cobertura de **ramas** (cada `if` debe evaluarse como verdadero y como falso).
- Si la cobertura total baja de 85 %, `pytest` falla.

Para el informe, adjunta la captura de `htmlcov/index.html` y analiza qué archivos tienen menos cobertura y por qué.

---

## 8. Base de datos local

**SQLite:** un solo archivo, `db.sqlite3`, en la raíz del proyecto. No hay que instalar ningún motor.

> `db.sqlite3` y `.env` están en `.gitignore`: **no se suben a GitHub**. Cada integrante genera su base con `migrate` + `cargar_datos_demo`.

**Ver las tablas:**

1. **DB Browser for SQLite** (https://sqlitebrowser.org): *Open Database* → `db.sqlite3` → *Browse Data* → tabla `cotizaciones`.
2. **VS Code:** extensión *SQLite Viewer*, clic en `db.sqlite3`.
3. **Admin de Django:** `/admin/` → Cotizaciones (necesita `createsuperuser`).

```sql
SELECT id, peso_kg, tipo_cliente, tipo_envio, subtotal, descuento, recargo, total, creado_en
FROM cotizaciones
ORDER BY total DESC;
```

**Tabla `cotizaciones`:**

| Columna | Tipo | Descripción |
|---|---|---|
| id | entero, PK | consecutivo |
| peso_kg | decimal(5,2) | 0.01 – 20.00 |
| tipo_cliente | texto | NUEVO / FRECUENTE / VIP |
| tipo_envio | texto | ESTANDAR / EXPRESS |
| costo_base | decimal | 5.00 (BR-01) |
| tarifa_por_kg | decimal | 2.00 o 4.00 (BR-02) |
| costo_peso | decimal | peso × tarifa |
| subtotal | decimal | costo_base + costo_peso |
| porcentaje_descuento | decimal | 0.00 / 0.10 / 0.20 (BR-03) |
| descuento | decimal | subtotal × % |
| porcentaje_recargo | decimal | 0.00 / 0.25 (BR-04) |
| recargo | decimal | subtotal × % |
| total | decimal | subtotal − descuento + recargo |
| creado_en / actualizado_en | fecha/hora | automáticas (`ModeloBase`) |

Restricciones `CHECK` en la BD: peso entre 0.01 y 20.00, tipos válidos y total ≥ 0. Índice por `(tipo_cliente, tipo_envio)` para los filtros del listado. Se guarda el desglose completo para que las cotizaciones viejas conserven los valores con los que se calcularon, aunque cambien las tarifas.

**PostgreSQL (opcional):** `pip install -r requirements/production.txt` y en el `.env` poner `DB_ENGINE=postgres` más `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`. Luego `python manage.py migrate`.

---



## 9. Buenas prácticas aplicadas

- Arquitectura por capas, una carpeta por capa y un archivo por responsabilidad.
- Módulos de negocio aislados en `principal/modulos/`, con un `core/` compartido.
- Settings separados por entorno (development / testing / production); secretos solo en `.env`.
- `ModeloBase` abstracto con los campos de auditoría.
- Sin números mágicos: todo está en `constantes/`.
- Validación en tres niveles: el serializer revisa el formato, el servicio las reglas y la BD tiene restricciones `CHECK`.
- Escritura segura: primero se calcula (y se rechaza si viola una regla), después se guarda, así una petición rechazada nunca deja datos a medias.
- Errores de negocio jerárquicos (`ErrorNegocio`) con código estable y manejador global.
- Signals para efectos secundarios, registrados en `AppConfig.ready()`.
- Logging configurado en vez de `print`.
- Dinero con `Decimal`.
- API versionada (`/api/v1/`), paginada, documentada con OpenAPI y con health check.
- Linter (ruff), EditorConfig, cobertura mínima obligatoria y CI.

---

## 10. Flujo con Git

```bash
git checkout -b feature/nombre
ruff check . && pytest            # nunca subir con errores
git commit -m "feat: ..."         # feat / fix / test / docs / refactor
git push origin feature/nombre    # luego Pull Request hacia main
```

- Nadie sube directo a `main`: todo entra por Pull Request.
- Backend y Frontend trabajan en ramas separadas y no editan los archivos del otro.
- Antes de subir, revisa que no vayan `.venv/`, `.env`, `db.sqlite3` ni `__pycache__/` (el `.gitignore` ya los cubre).

---

## 11. Checklist de entrega

**Código (repositorio GitHub)**
- [ ] Backend y Frontend subidos y estructurados
- [ ] Suite de pruebas automatizadas configurada (`pytest`)
- [ ] README con instrucciones para correr todo
- [ ] Sin `.env`, `db.sqlite3` ni credenciales en el repositorio

**Informe técnico**
- [ ] Plan de caja negra: particiones de equivalencia y BVA para `Peso` y `Monto`
- [ ] Tabla de decisión `Tipo de cliente` + `Tipo de envío`
- [ ] Diagrama del CFG de `calcular_cotizacion`
- [ ] Cálculo paso a paso de V(G) = 9
- [ ] Caminos independientes identificados y probados (C1–C9)
- [ ] Captura y análisis del reporte de cobertura (mínimo 85 % de líneas y ramas)
- [ ] Interpretaciones del enunciado documentadas (sección 1)

---

## 12. Problemas comunes

| Síntoma | Causa y solución |
|---|---|
| `CORS error` en la consola del navegador | El puerto del frontend no está en `CORS_ALLOWED_ORIGINS` (sección 6, paso 4) |
| `Failed to fetch` / `ERR_CONNECTION_REFUSED` | El servidor del backend no está corriendo (sección 6, paso 2) |
| El puerto 8001 está ocupado | `python manage.py runserver 8002` y cambia `API_URL` |
| `405 Method Not Allowed` en PUT / PATCH / DELETE | La ruta debe terminar en `/` y llevar el id: `/cotizaciones/11/` |
| `404` con `"Página inválida."` | Pediste un `page` que no existe; la lista está vacía o es más corta |
| La lista sale vacía | Falta correr `python manage.py cargar_datos_demo` |
| `no such table` | Falta `python manage.py migrate` |
| PowerShell no deja activar el entorno | Una vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `pytest` falla por cobertura | Bajó del 85 %; abre `htmlcov/index.html` y revisa qué líneas o ramas faltan |
| `ModuleNotFoundError` | El entorno virtual no está activado o falta `pip install -r requirements/dev.txt` |

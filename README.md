# FastExpress — Backend (Django REST Framework)

Módulo de **Cotización de Envíos y Descuentos** del Proyecto Integrador de *Calidad de Software*.
Backend organizado como un proyecto escalable: cada capa tiene su carpeta y cada módulo de negocio vive aislado en `principal/modulos/`.

| | |
|---|---|
| Lenguaje | Python 3.11+ |
| Framework | Django 5.2 LTS + Django REST Framework |
| Base de datos | SQLite local (`db.sqlite3`), PostgreSQL opcional |
| Pruebas | PyTest + pytest-django + pytest-cov (unitarias e integración) |
| Calidad de código | Ruff (linter) + EditorConfig |
| Integración continua | GitHub Actions (lint, migraciones, pruebas, cobertura) |
| Documentación API | Swagger en `/api/docs/` |
| Cobertura | **100 % de líneas y ramas**, 74 pruebas (mínimo exigido: 85 %) |

---

## 1. Estructura del proyecto

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
│   │   ├── pagination.py                # paginación estándar
│   │   ├── serializers.py               # ErrorSerializer
│   │   └── views.py                     # health check
│   │
│   ├── modelos/                         # MODELOS (uno por archivo)
│   │   ├── base.py                      # ModeloBase: creado_en / actualizado_en
│   │   └── cotizacion.py                # tabla "cotizaciones"
│   │
│   ├── admin/                           # admin de Django (uno por modelo)
│   │   └── cotizacion_admin.py
│   │
│   ├── management/commands/
│   │   └── cargar_datos_demo.py         # llena la BD con datos de ejemplo
│   │
│   ├── migrations/
│   │
│   └── modulos/                         # MÓDULOS DE NEGOCIO
│       └── cotizaciones/
│           ├── exceptions.py            # errores del módulo (LIMITE_EXCEDIDO...)
│           ├── serializers/
│           │   └── cotizacion_serializers.py
│           ├── services/
│           │   ├── calculadora_service.py   # ALGORITMO CORE (caja blanca)
│           │   ├── cotizacion_service.py    # simular, registrar, listar
│           │   └── tarifa_service.py        # tarifas vigentes
│           ├── views/
│           │   ├── cotizacion_views.py
│           │   └── tarifa_views.py
│           ├── signals/
│           │   └── cotizacion_signals.py    # log de cotizaciones emitidas
│           └── urls.py
│
├── tests/                               # PRUEBAS (espejo de la estructura)
│   ├── conftest.py                      # fixtures compartidas
│   ├── unit/                            # sin base de datos, milisegundos
│   │   └── cotizaciones/
│   │       ├── test_calculadora_caja_blanca.py   # 9 caminos, V(G)=9
│   │       └── test_calculadora_caja_negra.py    # PE, BVA, tabla de decisión
│   └── integration/                     # con base de datos y HTTP
│       ├── cotizaciones/
│       │   ├── test_cotizacion_api.py
│       │   └── test_cotizacion_service.py
│       └── core/
│           └── test_core.py
│
├── docs/
│   ├── CAJA_BLANCA.md                   # CFG, cálculo de V(G), caminos
│   └── CAJA_NEGRA.md                    # tablas de particiones, BVA y decisión
├── requirements/
│   ├── base.txt                         # para que la app funcione
│   ├── dev.txt                          # + pruebas y linter
│   └── production.txt                   # + gunicorn, PostgreSQL
├── .github/workflows/pruebas.yml        # integración continua
├── pyproject.toml                       # config de pytest, coverage y ruff
├── .editorconfig
└── .env.example
```

### Dónde buscar cada cosa

| Necesito... | Voy a... |
|---|---|
| Cambiar una tarifa o un porcentaje | `principal/constantes/cotizacion.py` |
| Cambiar la fórmula de cálculo | `modulos/cotizaciones/services/calculadora_service.py` |
| Agregar un campo a la tabla | `principal/modelos/cotizacion.py` y luego `makemigrations` |
| Cambiar qué se valida en la entrada | `modulos/cotizaciones/serializers/` |
| Agregar un endpoint | `modulos/cotizaciones/views/` y su `urls.py` |
| Cambiar el formato de los errores | `principal/core/exceptions/handler.py` |
| Ver qué pasa al guardar una cotización | `modulos/cotizaciones/signals/` |

### Cómo fluye una petición

```
Frontend ─POST─> urls.py ─> views/ ─> serializers/ ─> services/ ─> modelos/ ─> BD
                             recibe   valida formato   reglas de     tabla
                                                       negocio
                                                          │
                                                       signals/ (log)
         <─JSON─ views/ <── serializers/ <──────────────── Cotizacion
```

| Capa | Responsabilidad | Lo que NO hace |
|---|---|---|
| `modelos/` | Define tablas y restricciones | No calcula |
| `serializers/` | Valida formato y arma el JSON | No aplica reglas de negocio |
| `services/` | Lógica de negocio, guardar, consultar | No sabe de HTTP |
| `views/` | Recibe la petición, llama al servicio, responde | No calcula |
| `signals/` | Efectos secundarios al guardar (log, auditoría) | No modifica la respuesta |

### Cómo agregar un módulo nuevo (escalabilidad)

Si mañana se agrega, por ejemplo, el módulo de **envíos**:

1. Crear `principal/modulos/envios/` con las carpetas `serializers/`, `services/`, `views/` y `signals/`, más su `urls.py` y su `exceptions.py`.
2. Crear el modelo en `principal/modelos/envio.py` y registrarlo en `principal/modelos/__init__.py`.
3. Si tiene constantes, crear `principal/constantes/envio.py`.
4. Incluir sus rutas en `principal/urls.py`: `path("", include("principal.modulos.envios.urls"))`.
5. Si tiene signals, importarlos en `PrincipalConfig.ready()`.
6. Crear `tests/unit/envios/` y `tests/integration/envios/`.

Ningún módulo toca el código de otro: comparten solo `core/`, `modelos/` y `constantes/`.

---

## 2. Instalación y ejecución

```bash
# 1. Entorno virtual
python -m venv .venv
.venv\Scripts\activate                 # Windows
# source .venv/bin/activate            # Linux / macOS

# 2. Dependencias de desarrollo
pip install -r requirements/dev.txt

# 3. Configuración local
copy .env.example .env                 # Windows (cp en Linux/macOS)

# 4. Base de datos (si no usas el db.sqlite3 incluido)
python manage.py migrate
python manage.py cargar_datos_demo
python manage.py createsuperuser

# 5. Servidor (usa config.settings.development por defecto)
python manage.py runserver 8001
```

> Se usa el puerto **8001** para no chocar con otros proyectos Django que tengas corriendo en el 8000.

| URL | Para qué |
|---|---|
| http://127.0.0.1:8001/api/docs/ | Swagger: probar los endpoints |
| http://127.0.0.1:8001/api/v1/cotizaciones/ | API navegable de DRF |
| http://127.0.0.1:8001/api/v1/health/ | Estado de la API y la BD |
| http://127.0.0.1:8001/admin/ | Panel de Django |

---

## 3. Base de datos local

**SQLite**: un solo archivo, `db.sqlite3`, en la raíz del proyecto. No hay que instalar ningún motor.

El `.zip` trae `db.sqlite3` ya migrado, con **10 cotizaciones de ejemplo** y un usuario admin local: `admin` / `FastExpress2026`.

> El `db.sqlite3` está en `.gitignore`: no se sube a GitHub. Cada integrante genera la suya con `migrate` + `cargar_datos_demo`. La clave del admin es solo para desarrollo local.

**Ver las tablas:**
1. **DB Browser for SQLite** (https://sqlitebrowser.org): *Open Database* → `db.sqlite3` → *Browse Data* → tabla `cotizaciones`.
2. **VS Code**: extensión *SQLite Viewer*, clic en `db.sqlite3`.
3. **Admin de Django**: `/admin/` → Cotizaciones.

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
| creado_en / actualizado_en | fecha/hora | automáticas (ModeloBase) |

Restricciones `CHECK` en la BD: peso en rango, tipos válidos y total ≥ 0. Índice por `(tipo_cliente, tipo_envio)` para los filtros del listado.

**PostgreSQL local (opcional):** `pip install -r requirements/production.txt` y en el `.env` poner `DB_ENGINE=postgres` con los datos de conexión. Luego `python manage.py migrate`.

---

## 4. Reglas de negocio

| Regla | Descripción |
|---|---|
| BR-01 | Costo base 5.00 USD |
| BR-02 | 0.01–5.00 kg: 2.00/kg · 5.01–20.00 kg: 4.00/kg · > 20 kg: rechazo |
| BR-03 | NUEVO 0 % · FRECUENTE 10 % · VIP 20 % |
| BR-04 | ESTANDAR 0 % · EXPRESS +25 % sobre el subtotal |

**Interpretación acordada (para el informe):**

```
subtotal  = 5.00 + peso × tarifa_kg
descuento = subtotal × % cliente
recargo   = subtotal × 25 %   (solo EXPRESS)
total     = subtotal − descuento + recargo
```

1. Descuento y recargo se calculan **sobre el mismo subtotal**, así el orden no cambia el resultado. Si el recargo se aplicara después del descuento, FRECUENTE+EXPRESS con 10 kg daría 50.63 en vez de 51.75.
2. La tarifa por kg se aplica a **todo** el peso.
3. Peso con **máximo 2 decimales**.
4. Dinero con `Decimal` (nunca `float`), redondeo a 2 decimales con la mitad hacia arriba.

---

## 5. API REST

Base: `http://127.0.0.1:8001/api/v1/`

| Método | Ruta | Descripción | Respuesta |
|---|---|---|---|
| POST | `/cotizaciones/calcular/` | Calcula **sin guardar** (vista previa) | 200 |
| POST | `/cotizaciones/` | Calcula y **guarda** | 201 |
| GET | `/cotizaciones/` | Lista paginada. Filtros: `?tipo_cliente=VIP&tipo_envio=EXPRESS&page_size=50` | 200 |
| GET | `/cotizaciones/{id}/` | Detalle | 200 / 404 |
| GET | `/tarifas/` | Reglas vigentes | 200 |
| GET | `/health/` | Estado de la API y la BD | 200 |

**Petición:**

```json
POST /api/v1/cotizaciones/
{ "peso_kg": "10.00", "tipo_cliente": "FRECUENTE", "tipo_envio": "EXPRESS" }
```

**Respuesta 201:**

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
  "creado_en": "2026-10-10T14:22:19-05:00"
}
```

En `/calcular/`, `id` y `creado_en` vienen en `null` porque no se guarda. Los montos van como texto para no perder precisión en JavaScript.

**Errores (siempre el mismo formato):**

```json
{ "codigo": "LIMITE_EXCEDIDO", "detalle": "Envío rechazado: el peso máximo permitido es 20.00 kg." }
```

| Código | HTTP | Cuándo |
|---|---|---|
| `DATOS_INVALIDOS` | 400 | Falta un campo, formato incorrecto, tipo o filtro no permitido |
| `PESO_INVALIDO` | 400 | Peso ≤ 0 |
| `LIMITE_EXCEDIDO` | 422 | Peso > 20.00 kg |
| `NOT_FOUND` | 404 | No existe la cotización |
| `METHOD_NOT_ALLOWED` | 405 | Intento de modificar o borrar |

---

## 6. Pruebas, cobertura y calidad de código

```bash
pytest                           # toda la suite + cobertura
pytest tests/unit --no-cov       # solo unitarias (sin BD)
pytest tests/integration --no-cov
pytest -m caja_blanca --no-cov   # los 9 caminos independientes
pytest -m caja_negra --no-cov    # PE, BVA, tabla de decisión
pytest -m api --no-cov           # endpoints

ruff check .                     # revisa el estilo del código
ruff check . --fix               # corrige lo que se pueda automáticamente
```

`pytest` usa `config.settings.testing`, con una BD en memoria, así que nunca toca tu `db.sqlite3`. Además genera:
- la tabla de cobertura en la terminal;
- **`htmlcov/index.html`**, el reporte visual (de ahí sale la captura para el informe);
- `coverage.xml`.

**Cómo leer el reporte:** `Stmts`/`Miss` dan la cobertura de **líneas**. `Branch`/`BrPart` dan la de **ramas**: cada `if` tiene que evaluarse como verdadero y como falso. Si la cobertura total baja de 85 %, `pytest` falla.

**Integración continua:** en cada push a `main` o Pull Request, GitHub Actions corre ruff, revisa que no falten migraciones, ejecuta las pruebas y publica el reporte de cobertura en la pestaña *Actions*.

Diseño de pruebas: [`docs/CAJA_BLANCA.md`](docs/CAJA_BLANCA.md) y [`docs/CAJA_NEGRA.md`](docs/CAJA_NEGRA.md).

---

## 7. Buenas prácticas aplicadas

- Arquitectura por capas con una carpeta por capa y un archivo por responsabilidad.
- Módulos de negocio aislados en `principal/modulos/`, con un `core/` compartido.
- Settings separados por entorno (development / testing / production).
- `ModeloBase` abstracto con los campos de auditoría.
- Sin números mágicos: todo está en `constantes/`.
- Validación en tres niveles: el serializer revisa el formato, el servicio las reglas y la BD tiene restricciones `CHECK`.
- Errores de negocio jerárquicos (`ErrorNegocio`) con código estable y manejador global.
- Signals para efectos secundarios, registrados en `AppConfig.ready()`.
- Logging configurado, en vez de `print`.
- Dinero con `Decimal`.
- Transacciones atómicas al guardar.
- API versionada, paginada, documentada con OpenAPI y con health check.
- Linter (ruff), EditorConfig, cobertura mínima obligatoria y CI.

## 8. Flujo con Git

```bash
git checkout -b feature/nombre
ruff check . && pytest            # nunca subir con errores
git commit -m "feat: ..."         # feat / fix / test / docs / refactor
git push origin feature/nombre    # luego Pull Request hacia main
```

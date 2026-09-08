# Plantilla de arquitectura — Stack "Velonox"

> Este documento describe la **estructura técnica reutilizable** del proyecto para poder clonarla en otros proyectos: stack, organización de carpetas, patrones de código y convenciones. **No incluye** pasarelas de pago, integraciones específicas de negocio ni nada de diseño/CSS/branding — eso es intencional, este archivo es solo el "esqueleto" técnico.
>
> Pensado para que cualquier IA (o desarrollador) pueda leerlo y recrear la misma arquitectura desde cero en un proyecto nuevo.

---

## 1. Resumen del stack

| Capa | Tecnología |
|---|---|
| Backend | **FastAPI** (Python 3), servidor ASGI con **Uvicorn** |
| ORM / DB | **SQLAlchemy 2.x en modo síncrono** (no async) + **PostgreSQL** |
| Migraciones | **Alembic** |
| Auth | **JWT** (`python-jose`) + hashing con **bcrypt** |
| Rate limiting | **slowapi** (`Limiter` + `SlowAPIMiddleware`) |
| Validación / schemas | **Pydantic v2** |
| Envío de emails | API HTTP de un proveedor transaccional (ej. Resend) — **no SMTP** |
| Frontend | HTML/CSS/JS **vanilla**, sin framework ni build step |
| Hosting backend | Railway (o cualquier PaaS con soporte de `Procfile`) |
| Hosting frontend | Cloudflare Pages (o cualquier hosting de estáticos) |
| Testing | **pytest** contra una DB SQLite en memoria, con mocks de todos los servicios externos |

**Decisión de diseño clave:** todo el ORM es **síncrono**. No mezclar SQLAlchemy async en algunos endpoints y sync en otros — es una convención deliberada, no un descuido, y facilita mantener un único patrón de sesión de DB en todo el proyecto.

---

## 2. Estructura de carpetas

```
proyecto/
├── backend/
│   ├── main.py                # entrypoint FastAPI: crea la app, CORS, rate limiter, monta routers
│   ├── database.py            # engine, SessionLocal, Base, get_db()
│   ├── procfile                # comando de arranque en producción
│   ├── requirements.txt
│   ├── requirements-dev.txt   # deps solo de test/dev (pytest, etc.)
│   ├── runtime.txt             # versión de Python fijada para el hosting
│   ├── pytest.ini
│   ├── .coveragerc
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/           # un archivo por migración, autogenerado
│   ├── models/                 # un archivo por entidad (SQLAlchemy models)
│   │   └── __init__.py
│   ├── schemas/                 # un archivo por dominio (Pydantic request/response)
│   │   └── __init__.py
│   ├── routes/                  # un router por dominio, montado en main.py
│   │   └── __init__.py
│   ├── services/                # lógica de negocio / integraciones externas
│   │   └── __init__.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py              # get_current_user / get_current_admin (dependencies)
│   └── tests/
│       ├── conftest.py          # fixtures: DB en memoria + mocks de servicios externos
│       └── test_*.py            # un archivo de test por dominio
│
├── frontend/
│   ├── *.html                   # una página por archivo, cada una con su propio <style>/<script> inline
│   ├── js/
│   │   ├── api.js               # API_URL, helpers de token, apiFetch(), sistema de moneda si aplica
│   │   └── *.js                 # un helper compartido por responsabilidad (auth, carrito, etc.)
│   ├── css/                     # solo hojas de estilo *compartidas* entre varias páginas
│   ├── favicon/
│   └── _redirects                # reglas del hosting de estáticos (ej. catch-all 404)
│
├── docs/
├── package.json                  # solo si el frontend usa alguna librería vía npm/CDN (ej. animaciones)
├── CLAUDE.md / README.md         # documentación del proyecto para humanos e IA
└── .gitignore
```

---

## 3. Patrón de backend

### 3.1 `main.py` — entrypoint
Responsabilidades, en este orden:
1. Cargar variables de entorno (`load_dotenv()`).
2. Crear la instancia `FastAPI(...)`.
3. Configurar **rate limiting** (`slowapi`): un `Limiter` con `key_func` que lee la IP real del cliente desde `X-Forwarded-For` (necesario detrás de un proxy/PaaS), registrado en `app.state.limiter`, más `SlowAPIMiddleware`.
4. Configurar **CORS** de forma explícita: `allow_origins` como lista cerrada de dominios conocidos (nunca `["*"]`), `allow_methods` explícito incluyendo todos los verbos que se usen realmente (un método faltante aquí rompe silenciosamente el preflight de esa operación), `allow_headers` explícito (`Content-Type`, `Authorization`).
5. **Importar los routers después de crear `limiter`**, porque algunos routers hacen `from main import limiter` para decorar sus endpoints con `@limiter.limit(...)`.
6. `app.include_router(...)` por cada dominio.
7. Endpoints de salud: `GET /`, `GET /health`, `GET /db-check` (verifica conexión real a la DB).

### 3.2 `database.py`
- `create_engine(DATABASE_URL)`, con normalización de esquema si el proveedor de hosting usa `postgres://` en vez de `postgresql://` (caso típico de Railway/Heroku).
- `SessionLocal = sessionmaker(...)`.
- `Base = declarative_base()`.
- `get_db()` generador que abre/cierra sesión, usado como dependency (`Depends(get_db)`) en cada endpoint que toca la DB.

### 3.3 `models/`
- Un archivo por entidad, clase SQLAlchemy heredando de `Base`.
- Relaciones con `ON DELETE CASCADE` / `ON DELETE SET NULL` explícitas en la FK cuando el borrado en cascada es el comportamiento deseado.
- Timestamps con timezone: usar columnas `DateTime(timezone=True)` y, en Python, `datetime.now(timezone.utc)` — **nunca** `datetime.utcnow()` (naive) si esa columna se va a comparar contra un valor calculado en Python, para evitar `TypeError: can't compare offset-naive and offset-aware datetimes`.

### 3.4 `schemas/`
- Un archivo por dominio, con los modelos Pydantic de request/response (`*Create`, `*Update`, `*Response`).
- Separados de los modelos de SQLAlchemy: nunca se expone el modelo de DB directamente en una respuesta.

### 3.5 `routes/`
- Un router (`APIRouter`) por dominio de negocio, con su propio `prefix` y `tags`.
- Cuando dos routers comparten un mismo prefix pero cubren sub-recursos distintos (ej. algo como `/productos/{id}/variantes`), está bien tenerlos en archivos separados — no todo tiene que vivir en el archivo "dueño" del prefix.
- Los endpoints que requieren usuario autenticado usan `Depends(get_current_user)`; los que requieren admin, `Depends(get_current_admin)`.
- **Errores internos nunca se exponen tal cual al cliente** (errores de DB, de integraciones externas, tracebacks): se atrapan y se devuelve un mensaje genérico; el detalle va a logs.

### 3.6 `services/`
- Lógica de negocio e integraciones con terceros, desacoplada de las rutas.
- **Ninguna integración externa se llama directamente desde el frontend** — el backend siempre actúa de proxy usando sus propias claves desde `.env`. Esto es un patrón de seguridad central: evita exponer API keys en el navegador.
- Mismo patrón para envío de emails: una función central `send_email(to, subject, html)` con try/except que devuelve `bool`, y funciones de más alto nivel (`email_bienvenida`, `email_confirmacion_*`, etc.) que solo arman el HTML y la llaman. Si el proveedor de envío cambia, solo cambia la implementación de `send_email`.

### 3.7 `middleware/auth.py`
- `get_current_user`: extrae el JWT del header `Authorization: Bearer`, lo decodifica, busca el usuario en DB, valida que esté activo.
- `get_current_admin`: reutiliza `get_current_user` y valida el flag de admin.
- Loggear intentos fallidos con la IP real del cliente (reutilizando el mismo `get_client_ip` de `main.py`).

### 3.8 Autenticación
- JWT con `python-jose`, `SECRET_KEY`/`ALGORITHM`/`ACCESS_TOKEN_EXPIRE_MINUTES` desde `.env`.
- Hashing de contraseñas con `bcrypt`.
- Flujo estándar: `POST /auth/register`, `POST /auth/login`, `POST /auth/forgot-password`, `POST /auth/reset-password` (con tabla de tokens de un solo uso y expiración).
- Cuidado con enumeración de usuarios: las respuestas de registro/login no deben revelar si un email ya existe o no de forma que facilite enumerar cuentas.

### 3.9 Migraciones (Alembic)
- `alembic revision --autogenerate -m "descripcion"` para generar, `alembic upgrade head` para aplicar.
- En producción, el comando de arranque corre `alembic upgrade head` **antes** de levantar el servidor (ver `procfile`).
- **Orden crítico:** una migración "breaking" para el código que está actualmente desplegado puede romper producción incluso antes de que el código nuevo se despliegue (ej. un `DROP COLUMN` que el handler viejo todavía lee). Nunca tratar "correr la migración" y "desplegar el código" como pasos independientes/reordenables — confirmar que el código compatible ya está desplegado, o se despliega inmediatamente después.

### 3.10 Testing
- `pytest`, corrido desde `backend/`.
- DB de test: **SQLite en memoria**, no la DB real. Si el motor de producción es Postgres, el `conftest.py` necesita parches específicos para imitar su comportamiento (activar el pragma de foreign keys, columnas datetime timezone-aware, binding laxo de UUID si se usan, etc.).
- **Todo servicio externo se mockea** (pasarela de pago, proveedor de fulfillment, proveedor de email, fuente de tasas de cambio, cualquier API de IA, etc.) — el test suite nunca debe golpear una API real ni la DB real.
- Cobertura configurada vía `.coveragerc`, corrida con `pytest --cov=.`.

### 3.11 Variables de entorno típicas (`.env.example`)
```
DATABASE_URL=postgresql://user:password@localhost:5432/db_name

SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

FRONTEND_URL=

# Claves de integraciones externas del proyecto (pago, fulfillment, IA, etc.)
# van aquí, nunca hardcodeadas ni expuestas al frontend.
```

---

## 4. Patrón de frontend

- **Sin bundler ni framework**: archivos `.html` planos, cada uno con su propio `<style>`/`<script>` inline. No hay paso de build.
- Helpers compartidos viven en `frontend/js/`, un archivo por responsabilidad (ej. `api.js` para todo lo de red/auth, un archivo por feature transversal como carrito o checkout).
- **Todos los links y referencias a assets (`href`/`src`) usan rutas absolutas** (con `/` inicial, ej. `/js/api.js`, `/admin.html`) en vez de relativas — convención a mantener en cualquier página nueva.
- `js/api.js` (o equivalente) centraliza:
  - `API_URL` apuntando al backend.
  - Helpers de token (`getToken`/`setToken`/`removeToken`/`isLoggedIn`) sobre `localStorage`.
  - Un wrapper único `apiFetch(endpoint, options)` que agrega el header `Authorization` automáticamente si hay token, y maneja 401 **solo cuando efectivamente había un token adjunto** (un 401 sin token, ej. credenciales incorrectas en el login, no debe forzar un redirect — debe caer al `throw` normal para que la página pueda mostrar el mensaje de error).
- Si hay un CMS/editor de contenido tipo "bloques" (secciones configurables por página), usar un único renderer de bloques compartido entre páginas de contenido, en vez de reimplementarlo por página — evita que las páginas diverjan en cómo interpretan el mismo tipo de bloque.
- Gotcha a tener presente si en algún momento se generan strings de HTML con `<script>...</script>` embebidos dentro de un template literal que a su vez vive dentro de otro `<script>`: el string literal `</script>` cierra el tag que lo contiene sin importar el contexto de JS — escribirlo como `<\/script>` en esos casos.
- Panel de administración (si aplica) como SPA de una sola página con tabs, en vez de multi-page — más simple de mantener sin framework.

---

## 5. Patrón de seguridad transversal

1. **Nunca** llamar APIs externas directamente desde el navegador usando claves propias del proyecto — siempre proxear a través del backend, que guarda las claves en su `.env`. Única excepción aceptable: un servicio de terceros que **no** requiere ni maneja secretos del proyecto (ej. un webhook de un chatbot externo que no conoce ninguna clave interna) — y aun así, documentar explícitamente por qué esa excepción es segura, para no usarla como precedente de otras integraciones directas.
2. CORS con `allow_origins`/`allow_methods`/`allow_headers` explícitos, nunca `["*"]`.
3. Errores internos (DB, integraciones) nunca se devuelven verbatim al cliente.
4. Rate limiting en endpoints sensibles (login, registro, reset de password) vía `slowapi`.
5. Contraseñas siempre hasheadas (bcrypt), nunca en texto plano ni en logs.
6. Tokens de un solo uso (reset de password, etc.) con expiración y comparación timezone-aware.
7. Respuestas de auth diseñadas para no filtrar si un email/usuario existe (evitar enumeración de cuentas).

---

## 6. Despliegue

- **Backend**: PaaS tipo Railway. `procfile` con el patrón `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT`. Logs de producción accesibles vía CLI del proveedor para diagnosticar errores que no reproducen en local.
- **Frontend**: hosting de estáticos tipo Cloudflare Pages, sin SPA fallback — un archivo `_redirects` (o equivalente del proveedor) con una regla catch-all a una página 404 real.
- Dominio canónico centralizado: definir un único dominio "fuente de verdad" y usarlo consistentemente en CORS, valores por defecto de `FRONTEND_URL`, textos de emails transaccionales y contenido sembrado por el CMS — un mix accidental de variantes de dominio (ej. `.com` vs `.co`, o con/sin `www`) es un bug fácil de reintroducir si no se centraliza.

---

## 7. Qué NO incluye este documento (a propósito)

- Integraciones concretas de pasarela de pago / fulfillment (nombres de proveedores, formatos de payload, firmas/HMAC).
- Cualquier detalle de diseño visual: paletas de color, tipografías, CSS específico, layout de páginas.
- Contenido de negocio (textos, copy, nombres de producto, branding).

Estos quedan fuera deliberadamente: este archivo documenta el **esqueleto técnico reutilizable**, no el negocio concreto montado sobre él.

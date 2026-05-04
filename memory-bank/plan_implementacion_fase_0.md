# Plan de implementación detallado — Fase 0 (cimientos del proyecto)

Este documento desarrolla la **Fase 0** definida en [`planes_implementacion_fases.md`](./planes_implementacion_fases.md), tomando como contexto [`general_description.md`](./general_description.md) (stack Django + PostgreSQL + Admin + HTMX en fases posteriores + DigitalOcean).

**Índice de planes:** tabla *Planes detallados por fase* en el documento maestro.

---

## 1. Objetivo

Dejar un **proyecto Django reproducible** en la máquina de cualquier desarrollador y en un entorno de staging, con configuración base alineada al brief: idioma México, zona horaria, PostgreSQL por variables de entorno, admin usable y preparación para apps de dominio (Fase 1+).

---

## 2. Alcance y límites

### 2.1 Dentro de alcance

- Gestión de dependencias (`requirements.txt`) y variables documentadas (`.env.example`).
- `settings.py`: `BASE_DIR`, `DEBUG` / `SECRET_KEY` según entorno, `ALLOWED_HOSTS`, i18n (`LANGUAGE_CODE = es-MX`), `TIME_ZONE = America/Mexico_City`, `USE_I18N`, `USE_TZ`, `DEFAULT_AUTO_FIELD`, estáticos y media bajo `BASE_DIR`, `SECURE_PROXY_SSL_HEADER` para reverse proxy.
- Base de datos PostgreSQL: `ENGINE`, `DB_*`, `DISABLE_SERVER_SIDE_CURSORS` en `default`.
- Paquetes base del brief técnico: Django (rama estable acordada), DRF, CORS, `psycopg`, `python-dotenv`, `gunicorn`.
- Admin con **Unfold** y app mínima (`core` o equivalente) si hace falta extender admin de auth.
- Estructura de carpetas acordada (`memory-bank/`, futuras apps; opción `apps/` documentada en Fase 1).

### 2.2 Fuera de alcance (fases posteriores)

- Modelos de negocio (clientes, membresías, pagos, asistencias) → **Fase 1**.
- Lógica de check-in, HTMX, reportes → Fases 2–5.
- Infraestructura productiva completa (droplet, SSL, pipelines) → **Fases 6–7** (aquí solo preparación y documentación mínima).

---

## 3. Pasos de implementación (orden sugerido)

### 3.1 Repositorio y entorno Python

| Paso | Acción | Verificación |
|------|--------|--------------|
| 0.1 | Definir versión de Python soportada (coherente con Django y Unfold; p. ej. 3.11+). Documentarla en README o en este plan. | `python --version` |
| 0.2 | Crear entorno virtual (`.venv`) y flujo de activación en README. | `which python` apunta al venv |
| 0.3 | `pip install -r requirements.txt` | Sin errores de resolución |

### 3.2 Variables de entorno

| Paso | Acción | Verificación |
|------|--------|--------------|
| 0.4 | Mantener `.env.example` con `DB_*`, `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS` y comentarios breves. | Archivo versionado |
| 0.5 | `.env` en `.gitignore` (si aún no existe) para no commitear secretos. | `git status` no lista `.env` |
| 0.6 | Copia local `.env` desde ejemplo y valores de PostgreSQL de desarrollo. | Conexión en paso 0.9 |

### 3.3 Proyecto Django y settings

| Paso | Acción | Verificación |
|------|--------|--------------|
| 0.7 | Confirmar `INSTALLED_APPS` incluye terceros necesarios (DRF, CORS, Unfold, `core` si aplica). | `manage.py check` |
| 0.8 | Carga de `.env` con `python-dotenv` desde `BASE_DIR` (patrón try/import). | Cambiar `DEBUG` en `.env` y comprobar comportamiento |
| 0.9 | Crear rol/base PostgreSQL local o gestionada; ejecutar `migrate`. | Tablas `django_*` creadas |
| 0.10 | `createsuperuser` y acceso a `/admin/`. | Login OK, Unfold visible |

### 3.4 Calidad mínima y documentación

| Paso | Acción | Verificación |
|------|--------|--------------|
| 0.11 | README mínimo: clonar, venv, `cp .env.example`, `migrate`, `runserver`, URL admin. | Otro dev puede seguir pasos |
| 0.12 | (Opcional) `pre-commit`, formato con `ruff`/`black`, o CI que ejecute `check` + tests vacíos. | Pipeline verde |

---

## 4. Alineación con el brief

| Tema en `general_description.md` | Cómo lo cubre Fase 0 |
|----------------------------------|----------------------|
| §3 Stack Django + PostgreSQL | Settings + requirements |
| §3 Admin | Unfold instalado y accesible |
| §3 HTMX | No implementado aún; opcional añadir `django-htmx` o CDN documentado para Fase 4 |
| §12 Seguridad (base) | `SECRET_KEY` en prod, CSRF activo por defecto Django, staff para admin |

---

## 5. Lista de verificación de pruebas

- [ ] `python manage.py check` sin errores ni warnings críticos.
- [ ] `python manage.py migrate` en base PostgreSQL limpia.
- [ ] Servidor de desarrollo arranca; `/admin/` carga con estilos Unfold.
- [ ] Con `DEBUG=False` en entorno de prueba, falta de `SECRET_KEY` provoca error claro (`ImproperlyConfigured` o equivalente acordado).
- [ ] README o `.env.example` explica cómo ejecutar `migrate` y crear superusuario.

---

## 6. Criterios de salida

1. Cualquier miembro del equipo puede reproducir el entorno siguiendo la documentación.
2. PostgreSQL es la base por defecto vía variables `DB_*`.
3. Admin moderno operativo para usuarios staff.
4. No hay secretos en el repositorio; `.env` ignorado o no versionado.

---

## 7. Riesgos y notas

- **Unfold y versión de Python:** revisar requisitos de la versión pinneada de `django-unfold`.
- **CORS:** en Fase 0 basta con estar instalado; orígenes concretos pueden definirse cuando exista front o kiosko (Fase 4).
- **DigitalOcean:** solo nota; despliegue detallado en Fase 7.

---

## 8. Siguiente fase

**Fase 1:** modelos de dominio y migraciones según [`plan_implementacion_fase_1.md`](./plan_implementacion_fase_1.md).

# Runbook — despliegue App Platform (DigitalOcean + GitHub + GoDaddy)

Guía operativa para el go-live. El código ya incluye `.do/app.yaml`, health check en `/health/` y variables documentadas en `.env.example`.

**Antes de empezar:** reemplazar `midominio.com` por tu dominio real en `.do/app.yaml` (ALLOWED_HOSTS y CSRF_TRUSTED_ORIGINS) y volver a hacer push.

---

## 1. DigitalOcean — crear la app

1. [cloud.digitalocean.com](https://cloud.digitalocean.com) → **Apps → Create App → GitHub**
2. Autorizar cuenta `Brandon-Hernandez-T` y repo `albercas-semiolimpicas`, rama `main`
3. DO detectará `.do/app.yaml` — revisar región **sfo** (o **nyc**)
4. **Add Resource → Database → PostgreSQL 16** (plan Dev ~$15/mes)
5. **Environment Variables** → agregar `SECRET_KEY` (tipo Secret):

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

6. Incluir en `ALLOWED_HOSTS` la URL temporal `*.ondigitalocean.app` hasta tener dominio propio
7. **Create Resources** → esperar build (~5–8 min)
8. Anotar URL: `https://albercas-semiolimpicas-xxxxx.ondigitalocean.app`

### Variables de entorno (resumen)

| Variable | Valor producción |
|----------|------------------|
| `DEBUG` | `False` (Build + Run) |
| `SECRET_KEY` | Secret generado |
| `ALLOWED_HOSTS` | `tudominio.com,www.tudominio.com,<app>.ondigitalocean.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://tudominio.com,https://www.tudominio.com` |
| `DB_CONN_MAX_AGE` | `60` |
| `LOG_LEVEL` | `INFO` |
| `SECURE_HSTS_SECONDS` | `0` (subir a `31536000` tras 1–2 semanas) |

`DB_*` se inyectan al vincular PostgreSQL.

---

## 2. GoDaddy — DNS (apex + www)

1. App Platform → **Settings → Domains → Add Domain**
2. Agregar dominio raíz y `www`
3. En GoDaddy → **DNS** del dominio:

| Host | Tipo | Valor |
|------|------|-------|
| `www` | CNAME | URL `*.ondigitalocean.app` que indica DO |
| `@` | A | IP(s) que indica DO para apex |

4. TTL 600 s durante pruebas
5. Esperar propagación (15 min – 2 h)

### SSL (Let's Encrypt — automático)

- DO emite y renueva el certificado cuando DNS resuelve
- **No** comprar SSL en GoDaddy ni instalar Certbot
- Verificar: **Domains → Active** y candado en `https://tudominio.com/admin/`

---

## 3. Configuración inicial (consola DO)

App → componente **web** → **Console**:

```bash
python manage.py createsuperuser
python manage.py setup_staff_groups
```

Luego en `/admin/`:

1. Asignar usuarios staff a grupos **Recepción** o **Administración**
2. **Eliminar** cliente demo `DEMO001`
3. Revisar **Planes de membresía** (precios y días)
4. Importar socios: Admin → Clientes → **Importar CSV** o `python manage.py import_clients clientes.csv`

---

## 4. Smoke tests

| # | Prueba | Resultado esperado |
|---|--------|-------------------|
| 1 | `GET /health/` | `ok` |
| 2 | Login `/admin/` | Admin Unfold con estilos |
| 3 | `/quick-checkin/` | Formulario (requiere staff) |
| 4 | Check-in socio vigente | Mensaje verde |
| 5 | Check-in denegado | Mensaje rojo con motivo |
| 6 | `/staff/reports/` | Reportes cargan |
| 7 | HTTP → HTTPS | Redirección automática |
| 8 | POST login / check-in | Sin error CSRF |

---

## 5. Deploys futuros

Cada `git push` a `main` dispara: build → `migrate` (pre-deploy) → deploy.

**Rollback:** App → **Activity** → deploy anterior → **Rollback**

**Backups:** Databases → Backups (automático diario en plan Dev)

---

## 6. Entrega al cliente

1. URLs: `https://tudominio.com/admin/`, `/quick-checkin/`
2. Credenciales admin (canal seguro)
3. [`manual_operacion_staff.md`](./manual_operacion_staff.md)
4. Contacto soporte primeras 48–72 h

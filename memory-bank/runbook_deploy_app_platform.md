# Runbook — despliegue App Platform (DigitalOcean + GitHub + GoDaddy)

Guía operativa para el go-live. Dominio de producción: **albercas-ixtapaluca.xyz**.

El código ya incluye `.do/app.yaml`, health check en `/health/` y variables documentadas en `.env.example`.

---

## 1. DigitalOcean — crear la app

1. [cloud.digitalocean.com](https://cloud.digitalocean.com) → **Apps → Create App → GitHub**
2. Autorizar cuenta `Brandon-Hernandez-T` y repo `albercas-semiolimpicas`, rama `master`
3. DO detectará `.do/app.yaml` — revisar región **sfo** (o **nyc**)
4. **Add Resource → Database → PostgreSQL 16** (plan Dev ~$15/mes)
5. **Environment Variables** → agregar `SECRET_KEY` (tipo Secret):

   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

6. En el primer deploy, agregar en `ALLOWED_HOSTS` la URL temporal `*.ondigitalocean.app` (además del dominio ya configurado en `app.yaml`)
7. **Create Resources** → esperar build (~5–8 min)
8. Anotar URL: `https://albercas-semiolimpicas-xxxxx.ondigitalocean.app`

### Variables de entorno (resumen)

| Variable | Valor producción |
|----------|------------------|
| `DEBUG` | `False` (Build + Run) |
| `SECRET_KEY` | Secret generado |
| `ALLOWED_HOSTS` | `albercas-ixtapaluca.xyz,www.albercas-ixtapaluca.xyz,<app>.ondigitalocean.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://albercas-ixtapaluca.xyz,https://www.albercas-ixtapaluca.xyz` |
| `DB_CONN_MAX_AGE` | `60` |
| `LOG_LEVEL` | `INFO` |
| `SECURE_HSTS_SECONDS` | `0` (subir a `31536000` tras 1–2 semanas) |

`DB_*` se inyectan al vincular PostgreSQL.

---

## 2. GoDaddy — DNS (apex + www)

Dominio: **albercas-ixtapaluca.xyz**

1. App Platform → **Settings → Domains → Add Domain**
2. Agregar `albercas-ixtapaluca.xyz` y `www.albercas-ixtapaluca.xyz`
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
- Verificar: **Domains → Active** y candado en `https://albercas-ixtapaluca.xyz/admin/`

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

Cada `git push` a `master` dispara: build → `migrate` (pre-deploy) → deploy.

**Rollback:** App → **Activity** → deploy anterior → **Rollback**

**Backups:** Databases → Backups (automático diario en plan Dev)

---

## 6. Entrega al cliente

1. URLs: `https://albercas-ixtapaluca.xyz/admin/`, `https://albercas-ixtapaluca.xyz/quick-checkin/`
2. Credenciales admin (canal seguro)
3. [`manual_operacion_staff.md`](./manual_operacion_staff.md)
4. Contacto soporte primeras 48–72 h

# Listo para producción — Fase 6

Checklist y referencias para despliegue en **DigitalOcean** (o entorno equivalente con PostgreSQL, Gunicorn y reverse proxy HTTPS).

**Prerrequisito funcional:** Fases 0–5 completadas. **Siguiente:** [plan_implementacion_fase_7.md](./plan_implementacion_fase_7.md) (UAT y go-live).

---

## 1. Objetivos de rendimiento

| Flujo | Meta orientativa (servidor, sin red) |
|-------|--------------------------------------|
| POST `/quick-checkin/` (capa servicio) | **p95 &lt; 300 ms** |
| Percepción en recepción (brief) | **&lt; 1–2 s** por cliente incluyendo red |

### Medición local

```bash
python manage.py benchmark_checkin --access-number DEMO001 --iterations 50
python manage.py benchmark_checkin --access-number DEMO001 --evaluate-only
python manage.py explain_checkin_queries --access-number DEMO001
```

Archivar salida de `EXPLAIN ANALYZE` en staging antes del go-live.

---

## 2. Índices de base de datos (Fase 6)

| Tabla / área | Índice |
|--------------|--------|
| `clients_client.access_number` | UNIQUE + índice (Fase 1) |
| `attendances_attendance` | UNIQUE `(client_id, attendance_date)` + `attendances_date_idx` |
| `payments_payment` | `payments_client_paydate_desc`, `payments_client_expiration`, `payments_expiration_date_idx` |

Aplicar migraciones:

```bash
python manage.py migrate
```

---

## 3. Variables de entorno (producción)

Ver [`.env.example`](../.env.example). Mínimo:

| Variable | Valor en producción |
|----------|---------------------|
| `DEBUG` | `False` |
| `SECRET_KEY` | Cadena larga aleatoria (obligatoria si `DEBUG=False`) |
| `ALLOWED_HOSTS` | Dominio(s) reales separados por coma |
| `DB_*` | PostgreSQL gestionado o droplet |
| `DB_CONN_MAX_AGE` | `60` (ajustar con pooler si aplica) |
| `SECURE_SSL_REDIRECT` | `True` detrás de HTTPS |
| `SECURE_HSTS_SECONDS` | `0` al inicio; subir a `31536000` cuando HTTPS sea estable |
| `LOG_LEVEL` | `INFO` o `WARNING` |

---

## 4. Seguridad Django (activo con `DEBUG=False`)

Configurado en `albercas_semiolimpicas/settings.py`:

- `SECURE_SSL_REDIRECT`, cookies `Secure` + `HttpOnly`
- `SECURE_PROXY_SSL_HEADER` para nginx/DO load balancer
- `SECURE_REFERRER_POLICY`, `SECURE_CONTENT_TYPE_NOSNIFF`
- HSTS opcional vía `SECURE_HSTS_SECONDS`
- CSRF y staff sin relajar (check-in y reportes requieren `is_staff`)

**No** instalar `django-debug-toolbar` en producción.

---

## 5. Despliegue de aplicación

### Estáticos

```bash
python manage.py collectstatic --noinput
```

Con `DEBUG=False`, **WhiteNoise** sirve estáticos (`CompressedStaticFilesStorage`).

### Gunicorn

```bash
gunicorn albercas_semiolimpicas.wsgi:application -c gunicorn.conf.py
```

Variables opcionales: `GUNICORN_WORKERS`, `GUNICORN_BIND`, `GUNICORN_TIMEOUT`.

### Reverse proxy

- Terminar TLS en nginx / load balancer.
- Enviar `X-Forwarded-Proto: https`.
- Timeouts ≥ 30 s.

---

## 6. Observabilidad post-deploy (enlace Fase 7)

- Revisar logs de Gunicorn y nginx (errores 5xx).
- Alertar si la tasa de 5xx sube o el check-in deja de responder.
- Backup automático de PostgreSQL antes del go-live.

---

## 7. Checklist de cierre Fase 6

- [ ] Migraciones de índices aplicadas en staging/producción.
- [ ] `explain_checkin_queries` revisado; sin sequential scan inesperado en tablas grandes.
- [ ] `benchmark_checkin` dentro de meta o documentada desviación aceptada.
- [ ] `.env` producción sin `DEBUG=True`.
- [ ] `collectstatic` ejecutado.
- [ ] Gunicorn + proxy probados con HTTPS.
- [ ] Sin secretos en el repositorio.

---

## 8. Fuera de alcance (sin cache de negocio)

No se añadió cache de decisiones de check-in: el plan Fase 6 solo la recomienda tras medición que demuestre cuello de botella. Reevaluar en Fase 7 si el tráfico real lo exige.

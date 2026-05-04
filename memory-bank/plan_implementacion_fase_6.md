# Plan de implementación detallado — Fase 6 (rendimiento, seguridad y endurecimiento)

Este documento desarrolla la **Fase 6** definida en [`planes_implementacion_fases.md`](./planes_implementacion_fases.md), alineado con [`general_description.md`](./general_description.md) §11 (performance), §12 (seguridad), §3 (deploy DigitalOcean a alto nivel) y el contexto de **4 albercas** y alto volumen en pico (§1).

**Prerrequisitos:** **Fase 4** implementada (endpoint de check-in); **Fase 3–5** para tener queries reales que medir.

**Índice de planes:** tabla *Planes detallados por fase* en el documento maestro.

---

## 1. Objetivo

Asegurar que el sistema **aguante el uso previsto** (especialmente búsqueda por `access_number` e inserción/consulta de asistencias por día), que la configuración de **producción** sea segura, y dejar **documentación** de “listo para producción” con umbrales medidos o acordados.

---

## 2. Base de datos y consultas

### 2.1 Índices (brief §11)

| Área | Acción |
|------|--------|
| Cliente | Confirmar unicidad/`INDEX` en `access_number` (Fase 1). |
| Asistencia | `UniqueConstraint` (cliente, fecha) ya optimiza “¿ya vino hoy?”; revisar si hace falta índice adicional por `attendance_date` solo para reportes (Fase 5). |
| Pagos | Índice compuesto `(client_id, payment_date)` o `(client_id, expiration_date)` si las consultas Fase 2/5 lo justifican. |

### 2.2 Análisis de queries

| Paso | Acción |
|------|--------|
| 6.1 | Activar logging de queries lentas en staging o usar `EXPLAIN ANALYZE` en PostgreSQL sobre la query principal del check-in. |
| 6.2 | Eliminar **N+1** en changelists de admin (`list_select_related`, `prefetch_related`). |
| 6.3 | Documentar tiempo objetivo (p. ej. p95 &lt; 300 ms servidor para POST check-in sin contar red). |

### 2.3 Cache (brief §11: opcional)

- Introducir cache **solo** si hay medición previa que demuestre cuello de botella.
- Si se usa: claves con TTL corto, invalidación clara; evitar cachear decisiones de negocio sin invalidar al registrar pago/asistencia.

---

## 3. Seguridad (brief §12 + hardening Django)

### 3.1 Configuración producción

| Elemento | Acción |
|----------|--------|
| `DEBUG` | `False`; verificar que errores no filtran settings. |
| `SECRET_KEY` | Obligatoria y rotación documentada. |
| `ALLOWED_HOSTS` | Dominios reales del sitio y del load balancer si aplica. |
| HTTPS | `SECURE_SSL_REDIRECT`, cookies `Secure`, `SESSION_COOKIE_SECURE` cuando todo el sitio sea HTTPS. |
| HSTS | Valor conservador al inicio; subdominios solo si se entiende el alcance. |
| `SECURE_PROXY_SSL_HEADER` | Ya previsto en Fase 0; confirmar que el proxy envía el header correcto. |
| CSRF / staff | Sin cambios que debiliten; revisar orígenes confiables si hay subdominios API. |

### 3.2 Aplicación

- Headers de seguridad razonables (`SecurityMiddleware` ya activo; valorar `SECURE_REFERRER_POLICY`, etc., según guías Django deployment).
- Logs sin datos sensibles completos (PCI no aplica a pagos manuales, pero minimizar PII en trazas).

---

## 4. Carga y capacidad

| Paso | Acción |
|------|--------|
| 6.4 | Script o **Locust** / `hey` contra `/quick-checkin/` con tokens CSRF resueltos (o prueba interna del servicio si el CSRF complica el load test). |
| 6.5 | Definir número concurrente objetivo (estimación pico recepción) y documentar resultado. |
| 6.6 | Ajustar workers Gunicorn, timeouts y conexiones a PostgreSQL (`CONN_MAX_AGE`, pooler si DO lo recomienda). |

---

## 5. Estáticos y archivos (DigitalOcean / §3)

| Paso | Acción |
|------|--------|
| 6.7 | `collectstatic` en build o en servidor; WhiteNoise opcional si sirve estáticos desde Django. |
| 6.8 | Media (fotos futuras): volumen o S3 fuera de alcance del brief; si solo disco local, documentar backup. |

---

## 6. Lista de verificación de cierre

- [ ] Índices creados y migraciones aplicadas en staging.
- [ ] `EXPLAIN` o equivalente archivado o resumido en doc interna.
- [ ] Checklist de settings producción completada (ver §3.1).
- [ ] Prueba de carga documentada con resultado (aunque sea “hasta X RPS sin errores”).
- [ ] Sin `django-debug-toolbar` ni `DEBUG` en producción.

---

## 7. Criterios de salida

1. Documento breve **“Listo para producción”** (markdown en repo o wiki) con métricas y checklist §6.
2. Equipo sabe cómo observar latencia y errores post-deploy (enlace a Fase 7).

---

## 8. Siguiente fase

**Fase 7:** UAT formal, despliegue y monitoreo inicial.

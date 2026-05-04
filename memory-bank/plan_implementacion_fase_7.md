# Plan de implementación detallado — Fase 7 (QA integrado y despliegue)

Este documento desarrolla la **Fase 7** definida en [`planes_implementacion_fases.md`](./planes_implementacion_fases.md), alineado con [`general_description.md`](./general_description.md) §9 (cronograma semanas 7–8), §10 (testing), §3 (DigitalOcean), §12 (seguridad) y §13 (alcance).

**Prerrequisitos:** **Fase 6** cerrada o en paralelo final; producto funcional en **staging** (Fases 1–5 mínimo).

**Índice de planes:** tabla *Planes detallados por fase* en el documento maestro.

---

## 1. Objetivo

Validar el sistema **de extremo a extremo** con criterios aceptados por el cliente, desplegar a **producción** en DigitalOcean (o stack acordado) con **rollback** y **monitoreo** básico, y cerrar el ciclo con lecciones aprendidas.

---

## 2. Alcance

### 2.1 Dentro de alcance

- Matriz de pruebas manuales y/o automatizadas de regresión.
- Corrección de bugs **P0** (bloqueantes) y **P1** (críticos operativos) antes del go-live.
- Procedimiento de deploy: código, migraciones, `collectstatic`, variables de entorno, proceso de backup/restore de BD.
- Plan de rollback (versión anterior de app + compatibilidad de migraciones).
- Smoke tests inmediatamente después del deploy.
- Canal de soporte post-lanzamiento (quién atiende incidencias las primeras 48–72 h).

### 2.2 Fuera de alcance

- Nuevas funcionalidades mayores no acordadas en UAT (van a backlog post-release).

---

## 3. QA integrado

### 3.1 Matriz de pruebas (mínimo sugerido)

| Área | Casos |
|------|--------|
| Admin (Fase 3) | CRUD cliente, pago, plan; permisos por rol; asistencia manual vs reglas. |
| Ingreso rápido (Fase 4) | Los 5 escenarios del brief §10; CSRF; no staff bloqueado; foco y Enter. |
| Reportes (Fase 5) | Totales coincidentes con datos semilla en staging. |
| Regresión | Migraciones desde base vacía a última versión en entorno limpio. |

### 3.2 Navegadores y dispositivos

- Definir lista corta (p. ej. Chrome último, Safari iOS si recepción usa tablet).
- Probar en red similar a producción (latencia moderada).

### 3.3 UAT con el cliente

| Paso | Acción |
|------|--------|
| 7.1 | Sesión guiada con checklist firmado o correo de “aceptación”. |
| 7.2 | Registrar hallazgos: must-fix vs siguiente iteración. |

---

## 4. Despliegue (DigitalOcean / producción)

### 4.1 Pre-deploy

| Paso | Acción |
|------|--------|
| 7.3 | Backup completo de PostgreSQL de producción (si ya hay datos) o plan de BD vacía inicial. |
| 7.4 | Variables de entorno revisadas contra `.env.example` (sin valores secretos en repo). |
| 7.5 | `migrate` en staging idéntico al commit que irá a prod. |
| 7.6 | Ventana de mantenimiento acordada si hay downtime. |

### 4.2 Deploy

| Paso | Acción |
|------|--------|
| 7.7 | Desplegar artefacto (git pull, contenedor, etc.). |
| 7.8 | Ejecutar migraciones. |
| 7.9 | `collectstatic` si aplica. |
| 7.10 | Reiniciar Gunicorn/uWSGI y workers según runbook. |

### 4.3 Post-deploy

| Paso | Acción |
|------|--------|
| 7.11 | Smoke: login admin, un check-in de prueba con usuario ficticio o bandera `MAINTENANCE`. |
| 7.12 | Revisar logs de aplicación y proxy (4xx/5xx). |
| 7.13 | Monitorización mínima: alerta por tasa de 5xx o caída del healthcheck. |

### 4.4 Rollback

- Tener comando o tag git de versión anterior.
- Si migraciones no son reversibles, plan B: hotfix forward-only documentado.

---

## 5. Documentación de entrega

- Runbook de deploy (1–2 páginas).
- Contactos de escalamiento.
- Enlace o copia del checklist de Fase 6 “listo para producción”.

---

## 6. Criterios de salida

1. UAT aceptado por el cliente o registro explícito de excepciones firmadas.
2. Producción estable en la ventana acordada post-deploy.
3. Backups automáticos o manuales de BD configurados y verificados al menos una vez.
4. Equipo conoce cómo aplicar hotfix y rollback.

---

## 7. Post-proyecto (mejora continua)

- Reunión retrospectiva: qué ajustar en Fases 1–6 para el siguiente release.
- Backlog: reposiciones, multi-sede, mejoras de reportes (según brief y negocio).

---

## 8. Referencia de fases anteriores

| Fase | Documento |
|------|-----------|
| 0–6 | [`plan_implementacion_fase_0.md`](./plan_implementacion_fase_0.md) … [`plan_implementacion_fase_6.md`](./plan_implementacion_fase_6.md) |

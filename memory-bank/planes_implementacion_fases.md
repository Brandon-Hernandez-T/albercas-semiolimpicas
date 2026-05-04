# Plan de implementación por fases

Este documento desglosa el desarrollo y las pruebas del sistema descrito en [`general_description.md`](./general_description.md). Cada fase tiene **objetivos**, **entregables**, **pruebas sugeridas** y **criterios de salida** para poder cerrar la fase antes de avanzar.

**Referencia de arquitectura de apps:** `clients`, `memberships`, `payments`, `attendances`, `checkin` (o equivalente bajo un prefijo común; lo importante es la separación por dominio).

**Stack de referencia:** Django, PostgreSQL, Admin (Unfold), Ingreso rápido con Django Templates + HTMX, despliegue en DigitalOcean.

### Planes detallados por fase

Cada fase tiene un plan de implementación ampliado en `memory-bank/` (objetivos, pasos, pruebas, criterios de salida), alineado con [`general_description.md`](./general_description.md).

| Fase | Documento |
|------|-----------|
| 0 — Cimientos | [`plan_implementacion_fase_0.md`](./plan_implementacion_fase_0.md) |
| 1 — Modelos y datos | [`plan_implementacion_fase_1.md`](./plan_implementacion_fase_1.md) |
| 2 — Reglas de negocio | [`plan_implementacion_fase_2.md`](./plan_implementacion_fase_2.md) |
| 3 — Backoffice | [`plan_implementacion_fase_3.md`](./plan_implementacion_fase_3.md) |
| 4 — Ingreso rápido | [`plan_implementacion_fase_4.md`](./plan_implementacion_fase_4.md) |
| 5 — Reportes | [`plan_implementacion_fase_5.md`](./plan_implementacion_fase_5.md) |
| 6 — Rendimiento y seguridad | [`plan_implementacion_fase_6.md`](./plan_implementacion_fase_6.md) |
| 7 — QA y despliegue | [`plan_implementacion_fase_7.md`](./plan_implementacion_fase_7.md) |

---

## Fase 0 — Cimientos del proyecto

**Objetivo:** Entorno reproducible, configuración base y convenciones listas para el dominio.

**Entregables:**

- Dependencias y variables de entorno documentadas (`.env.example`, `requirements.txt`).
- `settings.py` con PostgreSQL, i18n `es-MX`, zona `America/Mexico_City`, estáticos/media y seguridad básica detrás de proxy.
- Admin moderno (Unfold) operativo; app mínima para extender admin si aplica.
- Estructura de repositorio acordada (carpetas de apps, `memory-bank/` actualizado cuando cambie el alcance).

**Pruebas:**

- `python manage.py check` sin errores.
- `migrate` contra una base local o de staging.
- Acceso a `/admin/` con usuario staff.

**Criterios de salida:** Cualquier desarrollador puede levantar el proyecto con README o `.env.example` y ejecutar el servidor.

---

## Fase 1 — Modelos y datos (dominio)

**Objetivo:** Persistencia alineada con el brief: clientes, tipos de membresía, pagos y asistencias, con integridad referencial clara.

**Entregables (orientativo, a ajustar al modelo final):**

| App / dominio   | Contenido mínimo |
|-----------------|------------------|
| **clients**     | Cliente: nombre, `access_number` único, enlace a membresía vigente o tipo de paquete, flag `active`, timestamps. |
| **memberships** | Definición de paquetes (p. ej. 3 tipos): nombre, días permitidos (`JSON` o relación M2M a un catálogo de día), `duration_days`, metadatos de estado si aplica a nivel de “tipo”. |
| **payments**      | Pago: cliente, monto, `payment_date`, `expiration_date`, estado (activo / vencido o derivado por fecha). |
| **attendances**   | Asistencia: cliente, fecha (o datetime en zona del proyecto), estado o tipo de registro. |

- Migraciones versionadas y reversibles cuando sea posible.
- Índices previstos en Fase 7 como parte del diseño: al menos documentar `access_number` y búsquedas por `(cliente, fecha)` para asistencias.

**Pruebas:**

- Migraciones en base limpia y en base con datos de ejemplo.
- Constraints: unicidad de `access_number`; FKs coherentes.
- Datos de *factory* o fixtures mínimas para desarrollo (opcional pero recomendable).

**Criterios de salida:** Los cuatro dominios existen en el ORM, sin lógica de negocio compleja aún en vistas; admin puede mostrar modelos en bruto o con listas básicas.

---

## Fase 2 — Reglas de negocio (servicio / capa de dominio)

**Objetivo:** Centralizar validaciones que usarán admin, API futura e ingreso rápido; el backend es la fuente de verdad.

**Reglas (de [`general_description.md`](./general_description.md)):**

- Máximo **una asistencia por cliente y día** (calendario según `TIME_ZONE`).
- Membresía **activa** (según pago / vigencia definida en el proyecto).
- Asistencia solo en **días permitidos** por el tipo de membresía del cliente.
- Vigencia ligada a pagos; flag o regla para **reposiciones** (alcance mínimo o “fase 2 bis” si se pospone).

**Entregables:**

- Módulo(s) de servicio, p. ej. `services/membership.py`, `services/attendance.py`, o métodos de modelo **delgados** que deleguen en funciones testeables.
- Excepciones o resultados tipados (p. ej. `ResultadoIngreso` con permitido/denegado y **motivo** para mostrar en UI).
- Validadores reutilizables para “¿puede ingresar hoy?” y “¿ya asistió hoy?”.

**Pruebas (unitarias imprescindibles):**

- Cliente sin membresía → denegado.
- Membresía vencida → denegado.
- Segundo ingreso el mismo día → denegado.
- Día no permitido → denegado.
- Caso válido → permitido.

**Criterios de salida:** La lógica vive fuera de las vistas HTTP; tests cubren los cinco escenarios anteriores más casos límite (cambio de día en medianoche con `USE_TZ`, etc.).

---

## Fase 3 — Backoffice (Django Admin + Unfold)

**Objetivo:** Operación diaria de staff sin tocar código: CRUD clientes, membresías, pagos, consulta de asistencias.

**Entregables:**

- `ModelAdmin` con Unfold (`ModelAdmin` de unfold) por modelo relevante.
- Listas filtrables: por estado de pago, fechas, `active`, etc.
- Acciones o inlines razonables (p. ej. pagos del cliente en ficha de cliente).
- Permisos por grupo si el cliente lo requiere (mínimo: solo staff accede).

**Pruebas:**

- Flujos manuales en admin: crear cliente, asignar tipo de membresía, registrar pago, ver vigencia.
- Comprobar que las reglas de Fase 2 se respetan al crear asistencias desde admin (si aplica) o vía servicio compartido.

**Criterios de salida:** Un usuario staff puede mantener el catálogo y los datos sin inconsistencias obvias; documentación breve de “cómo damos de alta un cliente”.

---

## Fase 4 — Ingreso rápido (crítico)

**Objetivo:** Pantalla `/quick-checkin/` (o la ruta acordada) con **menos de ~2 s** percibidos por operador; foco en teclado y feedback inmediato.

**Entregables:**

- Vista + plantilla: input con **autofocus**, envío con **Enter**, `hx-post` hacia endpoint dedicado.
- Respuesta parcial HTMX: fragmento HTML con estado **verde** (OK) o **rojo** (error + **motivo** legible).
- Uso obligatorio de la capa de negocio de Fase 2 (sin duplicar reglas en la vista).
- Login requerido para staff; CSRF en formularios Django.

**Pruebas:**

- Pruebas de integración ligeras del endpoint (cliente + DB o mocks de servicio según estrategia del equipo).
- Prueba manual en red local: latencia percibida; repetir en horario de carga simulada si es posible.

**Criterios de salida:** Los cinco casos de prueba de la sección 10 del brief se reproducen desde la pantalla; operador puede corregir número y reintentar sin recargar página completa.

---

## Fase 5 — Reportes y operación

**Objetivo:** Visibilidad mínima para administración (sin BI avanzado; fuera de alcance según brief).

**Entregables:**

- Reportes básicos acordados con el cliente, p. ej.: asistencias por día / por alberca (si el modelo distingue sede), ingresos por periodo, clientes con membresía por vencer.
- Implementación preferible vía admin (listas + filtros), vistas staff protegidas, o export CSV simple.

**Pruebas:**

- Datos conocidos en fixtures → totales esperados en reportes.
- Comprobar uso de zona horaria en rangos de fechas.

**Criterios de salida:** El cliente puede auditar operación diaria sin SQL ad hoc.

---

## Fase 6 — Rendimiento, seguridad y endurecimiento

**Objetivo:** Cumplir la sección de performance y seguridad del brief antes de producción.

**Entregables:**

- Índices en BD: `access_number`; consultas por fecha de asistencia; revisión `EXPLAIN` en consultas del check-in.
- Evitar N+1 en listas admin y en el endpoint de ingreso rápido.
- Cache opcional solo si hay medición que lo justifique.
- Revisión: `DEBUG=False`, `SECRET_KEY`, hosts permitidos, HTTPS detrás de proxy (`SECURE_*` según despliegue).

**Pruebas:**

- Carga mínima (p. ej. locust o script) sobre `/quick-checkin/` con metas acordadas.
- Checklist de despliegue DigitalOcean (estáticos, `collectstatic`, variables de entorno).

**Criterios de salida:** Documento corto de “listo para producción” con métricas o umbrales aceptados.

---

## Fase 7 — QA integrado y despliegue

**Objetivo:** Validación end-to-end y salida a producción controlada.

**Entregables:**

- Matriz de pruebas manuales (admin + ingreso rápido + reportes).
- Corrección de bugs prioritarios (P0/P1).
- Pipeline o procedimiento de deploy (gunicorn, reverse proxy, BD gestionada).

**Pruebas:**

- Regresión de las reglas de negocio y de HTMX en navegadores objetivo.
- Rollback plan y backup de BD antes del go-live.

**Criterios de salida:** Cliente firma UAT o equivalente; monitoreo básico post-deploy (logs, errores 5xx).

---

## Orden sugerido y paralelización

| Fase | Dependencia principal      | Notas |
|------|----------------------------|--------|
| 0    | —                          | Ya parcialmente cubierta. |
| 1    | 0                          | Base para todo lo demás. |
| 2    | 1                          | No posponer: alimenta Fase 4. |
| 3    | 1, 2                       | Admin puede empezar con CRUD y endurecerse tras Fase 2. |
| 4    | 2 (obligatorio), 3 (útil) | Prioridad de negocio; UX en paralelo con pulido de admin. |
| 5    | 3, 4                       | Cuando haya datos reales o de staging. |
| 6    | 4                          | Optimizar con tráfico realista. |
| 7    | 5, 6                       | Cierre. |

---

## Relación con el cronograma de 8 semanas (referencia)

El brief propone un reparto semanal; este plan por **fases** no fuerza duración fija por fase. Equipo puede mapear, por ejemplo:

- Semanas 1–2 → Fase 0–1 y refinamiento de reglas (Fase 2 en diseño).
- Semana 3 → Fase 2 completa.
- Semana 4 → Fase 3.
- Semana 5 → Fase 4.
- Semana 6 → Fase 5.
- Semanas 7–8 → Fases 6–7.

Ajustar según capacidad del equipo y feedback del cliente tras el primer despliegue a staging.

---

## Mantenimiento de este documento

Al cerrar una fase, actualizar el archivo de seguimiento del equipo (por ejemplo `memory-bank/progress.md` si lo incorporan) con la fase actual y las pruebas ya verdes. Si el alcance cambia (p. ej. reposiciones, multi-sede), añadir una sub-fase o anexo aquí y en `general_description.md`.

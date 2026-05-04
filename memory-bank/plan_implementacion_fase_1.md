# Plan de implementación detallado — Fase 1 (modelos y datos)

Este documento desarrolla la **Fase 1** definida en [`planes_implementacion_fases.md`](./planes_implementacion_fases.md), tomando como fuente de negocio y alcance [`general_description.md`](./general_description.md). Índice de planes detallados: tabla **Planes detallados por fase** en el documento maestro.

| Referencia | Rol |
|------------|-----|
| Fase 1 (plan maestro) | Persistencia de clientes, membresías (paquetes), pagos y asistencias; migraciones; constraints; datos de ejemplo. |
| Brief §4–7, §11 | Módulos, modelos simplificados, performance (índices). |
| Fases 2+ (fuera de este plan) | Reglas “¿puede ingresar hoy?”, servicios, HTMX, reportes avanzados. En Fase 1 **solo** se deja el esquema listo para esas reglas (campos y restricciones donde aplique). |

---

## 1. Objetivo y límites de la Fase 1

### 1.1 Objetivo

Tener en PostgreSQL, vía Django ORM:

1. Catálogo de **tipos de membresía / paquetes** (tres configuraciones de negocio: días permitidos, duración en días, nombre).
2. **Clientes** con número de acceso único, enlace al tipo de paquete, estado activo/inactivo y metadatos mínimos para CRUD e historial futuro.
3. **Pagos** asociados al cliente con montos y fechas que definirán vigencia (Fase 2 decidirá cómo “activar” desde aquí).
4. **Asistencias** asociadas al cliente con fecha y estado, con restricción de unicidad **a nivel de base de datos** para “un registro por cliente y día” (alineado a la regla de negocio del brief).

### 1.2 Qué queda explícitamente fuera de Fase 1

- Lógica de “membresía activa” calculada en tiempo de check-in (servicio dedicado → Fase 2).
- Pantalla `/quick-checkin/` y HTMX (Fase 4).
- Reportes y agregaciones de negocio (Fase 5).
- Reposiciones: el brief las menciona como fase futura o flag simple; si se incluye un campo booleano opcional en `Payment` o `Client`, documentarlo como **opcional** y no bloqueante para cerrar Fase 1.
- Multi-sede (4 albercas): el brief habla del contexto operativo; si no hay campo `venue`/`pool` en Fase 1, dejar **nota de extensión** en sección 10.

---

## 2. Estructura de apps Django

### 2.1 Convención de carpetas

Alinear con la arquitectura sugerida en el brief (`apps/...`). Dos opciones válidas; elegir **una** y mantenerla en todo el repo:

| Opción | Ruta ejemplo | Notas |
|--------|----------------|-------|
| A (recomendada) | `apps/clients/`, `apps/memberships/`, … | Requiere paquete Python `apps` (`apps/__init__.py`) y posible ajuste de `PYTHONPATH` o uso de namespace claro en `INSTALLED_APPS`. |
| B | `clients/`, `memberships/` en la raíz del repo | Más simple; equivalente funcional a “apps” siempre que `INSTALLED_APPS` liste nombres correctos. |

El plan asume **nombres de app** `memberships`, `clients`, `payments`, `attendances` (sin prefijo o con prefijo `apps.` según la opción elegida).

### 2.2 Orden de dependencias entre apps

Para evitar importaciones circulares y migraciones conflictivas:

```text
memberships  →  sin FK a clients/payments/attendances
clients      →  FK a memberships (tipo de paquete del cliente)
payments     →  FK a clients
attendances  →  FK a clients
```

**Orden sugerido en `INSTALLED_APPS`:** `memberships`, `clients`, `payments`, `attendances` (después de `django.contrib` y terceros, antes de `core` si `core` solo toca auth).

### 2.3 Orden de implementación en el código (pasos 1.1–1.5)

| Paso | App | Acción |
|------|-----|--------|
| 1.1 | `memberships` | Crear app; modelo(s) de catálogo; migración inicial. |
| 1.2 | `clients` | Modelo `Client`; FK a membresía; migración inicial. |
| 1.3 | `payments` | Modelo `Payment`; FK a `Client`; migración inicial. |
| 1.4 | `attendances` | Modelo `Attendance`; FK a `Client`; restricción única; migración inicial. |
| 1.5 | Transversal | Índices explícitos si no cubiertos por `unique`; `verbose_name` en español; datos semilla de los 3 paquetes; registro admin mínimo (opcional pero útil para validar). |

---

## 3. Diseño de modelos (detalle de campos)

Convenciones transversales:

- `BigAutoField` como PK (ya definido en `DEFAULT_AUTO_FIELD` del proyecto).
- `created_at` / `updated_at` en modelos de negocio que vivan CRUD frecuente (`Client`, `Payment`, opcionalmente `Attendance`) para auditoría ligera.
- Textos visibles: `verbose_name` y `help_text` en **español** (`es-MX`).
- Fechas de negocio (`payment_date`, `expiration_date`, día de asistencia): acordar **solo `DateField`** vs **`DateTimeField`** en zona `America/Mexico_City`. Recomendación para asistencia “1 por día”: **`DateField` `attendance_date`** interpretado como **día civil local** del sitio, coherente con el brief; Fase 2 implementa comparaciones con “hoy” en esa zona.

### 3.1 App `memberships` — catálogo de paquetes (3 tipos)

**Nombre de modelo sugerido:** `MembershipPlan` (o `MembershipType`) para no confundir con “instancia de suscripción”. Si se prefiere el nombre corto `Membership` del brief, documentar en código que es **plan**, no membresía vigente por cliente.

| Campo | Tipo sugerido | Null | Notas |
|-------|----------------|------|--------|
| `id` | PK | — | Autogenerado. |
| `name` | `CharField` | no | Nombre del paquete (ej. “Semanal AM”, “Mensual completo”). `max_length` razonable (64–128). |
| `slug` | `SlugField` | no, `unique` | Opcional pero útil para seeds y URLs futuras; único. |
| `allowed_days` | `JSONField` | no, default `[]` | Lista de enteros de día de semana. **Documentar convención** en el modelo (ej. `0=Lunes … 6=Domingo` ISO-like, o `1–7`; lo importante es **una sola convención** usada después en Fase 2). |
| `duration_days` | `PositiveSmallIntegerField` | no | Duración asociada al paquete (según brief); validar `> 0` en `clean()` o constraint `CheckConstraint`. |
| `is_active` | `BooleanField`, default `True` | no | Permite desactivar un paquete en catálogo sin borrar historial. |
| `description` | `TextField`, blank | sí | Opcional; ayuda en admin. |
| `created_at` / `updated_at` | `DateTimeField`, `auto_now_add` / `auto_now` | — | Recomendado. |

**Alternativa a JSON para `allowed_days`:** modelo `Weekday` + `ManyToManyField` desde `MembershipPlan`. Más normalizado; más migraciones y fixtures. Para Fase 1, **JSON + convención documentada** suele ser suficiente y coincide con el brief (“JSON o ManyToMany”).

**Datos semilla (obligatorio para probar):** exactamente **tres** filas iniciales alineadas al negocio (nombres y `allowed_days`/`duration_days` a validar con el cliente). Implementación posible: migración de datos (`RunPython`), comando `loaddata`, o `post_migrate` signal; preferir **migración de datos versionada** o fixture `memberships/fixtures/initial_plans.json` con documentación en README.

### 3.2 App `clients`

| Campo | Tipo sugerido | Null | Notas |
|-------|----------------|------|--------|
| `id` | PK | — | |
| `name` | `CharField` | no | Nombre completo o razón social según operación. |
| `access_number` | `CharField`, **`unique=True`** | no | Número único de acceso (brief); índice implícito por unicidad. Normalizar en Fase 2 (espacios, ceros a la izquierda); en Fase 1 basta `unique` y `max_length` acorde al formato real (ej. 16–32). |
| `membership_plan` | `ForeignKey(MembershipPlan, …)` | no | Relación “cliente ↔ tipo de paquete” del brief (`membership` FK). `on_delete`: típicamente `PROTECT` para no borrar planes con clientes asignados. |
| `active` | `BooleanField`, default `True` | no | Cliente dado de baja lógica. |
| `notes` | `TextField`, blank | — | Opcional recepción. |
| `created_at` / `updated_at` | `DateTimeField` | — | Recomendado. |

**Historial (brief):** en Fase 1 no hace falta tabla de historial unificada; **pagos** y **asistencias** enlazados por FK a `Client` permiten historial en Fase 3/5. Opcional: propiedad en modelo solo lectura no persistida (fuera de Fase 1 estricta).

### 3.3 App `payments`

| Campo | Tipo sugerido | Null | Notas |
|-------|----------------|------|--------|
| `id` | PK | — | |
| `client` | `ForeignKey(Client, related_name='payments')` | no | `on_delete=CASCADE` o `PROTECT` según política de borrado; documentar decisión. |
| `amount` | `DecimalField(max_digits=…, decimal_places=2)` | no | Moneda MXN implícita salvo que se añada `currency` en el futuro. |
| `payment_date` | `DateField` | no | Fecha de pago (brief). |
| `expiration_date` | `DateField` | no | Fecha de vencimiento (brief); Fase 2 validará “activo” cruzando con `date.today()` en zona del proyecto. |
| `status` | `CharField` con `choices` o `PositiveSmallIntegerField` con choices | no | Brief: activo / vencido. Puede ser **derivable** por fecha; tener campo persistido acelera admin y filtros. Opción mínima: `ACTIVE`, `EXPIRED` actualizado por comando o al guardar en Fase 2; en Fase 1 puede default `ACTIVE` y `help_text` indicando que la fuente de verdad temporal es `expiration_date`. |
| `created_at` / `updated_at` | `DateTimeField` | — | Recomendado; `created_at` útil para orden “último pago”. |

**Índice recomendado (Fase 1 o inicio Fase 6):** `Index(fields=['client', '-payment_date'])` o similar para listar pagos por cliente rápido.

### 3.4 App `attendances`

| Campo | Tipo sugerido | Null | Notas |
|-------|----------------|------|--------|
| `id` | PK | — | |
| `client` | `ForeignKey(Client, related_name='attendances')` | no | |
| `attendance_date` | `DateField` | no | Día de la asistencia (un registro por día por cliente). Nombre explícito evita confusión con `auto_now_add`. |
| `status` | `CharField` con choices cortos | no | Brief menciona `status`; valores mínimos sugeridos: `REGISTERED` (registro normal), `CANCELLED` (anulación recepción), reservar extensión sin complicar Fase 2. |
| `registered_at` | `DateTimeField`, `auto_now_add` | no | Opcional pero útil para auditoría “a qué hora pasó” sin romper unicidad por día. |
| `notes` | `CharField` o `TextField`, blank | — | Opcional. |

**Restricción crítica (brief + §11):**

```text
UNIQUE (client_id, attendance_date)
```

En Django: `Meta.constraints = [models.UniqueConstraint(fields=['client', 'attendance_date'], name='uniq_attendance_per_client_day')]`.

Esto da integridad referencial **antes** de que exista el servicio de Fase 2 y evita condiciones de carrera dobles si dos requests insertan; la capa de aplicación igual debe manejar `IntegrityError` con mensaje amable en Fase 4.

---

## 4. Diagrama de relaciones (referencia)

```text
MembershipPlan (1) ──< (N) Client (1) ──< (N) Payment
                              │
                              └──< (N) Attendance
```

Ningún modelo de Fase 1 requiere FK desde `MembershipPlan` hacia `Client` inverso más allá del reverse por defecto de Django.

---

## 5. Migraciones y datos

### 5.1 Estrategia de migraciones

- Una **initial migration** por app en el orden 1.1–1.4.
- Evitar editar migraciones ya aplicadas en entornos compartidos; nuevos cambios → nuevas migraciones.
- Probar en local: `migrate` sobre base vacía; luego `sqlmigrate` opcional para revisar SQL de `UniqueConstraint`.

### 5.2 Rollback y entornos

- Documentar en README o en este plan: `python manage.py migrate attendances zero` (ejemplo) solo en desarrollo; en staging/producción seguir política de reversión del equipo.

### 5.3 Fixtures y factories

- **Fixture mínima:** tres `MembershipPlan` + 1–2 `Client` de prueba + 1 `Payment` + 0–1 `Attendance` coherente.
- **Factory Boy** (opcional Fase 1): si el equipo ya usa tests automatizados, añadir `factory_boy` en requirements de desarrollo y factories por modelo para Fase 2; no es obligatorio para cerrar Fase 1 si el criterio de salida se cumple con fixtures y admin manual.

---

## 6. Admin Django (mínimo viable en Fase 1)

Objetivo: verificar datos sin API. No sustituye Fase 3 (Unfold pulido, inlines, permisos).

- Registrar `MembershipPlan`, `Client`, `Payment`, `Attendance` con `ModelAdmin` de **Unfold** (`from unfold.admin import ModelAdmin`).
- `list_display`, `list_filter` básicos (ej. `active` en cliente, `status` en pago, `attendance_date` en asistencia).
- `search_fields` en `Client`: `name`, `access_number`.

---

## 7. Lista de verificación de pruebas (Fase 1)

### 7.1 Base de datos y migraciones

- [ ] `migrate` en PostgreSQL limpio sin errores.
- [ ] `makemigrations --check` sin cambios pendientes tras commit.
- [ ] Intentar crear dos `Client` con el mismo `access_number` → falla (integridad / validación formulario admin).

### 7.2 Integridad referencial

- [ ] Eliminar un `MembershipPlan` con clientes asignados con `PROTECT` → debe fallar.
- [ ] Crear `Payment` y `Attendance` ligados a un `Client` existente → OK.

### 7.3 Asistencias

- [ ] Dos `Attendance` mismo `client` y mismo `attendance_date` → falla con `IntegrityError` (o error de validación si se añade validación duplicada en `clean()`).

### 7.4 Datos semilla

- [ ] Existencia de **3** planes en catálogo tras seed/migración de datos.
- [ ] Al menos un cliente de prueba con plan asignado y un pago con `expiration_date` posterior a `payment_date`.

### 7.5 Rendimiento (diseño, mediciones en Fase 6)

- [ ] Confirmar que existe índice/unicidad sobre `access_number` (búsqueda check-in futuro).
- [ ] Confirmar `UniqueConstraint` en `(client, attendance_date)` (equivale a índice útil para “¿ya vino hoy?”).

---

## 8. Criterios de salida (definición de “Fase 1 cerrada”)

1. Las cuatro apps existen con modelos persistidos y migraciones aplicables en cadena limpia.
2. Relaciones FK y `UniqueConstraint` de asistencias cumplen el brief a nivel de esquema.
3. Tres tipos de paquete cargados y documentados (convención de `allowed_days`).
4. Lista de verificación §7 completada en entorno local (y en staging si aplica).
5. Ninguna regla de negocio compleja en vistas; como mucho `clean()` mínimo (p. ej. `expiration_date >= payment_date`) si el equipo lo desea explícitamente en Fase 1.

---

## 9. Riesgos y decisiones pendientes (resolver antes o durante Fase 1)

| Tema | Opción / mitigación |
|------|---------------------|
| Convención `allowed_days` | Documentar en `MembershipPlan` (help_text + README); alinear con Fase 2. |
| Estado de pago vs fecha | Decidir si `status` es manual, por `save()`, o solo por query; dejar constancia para Fase 2. |
| Zona horaria vs solo fecha | Si en el futuro hay turnos que cruzan medianoche, valorar `DateTimeField`; el brief enfatiza “por día” — `DateField` suele bastar. |
| Cuatro sedes | Si hace falta `pool_id` o similar en `Attendance`/`Client`, añadirlo en Fase 1 si el cliente ya lo exige; si no, anotar en backlog. |
| Reposiciones | Campo opcional en `Payment` o `Client`; si no se define, backlog explícito. |

---

## 10. Entregables concretos al cierre (checklist de artefactos)

- [ ] Carpetas de apps creadas y en `INSTALLED_APPS`.
- [ ] Migraciones iniciales en repo.
- [ ] Fixture o migración de datos para los 3 planes.
- [ ] Archivo `admin.py` por app (o centralizado donde acuerde el equipo) con registro mínimo Unfold.
- [ ] Actualización breve de [`planes_implementacion_fases.md`](./planes_implementacion_fases.md) o de este plan si el modelo difiere del orientativo (tabla de Fase 1).
- [ ] Opcional: sección en README “Cómo cargar datos iniciales y correr migraciones”.

---

## 11. Siguiente fase (recordatorio)

La **Fase 2** consumirá estos modelos para implementar servicios de validación (membresía activa, día permitido, duplicado mismo día a nivel aplicación + mensajes de error). Mantener los nombres de campos y la convención de días **estables** para no refactorizar en cadena.

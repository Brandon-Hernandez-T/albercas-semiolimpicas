# Plan de implementación detallado — Fase 3 (backoffice: Django Admin + Unfold)

Este documento desarrolla la **Fase 3** definida en [`planes_implementacion_fases.md`](./planes_implementacion_fases.md), alineado con [`general_description.md`](./general_description.md) §3 (Admin), §4.1–4.4 (CRUD y consultas), §12 (staff, CSRF) y las recomendaciones §14 (priorizar operación clara).

**Prerrequisitos:** **Fase 1** (modelos) y **Fase 2** (servicios de validación) según los planes respectivos.

**Índice de planes:** tabla *Planes detallados por fase* en el documento maestro.

---

## 1. Objetivo

Que el **personal autorizado (staff)** gestione el día a día sin SQL ni código: altas y bajas de clientes, catálogo de planes, registro manual de pagos y consulta/alta controlada de asistencias, con interfaz **Unfold** coherente y reglas de negocio **centralizadas en Fase 2** donde corresponda.

---

## 2. Alcance y límites

### 2.1 Dentro de alcance

- `ModelAdmin` heredando de `unfold.admin.ModelAdmin` para: plan de membresía, cliente, pago, asistencia (nombres exactos según modelos Fase 1).
- `list_display`, `list_filter`, `search_fields` (mínimo búsqueda por nombre y `access_number` en clientes).
- **Inlines:** p. ej. pagos y/o asistencias recientes en la ficha del cliente (evitar listas enormes: `max_num`, paginación o solo últimos N vía `get_queryset`).
- **Acciones** opcionales: marcar cliente inactivo, exportar CSV reducido (si no duplica Fase 5).
- Integración con **Fase 2:** al crear `Attendance` desde admin, usar `ModelAdmin.save_model` / formulario personalizado que llame al servicio de check-in o validación equivalente para no violar R1–R3.
- **Permisos:** grupos Django (ej. `Recepción`, `Administración`) con permisos de vista/edición acordados con el cliente; mínimo: solo `is_staff` accede al admin (brief §12).
- Documentación corta para el cliente: “Cómo dar de alta un socio y registrar un pago” (PDF o sección README).

### 2.2 Fuera de alcance

- Pantalla de ingreso rápido recepción → **Fase 4**.
- Reportes analíticos y dashboards → **Fase 5**.
- Temas visuales muy personalizados (logos corporativos) pueden posponerse si no hay assets; Unfold ya mejora la base.

---

## 3. Pasos de implementación (orden sugerido)

### 3.1 Inventario y registro

| Paso | Acción |
|------|--------|
| 3.1 | Listar todos los modelos expuestos al staff; decidir cuáles son solo lectura o editables. |
| 3.2 | Crear o actualizar `admin.py` por app; eliminar duplicados de registro. |
| 3.3 | Asegurar que modelos de auth (`User`, `Group`) sigan patrón Unfold (app `core` u otra). |

### 3.2 UX operativa (Unfold)

| Paso | Acción |
|------|--------|
| 3.4 | `list_filter`: `active` en cliente; fechas en pagos; `attendance_date` / `status` en asistencias; `is_active` en planes. |
| 3.5 | `readonly_fields` en modelos donde los timestamps no deben editarse a mano. |
| 3.6 | `autocomplete_fields` o `raw_id` para FK pesados (cliente en pago/asistencia) si las listas son largas. |
| 3.7 | Ajustar `UNFOLD` en `settings` (sidebar): enlaces a listados frecuentes (clientes, asistencias de hoy si hay filtro personalizado). |

### 3.3 Validación de negocio en admin

| Paso | Acción |
|------|--------|
| 3.8 | Formulario personalizado `AttendanceAdminForm` con `clean()` que delegue en Fase 2 **o** override `save_model` para llamar servicio y mostrar `ValidationError` con mensaje del `CheckInResult`. |
| 3.9 | Pagos: validar `expiration_date >= payment_date` en formulario si no está en el modelo. |
| 3.10 | Prohibir borrados que rompan integridad; usar `PROTECT` ya definido en Fase 1 y mensajes claros. |

### 3.4 Permisos

| Paso | Acción |
|------|--------|
| 3.11 | Definir grupos y asignar permisos por modelo (view/add/change/delete). |
| 3.12 | Probar con usuario de recepción sin superuser: solo lo permitido. |

---

## 4. Flujos manuales de prueba (checklist)

- [ ] Crear los tres planes (o verificar seeds) desde admin.
- [ ] Crear cliente, asignar plan, marcar activo.
- [ ] Registrar pago con vigencia futura.
- [ ] Registrar asistencia manual para hoy → OK.
- [ ] Intentar segunda asistencia mismo día mismo cliente → bloqueo coherente con Fase 2 / BD.
- [ ] Buscar cliente por `access_number` desde el buscador del changelist.
- [ ] Usuario solo recepción: confirmar que no accede a modelos restringidos.

---

## 5. Criterios de salida

1. Staff realiza el flujo completo “alta + pago + asistencia” solo con admin.
2. Reglas R1–R3 no se saltan por atajos del admin.
3. Interfaz Unfold en todos los modelos gestionados.
4. Existe guía breve para el cliente o manual interno.

---

## 6. Riesgos

- **Inlines grandes:** degradan performance; limitar queryset.
- **Doble validación:** mantener una sola implementación de reglas (Fase 2); admin solo orquesta.

---

## 7. Siguientes fases

- **Fase 4:** `/quick-checkin/` para el flujo crítico de recepción (brief §4.5).
- **Fase 5:** reportes que complementen listados del admin.

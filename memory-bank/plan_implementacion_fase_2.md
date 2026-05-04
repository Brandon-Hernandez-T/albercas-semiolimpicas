# Plan de implementación detallado — Fase 2 (reglas de negocio / capa de dominio)

Este documento desarrolla la **Fase 2** definida en [`planes_implementacion_fases.md`](./planes_implementacion_fases.md), tomando las reglas de [`general_description.md`](./general_description.md) §4.4, §4.5 (flujo de validación), §5, §7 y los casos de prueba §10.

**Prerrequisito:** modelos y datos de **Fase 1** cerrados según [`plan_implementacion_fase_1.md`](./plan_implementacion_fase_1.md) (convención de `allowed_days`, `Payment`, `Attendance`, unicidad por día).

**Índice de planes:** tabla *Planes detallados por fase* en el documento maestro.

---

## 1. Objetivo

Centralizar en **servicios o funciones puras testeables** toda la lógica que decide si un cliente puede ingresar **hoy** (zona `America/Mexico_City`), sin duplicar reglas en vistas HTTP ni en admin. El resultado debe ser consumible por Fase 3 (guardados), Fase 4 (HTMX) y futuras APIs.

---

## 2. Reglas de negocio (fuente: brief §5 y §4.4)

| ID | Regla | Comportamiento esperado |
|----|--------|-------------------------|
| R1 | Una asistencia por cliente y día | Si ya existe `Attendance` para ese `client` y fecha civil local → denegar (mensaje explícito). BD ya puede tener `UniqueConstraint` (Fase 1); la capa de servicio debe anticipar y devolver motivo legible. |
| R2 | Membresía activa | “Activa” según **pagos y vigencia** (brief §5: los pagos determinan vigencia). Definir regla única: p. ej. existe pago con `expiration_date >= hoy_local` y opcionalmente `status=ACTIVE` si el modelo lo tiene. Cliente `active=False` → denegar. |
| R3 | Día permitido | El día de la semana de **hoy** (según convención documentada en Fase 1 para `allowed_days` del plan del cliente) debe estar incluido en la lista. |
| R4 | Cliente sin membresía / sin plan | Sin `membership_plan` o inconsistente → denegar. |
| R5 | Reposiciones | Brief: fase futura o flag simple. Incluir **solo** si Fase 1 dejó campo acordado; si no, documentar “no implementado” y no bloquear cierre de Fase 2. |

**Casos de prueba obligatorios (brief §10):** sin membresía; membresía vencida; segundo ingreso mismo día; día no permitido; caso válido → ✅.

---

## 3. Alcance y límites

### 3.1 Dentro de alcance

- Módulo(s) dedicados, p. ej. `checkin/services.py`, `clients/services/checkin.py`, o paquete `services/` en la raíz; **una sola** entrada pública recomendada, p. ej. `evaluate_checkin(access_number: str, on_date: date | None) -> CheckInResult`.
- Tipo de resultado inmutable o dataclass: `allowed: bool`, `reason_code: str` (estable para i18n o mapeo a mensaje), `message: str` (texto humano para recepción), opcionalmente `client_id`, `attendance_id` tras registro exitoso.
- Función separada o método **`register_attendance_if_allowed`** que: valida; si OK, crea `Attendance` en transacción atómica; captura `IntegrityError` por carrera y traduce a mensaje de denegación.
- Uso de **`timezone.localdate()`** o fecha explícita inyectada en tests para “hoy”.
- Tests unitarios con base de datos de prueba o factories (sin servidor HTTP obligatorio en Fase 2).

### 3.2 Fuera de alcance

- Plantillas HTMX y URLs públicas de check-in → **Fase 4**.
- Pulido visual del admin → **Fase 3** (pero admin puede **llamar** al servicio al guardar si se acuerda en Fase 3).
- Reportes agregados → **Fase 5**.

---

## 4. Diseño del servicio (pasos 2.1–2.6)

### 4.1 Contrato de entrada/salida

| Elemento | Especificación |
|----------|----------------|
| Entrada principal | `access_number` (string tal como lo teclea recepción; normalizar: `strip`, posiblemente quitar espacios internos según política del negocio). |
| Búsqueda de cliente | Query optimizada: `select_related("membership_plan")` + prefetch de pagos recientes si hace falta; **índice** en `access_number` (Fase 1). |
| Fecha de evaluación | Parámetro opcional `on_date` para tests; producción usa fecha local del sitio. |
| Salida | `CheckInResult` (nombre ejemplo) con campos acordados en §3.1. |

### 4.2 Orden de validación sugerido

1. Resolver cliente por `access_number`; si no existe → `reason_code=CLIENT_NOT_FOUND`.
2. Cliente inactivo → `CLIENT_INACTIVE`.
3. Plan / membresía faltante → `NO_MEMBERSHIP_PLAN`.
4. Vigencia de pago (R2) → `MEMBERSHIP_EXPIRED` o `NO_ACTIVE_PAYMENT`.
5. Día permitido (R3) → `DAY_NOT_ALLOWED`.
6. Asistencia ya registrada ese día (R1) → `ALREADY_CHECKED_IN` (query o intento de insert).
7. Si todo OK → `allowed=True`; persistencia en paso 4.3.

Documentar mensajes en español para operador (Fase 4 reutiliza).

### 4.3 Transacciones e idempotencia

- `atomic()` al crear asistencia.
- Si dos peticiones concurrentes pasan validaciones lógicas, la segunda debe fallar en BD; devolver mismo código de usuario que “ya ingresó hoy”.

### 4.4 Códigos de motivo (recomendación)

Definir enum o constantes de string estables (`CLIENT_NOT_FOUND`, `MEMBERSHIP_EXPIRED`, …) para no acoplar tests a texto libre.

### 4.5 Integración con modelos

- No añadir lógica pesada en `save()` de modelos salvo delegación en una línea al servicio (evitar llamadas circulares).
- Opcional: `Client.clean()` mínimo si el equipo desea validaciones de integridad en admin; debe ser coherente con el servicio.

### 4.6 Documentación interna

- Docstring en la función pública describiendo R1–R4 y convención de días.
- Enlace en comentario al párrafo de `allowed_days` en el modelo de Fase 1.

---

## 5. Pruebas (detalle)

### 5.1 Matriz mínima (brief §10)

| Caso | Preparación datos | Resultado esperado |
|------|-------------------|---------------------|
| Sin membresía | Cliente sin plan o sin pagos según regla R2 | `allowed=False` |
| Membresía vencida | Pago con `expiration_date` < `on_date` | `allowed=False` |
| Segundo ingreso mismo día | Tras un check-in OK, segunda llamada mismo `on_date` | `allowed=False` |
| Día no permitido | `on_date` cuyo weekday no está en `allowed_days` | `allowed=False` |
| Válido | Cliente activo, pago vigente, día OK, sin asistencia | `allowed=True` y fila `Attendance` creada (si el método incluye persistencia) |

### 5.2 Casos límite recomendados

- Medianoche / `USE_TZ`: dos instantes distintos mismo día civil local → una sola asistencia permitida.
- `access_number` con mayúsculas/minúsculas según política de unicidad en BD.
- Cliente sin pagos pero con plan: denegar si la regla de negocio exige al menos un pago.

---

## 6. Lista de verificación de cierre

- [ ] Una API interna clara (función o clase de servicio) usada como única fuente de verdad para check-in.
- [ ] Los cinco casos §5.1 cubiertos por tests automatizados.
- [ ] Códigos de motivo estables documentados.
- [ ] Sin lógica duplicada en vistas (grep / revisión de código).
- [ ] Reposiciones: implementado o explícitamente pospuesto con nota en README o en este plan.

---

## 7. Criterios de salida

1. Tests verdes en CI o local con comando documentado (`pytest` / `manage.py test`).
2. Cualquier desarrollador puede entender las reglas leyendo el módulo de servicio y el brief.
3. Fase 4 puede importar el servicio sin refactor mayor.

---

## 8. Siguientes fases

- **Fase 3:** Admin que use filtros y, donde aplique, el servicio al crear asistencias manualmente.
- **Fase 4:** Vista `/quick-checkin/` que invoque el mismo servicio.

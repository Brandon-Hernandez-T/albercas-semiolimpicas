# Plan de implementación detallado — Fase 5 (reportes y operación)

Este documento desarrolla la **Fase 5** definida en [`planes_implementacion_fases.md`](./planes_implementacion_fases.md), alineado con [`general_description.md`](./general_description.md) §2 (reportes básicos), §4 (datos disponibles por módulo) y §13 (fuera de alcance: BI avanzado, integraciones).

**Prerrequisitos:** **Fase 1–4** con datos reales o de staging suficientes para validar totales.

**Índice de planes:** tabla *Planes detallados por fase* en el documento maestro.

---

## 1. Objetivo

Dar **visibilidad operativa y administrativa** al cliente: asistencias por periodo, ingresos por periodo (según pagos registrados), alertas simples (membresías por vencer), sin construir un data warehouse ni BI avanzado.

---

## 2. Alcance y límites

### 2.1 Dentro de alcance (elegir con el cliente antes de implementar)

| Reporte sugerido | Fuente de datos | Implementación típica |
|------------------|-----------------|------------------------|
| Asistencias por día (rango de fechas) | `Attendance` + `Client` | Changelist admin con filtros de fecha; o vista staff + tabla; o export CSV. |
| Ingresos por periodo | `Payment` (`amount`, `payment_date`) | Misma familia de opciones; suma en vista o query agregada. |
| Clientes con membresía por vencer (N días) | `Payment.expiration_date` o regla Fase 2 | Lista filtrada o comando management `report_expiring` que imprima CSV. |
| Por sede / alberca | Solo si Fase 1+ introdujo `venue` | Si no existe campo, **excluir** o fase futura explícita. |

### 2.2 Fuera de alcance (brief §13)

- Cuadros de mando interactivos complejos, ML, integraciones contables externas.
- Pagos en línea o conciliación bancaria automática.

---

## 3. Pasos de implementación

### 3.1 Descubrimiento (obligatorio)

| Paso | Acción |
|------|--------|
| 5.1 | Workshop corto con el cliente: lista final de reportes y formato (pantalla vs CSV vs ambos). |
| 5.2 | Definir zona horaria de los rangos (**America/Mexico_City**) y si “día” es civil local. |
| 5.3 | Documentar definiciones: “ingreso” = suma de `Payment.amount` en rango; “asistencia” = conteo de filas `Attendance` con `status` incluido. |

### 3.2 Implementación por opción

**Opción A — Solo Admin**

- Filtros personalizados (`SimpleListFilter`) por rango de fechas en `Attendance` y `Payment`.
- `date_hierarchy` donde aplique.
- Acción de export CSV en changelist (Django admin actions).

**Opción B — Vistas staff**

- URLs bajo prefijo `/staff/reports/...` con decorador staff.
- Plantillas tabulares simples; paginación si el volumen es alto.

**Opción C — Comandos + CSV**

- `python manage.py export_attendances --from --to > file.csv` para auditoría offline.

### 3.3 Calidad de datos en reportes

| Paso | Acción |
|------|--------|
| 5.4 | Usar `aggregate` / `annotate` con `select_related` mínimo necesario. |
| 5.5 | No exponer datos personales en CSV sin acuerdo de privacidad; considerar columnas mínimas. |

---

## 4. Pruebas

- [ ] Con fixtures de totales **conocidos**, verificar sumas y conteos del reporte.
- [ ] Rango que cruza cambio de mes / año en zona del proyecto.
- [ ] Usuario no staff no accede a vistas B ni a exportaciones restringidas.

---

## 5. Criterios de salida

1. Los reportes acordados están disponibles y documentados (cómo generarlos).
2. El cliente puede auditar operación diaria **sin SQL ad hoc** (criterio del plan maestro).
3. No se prometen capacidades de §13 fuera de alcance.

---

## 6. Riesgos

- **Confusión ingresos vs caja real:** los reportes reflejan solo lo registrado en el sistema (brief: registro manual de pagos).
- **Performance:** volúmenes grandes → paginación o export asíncrono (futuro); Fase 6 refuerza índices.

---

## 7. Siguientes fases

- **Fase 6:** optimizar consultas usadas aquí y las del check-in.
- **Fase 7:** validar reportes en UAT y en producción con datos reales.

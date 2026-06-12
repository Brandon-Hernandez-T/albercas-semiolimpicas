# Manual breve — operación en Django Admin (staff)

Contexto: sistema de albercas con **Unfold** en `/admin/`. Solo usuarios con **is_staff** acceden (y permisos por grupo si aplica).

## 1. Alta de un socio

1. Ir a **Clientes** → **Añadir cliente**.
2. Completar **nombre**, **número de acceso** (único), **plan de membresía** y dejar **activo** marcado.
3. Guardar.

## 2. Registrar un pago

1. Abrir el cliente (o **Pagos** → **Añadir pago** y elegir cliente).
2. Indicar **monto**, **fecha de pago** y **fecha de vencimiento** (debe ser ≥ fecha de pago).
3. Estado **Activo** / **Vencido** según operación; la vigencia para reglas de ingreso usa sobre todo las fechas y pagos activos (ver Fase 2).

## 3. Registrar asistencia manual

1. **Asistencias** → **Añadir asistencia** (o desde el cliente, pestaña de asistencias).
2. Elegir **cliente** y **día de asistencia**.
3. El formulario valida con las **mismas reglas** que el ingreso rápido (membresía vigente, día permitido, una asistencia por día, etc.). Si falla, se muestra el mensaje de error.
4. Para **editar** solo notas o estado del mismo día y cliente, la validación no bloquea (misma “casilla” de día).

## 4. Filtros útiles

- En **Asistencias**, filtro **periodo → Hoy** (o **Últimos 7 días** / **Mes actual**) para ver ingresos del día civil local (`America/Mexico_City`).

## 5. Acciones en lista de clientes

- Seleccionar clientes y **Marcar como inactivos** para baja lógica masiva.

## 6. Grupos de permisos (opcional)

Tras migraciones aplicadas:

```bash
python manage.py setup_staff_groups
```

Asignar en el admin cada usuario staff al grupo **Recepción** o **Administración** y comprobar que solo vea lo permitido.

## 7. Ingreso rápido (recepción en pico)

1. Iniciar sesión con una cuenta **staff** (puede ser el mismo login que usas en `/admin/`).
2. Abrir **`/quick-checkin/`** (también enlazado desde el menú lateral de Unfold como **Ingreso rápido**).
3. Escribir el **número de acceso** del socio y pulsar **Enter** o **Registrar ingreso**.
4. Mensaje **verde** = ingreso registrado; **rojo** = denegado con motivo (mismas reglas que Fase 2).
5. Tras un ingreso correcto el formulario se limpia y el cursor vuelve al campo para el siguiente cliente.

Si no has iniciado sesión, el sistema te envía a `/admin/login/`.

## 8. Reportes operativos (Fase 5)

Panel principal: **`/staff/reports/`** (también en el menú Unfold → **Reportes**).

| Reporte | URL | Definición |
|---------|-----|------------|
| Asistencias por periodo | `/staff/reports/asistencias/` | Conteo de filas `Attendance` por día en el rango (día civil local). |
| Ingresos por periodo | `/staff/reports/ingresos/` | Suma de `Payment.amount` con `payment_date` en el rango. |
| Membresías por vencer | `/staff/reports/por-vencer/` | Clientes activos con pago ACTIVE que vence en los próximos N días. |

Cada pantalla incluye enlace **Descargar CSV**. En el admin, los listados de **Pagos** y **Asistencias** tienen filtros de periodo y acción **Exportar selección a CSV**.

Comandos (salida en terminal):

```bash
python manage.py export_attendances --from 2026-05-01 --to 2026-05-31
python manage.py export_payments --from 2026-05-01 --to 2026-05-31
python manage.py report_expiring --days 30
```

Sin `--from` / `--to`, los exportadores usan el mes calendario actual.

## 9. Producción y rendimiento (Fase 6)

Documento de referencia para despliegue: [`listo_para_produccion.md`](./listo_para_produccion.md).

Comandos útiles antes del go-live:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py benchmark_checkin --access-number DEMO001 --evaluate-only
python manage.py explain_checkin_queries --access-number DEMO001
```

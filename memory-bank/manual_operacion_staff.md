# Manual breve — operación en Django Admin (staff)

Contexto: sistema de albercas con **Unfold** en `/admin/`. Solo usuarios con **is_staff** acceden (y permisos por grupo si aplica).

## 1. Alta de un socio

1. Ir a **Clientes** → **Añadir cliente**.
2. Completar **nombre**, **número de acceso** (único), **plan de membresía** y dejar **activo** marcado.
3. Guardar.

### Importar / exportar clientes (CSV)

En **Clientes** (listado del admin):

- **Exportar todos (CSV)** — descarga todos los socios.
- **Importar CSV** — sube un archivo con columnas: `nombre`, `numero_acceso`, `plan_slug`, `activo`, `notas`.
- Acción **Exportar selección a CSV** — solo los marcados en la lista.

El `plan_slug` debe existir (ej. `completo`, `entre-semana`, `fin-de-semana`). Con **Actualizar si ya existe el número de acceso**, se actualizan filas con el mismo `numero_acceso`.

Ejemplo de fila:

```csv
nombre,numero_acceso,plan_slug,activo,notas
María López,ACC1001,completo,1,
```

Por terminal:

```bash
python manage.py export_clients > clientes.csv
python manage.py import_clients clientes.csv
```

## 2. Registrar un pago

1. Abrir el cliente (o **Pagos** → **Añadir pago** y elegir cliente).
2. Indicar **monto**, **fecha de pago** (día en que entró el dinero), **inicio de vigencia** (acceso) y **fecha de vencimiento**.
3. Si dejas vacío el inicio de vigencia, se usa la fecha de pago. Para un **adelanto**, pon la fecha de pago = hoy y el inicio de vigencia = día en que empieza la membresía (puede ser posterior).
4. El formulario muestra el **precio del plan** del cliente. Reglas:
   - **Monto ≥ precio del plan** → estado **Activo (pago completo)**; el socio puede ingresar si la fecha está en vigencia (`inicio ≤ hoy ≤ vencimiento`).
   - **Monto menor** → **Pago parcial**; no basta para ingresar **hasta completar** el precio (varios abonos en el mismo periodo de vigencia **se suman**).
   - **Vencido** → sin acceso aunque hubiera saldo pagado antes.
5. Ejemplo normal: plan $1,200 → un pago de $1,200 activo, o dos de $600 en las mismas fechas de vigencia.
6. Ejemplo adelanto: el 31 ago cobra la membresía que inicia el 3 sep → `fecha de pago=31 ago`, `inicio de vigencia=3 sep`. El dinero sale en el **corte del 31**; el acceso con ese pago empieza el 3. La membresía actual (si aún no vence) sigue válida entre tanto.

## 3. Registrar asistencia manual

1. **Asistencias** → **Añadir asistencia** (o desde el cliente, pestaña de asistencias).
2. Elegir **cliente** y **día de asistencia**.
3. El formulario valida con las **mismas reglas** que el ingreso rápido (membresía vigente, día permitido, una asistencia por día, etc.). Si falla, se muestra el mensaje de error.
4. Para **editar** solo notas o estado del mismo día y cliente, la validación no bloquea (misma “casilla” de día).

## 4. Filtros útiles

- En **Asistencias**, filtro **periodo → Hoy** (o **Últimos 7 días** / **Mes actual**) para ver ingresos del día civil local (`America/Mexico_City`).

## 5. Acciones en lista de clientes

- Seleccionar clientes y **Marcar como inactivos** para baja lógica masiva.

## 6. Grupos de permisos

Tras migraciones aplicadas:

```bash
python manage.py setup_staff_groups
```

Asignar en el admin cada usuario staff al grupo **Recepción** o **Administración** (y desmarcar Superusuario si deben aplicar los permisos del grupo).

| Capacidad | Recepción | Administración |
|-----------|-----------|----------------|
| Nadadores (alta/edición) | Sí (su alberca) | Sí (todas) |
| Pagos | Solo **agregar** y ver; no editar ni eliminar | Sí (incl. editar/eliminar) |
| Credenciales / ingreso rápido | Sí | Sí |
| Reportes | Su alberca; en **ingresos** solo su propio corte | Todas las albercas; filtro libre de recepcionista |

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
| Ingresos por periodo | `/staff/reports/ingresos/` | Suma de `Payment.amount` con `payment_date` en el rango (día de cobro, aunque la vigencia empiece después). |
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

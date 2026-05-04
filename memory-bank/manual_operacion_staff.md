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

- En **Asistencias**, filtro **fecha rápida → Hoy** para ver ingresos del día civil local (`America/Mexico_City`).

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

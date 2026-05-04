# Plan de implementación detallado — Fase 4 (ingreso rápido — crítico)

Este documento desarrolla la **Fase 4** definida en [`planes_implementacion_fases.md`](./planes_implementacion_fases.md), alineado con [`general_description.md`](./general_description.md) §4.5 (ingreso rápido), §5 (reglas), §8 (HTMX), §10 (testing), §11 (performance), §12 (seguridad) y §14 (velocidad de uso).

**Prerrequisitos:** **Fase 2** (servicio de check-in) obligatorio; **Fase 3** recomendable para datos de prueba. Modelos **Fase 1**.

**Índice de planes:** tabla *Planes detallados por fase* en el documento maestro.

---

## 1. Objetivo

Entregar la pantalla de **check-in en recepción** con latencia percibida **muy baja** (meta del brief: **&lt; 1 s** ideal, **&lt; 2 s** por cliente aceptable en condiciones normales), uso **casi solo teclado**, feedback **verde/rojo** y **motivo** legible cuando se deniega, sin duplicar reglas fuera del servicio de Fase 2.

---

## 2. Alcance técnico

### 2.1 Entregables

| Componente | Especificación |
|------------|----------------|
| App sugerida | `checkin` (brief §6) o equivalente bajo `apps.checkin`. |
| Ruta | `/quick-checkin/` (brief §4.5); nombre interno de URL configurable pero documentado. |
| Autenticación | Solo **staff** autenticado (brief §12); `LoginRequiredMixin` + `UserPassesTestMixin` o decorador `staff_member_required`. |
| Plantilla | Django Templates: formulario con un campo (`access_number` o nombre acordado), `autofocus`, envío en **Enter** (form nativo o JS mínimo). |
| HTMX | `hx-post` al endpoint que procesa el número; `hx-target` en contenedor de resultado; `hx-swap` (p. ej. `innerHTML`). Incluir **CSRF** (`csrf_token` o header según documentación HTMX + Django). |
| Respuesta | Fragmento HTML parcial: bloque éxito (clase CSS “éxito” / verde) con confirmación; bloque error (rojo) con **mensaje** del `CheckInResult` de Fase 2. |
| Post-éxito | Re-enfocar input (atributo `hx-on::after-request` o `htmx:afterSwap` en JS mínimo) para cadena de clientes en pico (brief: input siempre listo). |
| Persistencia | Solo vía servicio Fase 2 que crea `Attendance` si procede. |

### 2.2 Dependencias

- Añadir **HTMX:** script desde CDN en plantilla de desarrollo o archivo estático versionado en prod (`collectstatic`). Opcional: paquete `django-htmx` para middleware y helpers.
- No introducir SPA pesada; cumplir brief §8.

### 2.3 Fuera de alcance

- App móvil nativa, pagos en línea (brief §13).
- Reportes agregados → **Fase 5**.

---

## 3. Pasos de implementación (orden sugerido)

| Paso | Acción |
|------|--------|
| 4.1 | Crear app `checkin`; registrar en `INSTALLED_APPS`. |
| 4.2 | Vista GET: renderiza plantilla completa mínima (base + formulario + `#result`). |
| 4.3 | Vista POST: recibe `access_number`; invoca servicio Fase 2; retorna **solo** partial (sin layout) si la petición es HTMX (`HX-Request` header) o según patrón del equipo. |
| 4.4 | Añadir `urls.py` del proyecto `path("quick-checkin/", ...)`. |
| 4.5 | Estilos: clases utilitarias o CSS mínimo (fondo verde claro / rojo claro, texto legible, tamaño de fuente cómodo para recepción). |
| 4.6 | Manejo de errores no previstos: 500 logueado; usuario ve mensaje genérico sin filtrar trazas. |
| 4.7 | (Opcional) Rate limiting básico por IP/usuario si hay riesgo de abuso. |

---

## 4. Performance (brief §11)

| Acción | Motivo |
|--------|--------|
| Query única o pocas en el servicio | `access_number` indexado (Fase 1). |
| Evitar `select_related` innecesarios | Medir con `django-debug-toolbar` solo en staging (Fase 6). |
| No bloquear la vista con trabajo IO externo | Sin integraciones en esta fase. |

---

## 5. Pruebas

### 5.1 Automatizadas

- Test de integración: cliente autenticado staff, `POST` con HTMX headers simulados o cliente Django `Client`, verificar status HTTP y fragmento contiene mensaje esperado para al menos 2 casos (OK y denegado).
- Test de permiso: usuario no staff → 302 a login o 403.

### 5.2 Manuales (brief §10)

Reproducir los **cinco** escenarios desde el navegador; cronometrar en red local (meta &lt; 1–2 s).

### 5.3 UX (brief §4.5)

- [ ] Autofocus al cargar y tras éxito.
- [ ] Enter envía.
- [ ] Sin recarga completa de página en cada intento.
- [ ] Color y mensaje claros.

---

## 6. Criterios de salida

1. Los cinco casos del brief reproducibles desde `/quick-checkin/`.
2. Solo staff autenticado; CSRF activo.
3. Cero duplicación de reglas de negocio fuera de Fase 2.
4. Operador puede encadenar ingresos sin usar ratón de forma obligatoria.

---

## 7. Riesgos

- **CSRF y HTMX:** verificar doble envío o pérdida de token en swaps.
- **Concurrencia:** Fase 2 + `UniqueConstraint` deben dar mensaje único al usuario.
- **Accesibilidad:** contraste mínimo en colores de éxito/error.

---

## 8. Siguientes fases

- **Fase 5:** reportes para supervisión (asistencias por día, etc.).
- **Fase 6:** carga y `EXPLAIN` sobre el flujo de esta fase.

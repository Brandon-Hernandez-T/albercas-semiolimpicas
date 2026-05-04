# 🧠 **PROJECT BRIEF — Sistema de Gestión de Albercas (Django Only)**

## 📌 1. Contexto del Proyecto

El cliente opera **4 albercas olímpicas** con alto volumen de usuarios, especialmente en horarios pico donde múltiples clientes ingresan en pocos minutos.

Actualmente el proceso es manual o poco eficiente, por lo que se requiere un sistema que:

- Controle el acceso de clientes a clases.
- Administre membresías y pagos.
- Registre asistencias con reglas estrictas.
- Permita operación rápida en recepción.

👉 **Punto crítico del sistema:**  
El módulo de **Ingreso Rápido**, que debe ser **extremadamente ágil (menos de 2 segundos por cliente)**.

---

## 🎯 2. Objetivo del Sistema

Desarrollar una plataforma backend con Django que permita:

- Gestión completa de clientes.
- Control de membresías y vigencias.
- Registro de asistencias automatizado.
- Validaciones en tiempo real.
- Operación eficiente en recepción.
- Reportes básicos administrativos.

---

## ⚙️ 3. Stack Tecnológico

- Backend: **Django**
- Base de datos: **PostgreSQL**
- UI:
  - Django Admin (backoffice)
  - Django Templates + **HTMX** (Ingreso Rápido)
- Deploy: DigitalOcean

---

## 🧩 4. Módulos del Sistema

### 👤 4.1 Clientes

- CRUD completo.
- Número único de acceso.
- Relación con membresía.
- Historial (pagos + asistencias).

---

### 🏷 4.2 Membresías

- 3 tipos de paquetes.
- Configuración de:
  - Días permitidos.
  - Vigencia.
  - Estado.

---

### 💰 4.3 Pagos

- Registro manual.
- Fecha de pago.
- Fecha de vencimiento.
- Estado (activo/vencido).

---

### ✅ 4.4 Asistencias

- Registro automático.
- Restricciones:
  - ❗ Solo 1 asistencia por día.
  - ❗ Validar día permitido.
  - ❗ Validar membresía activa.

---

### ⚡ 4.5 Ingreso Rápido (CRÍTICO)

#### Descripción:

Pantalla optimizada para recepción que permite registrar acceso en segundos.

#### Flujo:

1. Usuario ingresa número de cliente.
2. Sistema valida:
  - Membresía activa.
  - Día permitido.
  - No asistencia previa ese día.
3. Resultado inmediato:
  - ✅ Acceso permitido
  - ❌ Acceso denegado + motivo

#### Requisitos UX:

- Input auto-focus siempre.
- Enter para enviar.
- Respuesta inmediata (HTMX).
- Feedback visual:
  - Verde = OK
  - Rojo = Error
- Tiempo de respuesta < 1 segundo.

#### Endpoint sugerido:

```

```

```
/quick-checkin/
```

---

## 🧠 5. Reglas de Negocio

- Un cliente solo puede ingresar **1 vez por día**.  

- Membresía debe estar **activa**.  

- Solo puede asistir en **días permitidos**.  

- Pagos determinan vigencia.  

- Se pueden permitir reposiciones (fase futura o simple flag).  

---

## 🏗 6. Arquitectura Sugerida

```

```

```
apps/
  clients/
  memberships/
  payments/
  attendances/
  checkin/
```

---

## 🗃 7. Modelos Base (Simplificado)

### Client

- id  

- name  

- access_number (único)  

- membership (FK)  

- active  

---

### Membership

- name  

- allowed_days (JSON o ManyToMany)  

- duration_days  

---

### Payment

- client  

- amount  

- payment_date  

- expiration_date  

---

### Attendance

- client  

- date  

- status  

---

## ⚡ 8. Estrategia para Ingreso Rápido

### Tech:

- Django Template  

- HTMX (`hx-post`)  

- Partial rendering  

### Ejemplo flujo HTMX:

```

```

```
<form hx-post="/quick-checkin/" hx-target="#result">
  <input name="client_number" autofocus />
</form>

<div id="result"></div>
```

---

## ⏱ 9. Cronograma (8 semanas)

### Semana 1

- Kickoff  

- Definición reglas  

### Semana 2

- Modelos base  

### Semana 3

- Lógica negocio  

### Semana 4

- Django Admin  

### Semana 5

- Ingreso rápido (HTMX)  

### Semana 6

- Pagos + reportes  

### Semana 7

- QA  

### Semana 8

- Deploy  

---

## 🧪 10. Testing

- Casos críticos:  

-   Cliente sin membresía → ❌  

-   Membresía vencida → ❌  

-   Segundo ingreso mismo día → ❌  

-   Día no permitido → ❌  

-   Caso válido → ✅  

---

## 🚀 11. Performance (MUY IMPORTANTE)

- Index en:  
  - `client.access_number`  
  - `attendance.date`  

- Queries optimizadas.  

- Evitar joins innecesarios.  

- Cache ligero opcional.  

---

## 🔒 12. Seguridad

- Login requerido para staff.  

- Protección CSRF.  

- Validaciones backend siempre.  

---

## 📌 13. Fuera de alcance

- App móvil  

- Pagos en línea  

- Integraciones externas  

- BI avanzado  

---

## 🧠 14. Recomendaciones para el equipo

- Priorizar funcionalidad sobre estética.  

- Optimizar flujo de ingreso primero.  

- Evitar overengineering.  

- Mantener código simple y claro.  

- Pensar siempre en velocidad de uso.  

---

# 🔥 BONUS (MUY IMPORTANTE)

Para usar IA en el desarrollo, siempre dar contexto como:

> “Estoy construyendo un sistema de check-in rápido para albercas con Django + HTMX donde necesito validar membresías activas, restricciones por día y evitar duplicados por día…”


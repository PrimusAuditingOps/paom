# Gestión de Activos de TI — Guía del Usuario

> **¿Para quién es esta guía?** Para quienes tienen el perfil **Usuario** del
> módulo (por ejemplo, **Finanzas**). Con este perfil **consultas** toda la
> información de los equipos y licencias de la empresa (qué hay, quién lo
> tiene, cuánto costó y qué ha pasado con cada equipo), pero **no haces
> cambios**: los registros y movimientos los hace el equipo de TI.
>
> ¿Detectaste un dato incorrecto o necesitas un movimiento? Pídeselo a TI.

---

## Contenido

1. [Conceptos básicos](#1-conceptos-básicos)
2. [El Tablero](#2-el-tablero)
3. [Consultar equipos](#3-consultar-equipos)
4. [Consultar mantenimientos, movimientos y cartas](#4-consultar-mantenimientos-movimientos-y-cartas)
5. [Consultar software y licencias](#5-consultar-software-y-licencias)
6. [Costos y gasto](#6-costos-y-gasto)
7. [Búsquedas, filtros y exportar a Excel](#7-búsquedas-filtros-y-exportar-a-excel)
8. [Preguntas frecuentes](#8-preguntas-frecuentes)

---

## 1. Conceptos básicos

| Término | Qué significa |
|---|---|
| **Activo** | Un equipo físico (laptop, monitor, celular, access point…), identificado por su **etiqueta de activo** (ej. `LPT-MX-076`). |
| **Compañía** | El país donde el equipo **está en uso**: México, USA, Chile o Costa Rica. |
| **Responsable** | El **empleado** o el **departamento** que tiene el equipo. |
| **Suscripción** | Una plataforma de software contratada por una compañía (ej. *Google Workspace – Business Plus (Estados Unidos)*). |
| **Periodo** | Cada ciclo de contrato de una suscripción (normalmente un año), con su propio costo. |

### Estatus de un equipo

| Estatus | Significado |
|---|---|
| **Disponible** | Sin asignar, en bodega. |
| **Asignado** | En uso por un empleado o departamento. |
| **En tránsito** | Enviado por paquetería a su nuevo responsable. |
| **En reparación** | Fuera de servicio por mantenimiento o garantía. |
| **Dado de baja** | Retirado definitivamente (vendido, donado, desechado…). |
| **Extraviado / Robado** | Perdido o robado. |

### Menú del módulo

Entra a **Gestión de activos de TI** desde el menú principal de Odoo:

- **Tablero** — resumen con indicadores, gasto y alertas.
- **Hardware** → Activos · Mantenimiento · Movimientos · Cartas
- **Software** → Suscripciones · Asignaciones de licencias · Catálogo de software

> 💡 **Selector de compañías.** Lo que ves depende de las compañías que tengas
> seleccionadas en Odoo (arriba a la derecha). Con las 4 seleccionadas ves la
> información global; con solo una, solo la de ese país.

---

## 2. El Tablero

Es la pantalla con la que abre el módulo.

**Filtros (parte superior):**
- **Compañías**: botones con el país; actívalos o desactívalos para ver uno o
  varios países.
- **Desde / Hasta**: el periodo a analizar (por defecto, el año en curso).
  Puedes ajustarlo, por ejemplo, al año fiscal de tu país o a un trimestre.
- **Hardware / Software**: cambia la gráfica.

**Qué encuentras:**

| Sección | Qué te dice |
|---|---|
| **Activos vigentes** | Cuántos equipos están en operación, contra el total registrado. |
| **Valor de activos (costo de adquisición)** | Lo que costaron **al comprarse** los equipos vigentes, en USD. Los costos complementarios (mantenimiento, garantía, envíos) están en cada equipo, pestaña **Costos**. |
| **Compras del periodo** | Cuánto se gastó (USD) y cuántos equipos se compraron en el periodo. |
| **Gasto en software del periodo** | Costo de los contratos de software que **inician** en el periodo (USD). |
| **Uso de licencias** | Cuántos usuarios tienen licencia asignada contra cuántos permite lo contratado. |
| **Asignaciones por revisar · Preventivos vencidos · Envíos retrasados** | Pendientes de TI. Haz clic para ver el detalle. |
| **Gasto del periodo por concepto (USD)** | El gasto total del periodo separado en **Adquisiciones, Mantenimiento, Garantías, Envíos y Software**, con el % de cada uno. |
| **Gráfica** | *Hardware*: valor de los equipos por categoría. *Software*: gasto del periodo por tipo de software. |
| **Alertas (calendario)** | Mantenimientos programados, garantías que vencen, renovaciones o vencimientos de suscripciones y envíos en camino. Cambia de mes con ‹ ›; haz clic en un evento para abrirlo. |

> 💡 Todos los montos del tablero están en **USD**, convertidos con el tipo de
> cambio de la fecha de cada gasto.

---

## 3. Consultar equipos

**Hardware → Activos**

La lista muestra por defecto los **activos vigentes** (sin los dados de baja
ni los extraviados). Puedes cambiar entre vista de **lista** y **kanban**
(tarjetas con foto).

Al abrir un equipo verás:

- **Arriba**: etiqueta, foto, estatus, categoría, marca, modelo, condición,
  **próximo preventivo**, compañía, ubicación (Oficina / Home Office),
  responsable, departamento y fecha de alta.
- **Detalles**: número de serie, número de producto, IMEI (celulares),
  especificaciones y notas.
- **Compra**: cómo se compró (orden de compra u otro método como Amazon),
  proveedor, fecha, **costo** y moneda. Si vino de una orden de compra, se
  listan sus **facturas de proveedor** con su estado. Si se pagó por otro
  medio, aparece la factura o **póliza** ligada. También la **distribución
  analítica**.
- **Garantía**: vigencia, proveedor y estatus (*En garantía*, *Por vencer*,
  *Vencida*).
- **Costos**: costo total del equipo en USD (ver [sección 6](#6-costos-y-gasto)).
- **Mantenimiento**: todos sus mantenimientos (preventivos, correctivos y de
  garantía) con fechas, técnico o proveedor y costo.
- **Historial**: todo lo que le ha pasado al equipo (alta, asignaciones,
  envíos, devoluciones, reparaciones, bajas), con fechas, responsables,
  compañía, ubicación y quién hizo cada movimiento. Debajo, sus **cartas**
  responsivas y de devolución.
- **Galería**: fotos de evidencia.

> 💡 Los empleados y departamentos aparecen con su país entre paréntesis (ej.
> *IT (México)*), porque algunos se repiten en varias compañías.

---

## 4. Consultar mantenimientos, movimientos y cartas

- **Hardware → Mantenimiento**: todos los mantenimientos. Usa la vista de
  **calendario** para ver los programados, y los filtros *Preventivo /
  Correctivo / Garantía*, *Vencido* y por estatus.
- **Hardware → Movimientos**: el historial de **todos** los equipos. Útil
  para auditoría, por ejemplo con los filtros *Entre compañías* (equipos que
  cambiaron de país), *Envíos* o por fecha.
- **Hardware → Cartas**: las cartas responsivas y de devolución.
  - El filtro **Pendiente de firma** muestra las que aún no tienen la versión
    firmada.
  - Puedes **descargar** cualquier carta en español o en inglés con los
    botones **Descargar (español)** / **Descargar (inglés)**, y ver el **PDF
    firmado** cuando ya se subió.

---

## 5. Consultar software y licencias

### 5.1 Suscripciones

**Software → Suscripciones** — una por plataforma, plan y compañía.

En la lista ves, de cada suscripción: tipo de licencia, renovación
automática, licencias compradas, usuarios permitidos y asignados, fin del
periodo vigente, **costo del periodo vigente**, **último aumento de precio
(%)** y estatus:

| Estatus | Significado |
|---|---|
| **Activo** | Contrato vigente. |
| **Por renovar** | Se renueva sola y faltan 10 días o menos. |
| **Por vencer** | No se renueva sola y faltan 10 días o menos. |
| **Vencida** | Terminó y no se renovó. |
| **Cancelado** | Se dejó de usar. |
| **Sin periodo** | Aún no tiene costos registrados. |

Al abrir una suscripción:

- **Periodo vigente**: fechas, total, licencias, usuarios y el último aumento.
- **Periodos**: el historial de contratos, con el costo de cada año y el
  **% de cambio contra el periodo anterior**, en precio unitario y en total.
  Sirve para ver cuánto sube cada plataforma año con año.
- **Asignaciones**: quién tiene licencia (empleado o departamento, con su
  departamento), desde cuándo y hasta cuándo.
- **Analítica y justificación**: cómo se reparte el costo entre departamentos
  y por qué se contrató.

> 🔒 Las **claves de licencia** solo las ve TI.

### 5.2 Asignaciones de licencias

**Software → Asignaciones de licencias** — todas las licencias asignadas.

- Agrupa por **Empleado** para ver qué licencias tiene cada persona.
- Agrupa por **Departamento** para ver las licencias de cada área.
- El filtro **Por revisar** muestra licencias de personas dadas de baja que
  TI debe liberar.

### 5.3 Catálogo de software

**Software → Catálogo de software**: las plataformas que usa la empresa y, en
cada una, sus suscripciones en todas las compañías.

---

## 6. Costos y gasto

### Por equipo

Pestaña **Costos** de cada equipo:

- **Adquisición**: lo que costó comprarlo.
- **Mantenimiento**: sus mantenimientos preventivos y correctivos.
- **Garantía**: costos de sus servicios de garantía (envíos, deducibles).
- **Envíos**: lo que costó enviarlo por paquetería.
- **Costo total (USD)**.

El **Detalle** lista cada partida con su fecha, su monto en la moneda
original (MXN, USD, CLP, CRC) y su equivalente en USD con el **tipo de cambio
de esa fecha**.

### Del periodo (todos los equipos y software)

En el **Tablero**, ajusta **Desde / Hasta** y las **Compañías**, y revisa
**Gasto del periodo por concepto (USD)**.

### En listas

En **Hardware → Activos** puedes mostrar las columnas **Adquisición (USD)** y
**Costo total (USD)** con el ícono ⇄ al final de los encabezados de la lista.
Al **agrupar** (por compañía, categoría, departamento…) verás el subtotal de
cada grupo.

---

## 7. Búsquedas, filtros y exportar a Excel

- **Buscar**: escribe en la barra de búsqueda y elige en qué campo (ej. en
  *Activos*: etiqueta, número de serie, IMEI, empleado u orden de compra).
- **Filtros**: haz clic en la flecha ▾ del buscador. Por ejemplo:
  - *Activos*: por estatus, *Oficina* / *Home Office*, garantía, *Sin
    asignar*.
  - *Suscripciones*: *Por vencer*, *Excedente*, *Con aumento de precio*.
- **Agrupar por**: en el mismo menú (compañía, categoría, departamento,
  empleado…).
- **Exportar a Excel**: selecciona los registros (casilla de la izquierda o
  la de todos) → **Acción → Exportar** → elige las columnas → **Exportar**.
- **Guardar una búsqueda**: arma tus filtros y usa **Favoritos → Guardar
  búsqueda actual**, para no repetirla cada vez.

---

## 8. Preguntas frecuentes

**No encuentro un equipo.**
Revisa que tengas seleccionada su compañía (arriba a la derecha) y quita el
filtro *Activos vigentes* si podría estar dado de baja o extraviado.

**¿Por qué no puedo editar nada?**
Tu perfil es de consulta. Los cambios los hace TI, lo que garantiza que el
historial sea confiable.

**¿El "Valor de activos" incluye mantenimientos?**
No. Es el **costo de adquisición**. Mantenimientos, garantías y envíos están
en *Gasto del periodo por concepto* (tablero) y en la pestaña *Costos* de
cada equipo.

**¿Con qué tipo de cambio se convierte a USD?**
Con el tipo de cambio registrado en Odoo en la **fecha de cada gasto** (compra,
mantenimiento, envío o inicio del periodo de software).

**¿Cómo sé cuánto subió una licencia?**
Abre la suscripción → pestaña **Periodos**: cada periodo muestra su % de
cambio contra el anterior. En la lista de suscripciones, el filtro **Con
aumento de precio** te muestra todas las que subieron.

**Veo un dato incorrecto.**
Repórtalo a TI indicando la etiqueta del equipo o la suscripción.

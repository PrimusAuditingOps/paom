# Gestión de Activos de TI — Guía del Administrador

> **¿Para quién es esta guía?** Para el equipo de **TI**, que tiene el perfil
> **Administrador** del módulo. Con este perfil registras equipos y
> licencias, los asignas, los envías, les das mantenimiento, generas las cartas
> responsivas y mantienes los catálogos.
>
> Si solo necesitas **consultar** información (por ejemplo, Finanzas), usa la
> **Guía del Usuario**.

---

## Contenido

1. [Conceptos básicos](#1-conceptos-básicos)
2. [Primeros pasos: configuración inicial](#2-primeros-pasos-configuración-inicial)
3. [El Tablero](#3-el-tablero)
4. [Registrar un equipo (activo de hardware)](#4-registrar-un-equipo-activo-de-hardware)
5. [Movimientos: asignar, enviar, devolver, reparar y dar de baja](#5-movimientos-asignar-enviar-devolver-reparar-y-dar-de-baja)
6. [Cartas responsiva y de devolución](#6-cartas-responsiva-y-de-devolución)
7. [Mantenimiento y garantía](#7-mantenimiento-y-garantía)
8. [Software, suscripciones y licencias](#8-software-suscripciones-y-licencias)
9. [Costos](#9-costos)
10. [Búsquedas, filtros y reportes](#10-búsquedas-filtros-y-reportes)
11. [Reglas importantes del sistema](#11-reglas-importantes-del-sistema)
12. [Preguntas frecuentes](#12-preguntas-frecuentes)

---

## 1. Conceptos básicos

| Término | Qué significa |
|---|---|
| **Activo** | Un equipo físico: laptop, monitor, celular, access point, impresora… Cada uno tiene una **etiqueta de activo** única (ej. `LPT-MX-076`). |
| **Compañía** | La compañía (país) donde el equipo **está en uso**: México, USA, Chile o Costa Rica. Si el equipo se muda de país, cambia de compañía mediante un movimiento. |
| **Responsable** | A quién está asignado el equipo: **un empleado** o **un departamento** (nunca ambos). Ej.: una laptop a una persona; unos access points al departamento de TI. |
| **Estatus** | En qué situación está el equipo (ver tabla abajo). **Solo cambia con los botones de movimiento**, nunca a mano. |
| **Movimiento** | Cada cambio del equipo (asignación, envío, devolución, reparación, baja…). Queda en el **Historial** y no se puede modificar ni borrar. |
| **Suscripción** | Una plataforma de software contratada por una compañía (ej. *Google Workspace – Business Plus (Estados Unidos)*). |
| **Periodo** | Cada ciclo de contrato de una suscripción (normalmente un año), con su propio costo. |

### Estatus de un equipo

| Estatus | Significado |
|---|---|
| **Disponible** | En bodega o sin asignar; listo para asignarse. |
| **Asignado** | En uso por un empleado o departamento. |
| **En tránsito** | Enviado por paquetería, en camino a su nuevo responsable. |
| **En reparación** | Fuera de servicio por mantenimiento o garantía (conserva a su responsable). |
| **Dado de baja** | Retirado definitivamente (vendido, donado, desechado…). Es final. |
| **Extraviado / Robado** | Perdido o robado. Conserva a la última persona que lo tenía. Se puede **Recuperar** si aparece. |

### Menú del módulo

Entra a **Gestión de activos de TI** desde el menú principal de Odoo:

- **Tablero** — pantalla de inicio con indicadores y alertas.
- **Hardware** → Activos · Mantenimiento · Movimientos · Cartas
- **Software** → Suscripciones · Asignaciones de licencias · Catálogo de software
- **Configuración** → catálogos y documentos (solo administradores).

> 💡 **Selector de compañías.** Todo lo que ves depende de las compañías que
> tengas seleccionadas en el selector de compañías de Odoo (arriba a la
> derecha). Con las 4 seleccionadas ves todo; con solo México, solo México.

---

## 2. Primeros pasos: configuración inicial

Antes de registrar equipos, deja listos los catálogos. Todos están en
**Configuración**.

### 2.1 Catálogos de hardware (Configuración → Hardware)

| Catálogo | Qué capturar | Tip |
|---|---|---|
| **Categorías** | Tipos de equipo (Laptop, Monitor, Celular…). Ya vienen precargadas. | Marca **Requiere IMEI** en celulares y tabletas. Marca **Requiere mantenimiento preventivo** y la **Periodicidad preventiva (meses)** en las categorías que tengan plan preventivo (ver [sección 7](#7-mantenimiento-y-garantía)). |
| **Marcas** | Lenovo, HP, Dell, Samsung… | Dentro de cada marca puedes capturar sus modelos. |
| **Modelos** | ThinkBook 14 ITL, V14 G3 IAP… (cada uno ligado a su marca). | Al elegir una marca en un equipo, solo aparecen sus modelos. |
| **Ubicaciones** | Ciudad + estado + tipo (**Oficina** u **Home Office**) + compañía. | El nombre se arma solo: *Guadalajara, Jalisco – Oficina*. Crea una ubicación "Home Office" por ciudad donde haya personal remoto. |
| **Condiciones** | Buena, Normal, Mala, Descompuesta (precargadas). | Es el estado físico del equipo, independiente del estatus. |
| **Otros métodos de compra** | Amazon, Mercado Libre… | Para compras que no pasan por una orden de compra. |
| **Paqueterías** | DHL, FedEx, UPS, Estafeta (precargadas). | Se usan al enviar equipos. |
| **Motivos de baja** | Vendido, Donado, Desechado, Reciclaje electrónico, Obsoleto. | Se piden al dar de baja un equipo. |

### 2.2 Documentos (Configuración → Documentos)

- **Plantillas de cartas**: título y cláusulas de la **carta responsiva** y de
  la **carta de devolución**, en **inglés y español**. Es un texto **global**
  (igual para todos los países). Separa cada cláusula con una línea en blanco.
- **Control de documentos**: un renglón por compañía y tipo de carta con
  **código** (FTI-01 / FTI-02), **revisión**, **elaborado / revisado /
  aprobado por**, **edición original** y **fecha de emisión**. Aparecen en el
  pie de cada carta. Las compañías de México ya vienen llenas; completa las
  demás.

### 2.3 Software (Configuración → Software)

- **Tipos de software**: Productividad / Correo, Editor de PDF,
  Videoconferencia, Antivirus… (precargados).

### 2.4 Permisos de los usuarios

En **Ajustes → Usuarios**, en la sección *Gestión de activos de TI*:

- **Administrador** → equipo de TI.
- **Usuario** → Finanzas y cualquier persona que solo consulte.

---

## 3. El Tablero

Es la pantalla con la que abre el módulo (**Tablero**).

**Filtros (parte superior):**
- **Compañías**: botones con el país; activa o desactiva cada una (solo
  aparecen las que tienes seleccionadas en Odoo).
- **Desde / Hasta**: rango de fechas (por defecto, el año en curso).
- **Hardware / Software**: cambia la gráfica.

**Qué muestra:**

| Sección | Qué significa | ¿Le afecta el rango de fechas? |
|---|---|---|
| Activos vigentes | Equipos no dados de baja ni extraviados, contra el total. | No |
| Valor de activos (costo de adquisición) | Lo que costaron al comprarse los equipos vigentes, en USD. Los costos complementarios se ven en cada activo, pestaña **Costos**. | No |
| Compras del periodo | Monto (USD) y número de equipos comprados en el rango. | **Sí** |
| Gasto en software del periodo | Total de los periodos de suscripción que **inician** en el rango (USD). | **Sí** |
| Uso de licencias | Usuarios asignados / usuarios permitidos en las suscripciones vigentes. | No |
| Asignaciones por revisar · Preventivos vencidos · Envíos retrasados | Pendientes de atender. **Haz clic** para abrir la lista. | No |
| Gasto del periodo por concepto | Adquisiciones, Mantenimiento, Garantías, Envíos, Software y Total, en USD. | **Sí** |
| Gráfica | *Hardware*: valor por categoría. *Software*: gasto por tipo. | Software: sí |
| Alertas (calendario) | Mantenimientos programados, garantías que vencen, renovaciones/vencimientos de suscripciones y envíos en tránsito. Usa ‹ › para cambiar de mes; **haz clic** en un evento para abrirlo. | — |

> 💡 Revisa el tablero al inicio de la semana: los conteos en rojo y el
> calendario te dicen qué atender.

---

## 4. Registrar un equipo (activo de hardware)

**Hardware → Activos → Nuevo**

1. **Foto** (opcional): haz clic en el recuadro de imagen.
2. **Etiqueta de activo** (obligatoria y única): se guarda en mayúsculas y
   sin espacios.
3. **Identificación**: Categoría, Marca, Modelo, Condición.
4. **Ubicación y responsable**: **Compañía**, **Ubicación** y **Fecha de
   alta**.
   - La *Fecha de alta* es la fecha desde la que el equipo existe en el
     sistema. Para equipos antiguos pon su fecha real: ningún movimiento podrá
     ser anterior a ella.
   - ⚠️ **Compañía, ubicación y fecha de alta solo se capturan al crear el
     equipo.** Después cambian únicamente con movimientos.
5. Pestaña **Detalles**: Número de serie, Número de producto, **IMEI** (solo
   aparece en celulares y tabletas), **Especificaciones** (texto libre) y
   **Notas**.
6. Pestaña **Compra** — elige el **Origen de compra**:
   - **Orden de compra**: selecciona la **Orden de compra** y su **Línea**.
     Se llenan solos la fecha, el costo unitario **sin impuestos** y la
     moneda (puedes ajustarlos), y el **Proveedor** sale de la orden. Las
     **Facturas de proveedor** de esa línea aparecen solas, con su estado,
     aunque se registren después.
   - **Otro método de compra**: elige el método (Amazon, Mercado Libre…) y
     describe en **Detalles de pago** cómo se pagó (ej. *tarjeta corporativa
     terminación 1234*). Si ya existe la factura o la **póliza** de ajuste,
     lígala en **Factura de proveedor / Póliza**.
   - **Distribución analítica** (opcional): reparte el costo entre cuentas
     analíticas; si la capturas, cada plan debe sumar 100%.
7. Pestaña **Garantía**: Inicio y fin de garantía, Proveedor de garantía y
   cobertura. El estatus de garantía se calcula solo (*En garantía*,
   *Garantía por vencer* a 30 días, *Garantía vencida*).
8. Pestaña **Galería**: agrega fotos de evidencia (estado al recibir,
   daños…).
9. **Guarda**. El equipo queda **Disponible** y su primer renglón del
   historial (*Alta*) se crea solo.

---

## 5. Movimientos: asignar, enviar, devolver, reparar y dar de baja

Los movimientos se hacen con los **botones de la parte superior** del equipo.
Solo aparecen los que aplican a su estatus actual. Cada movimiento abre una
ventana, y al **Confirmar**:

- se registra un renglón en la pestaña **Historial** (antes → después, quién
  lo hizo y cuándo);
- se actualizan estatus, responsable, compañía y ubicación del equipo.

> 📅 **Fecha del movimiento**: puedes capturar una fecha pasada (para
> registrar algo que ya ocurrió), pero **nunca futura**, ni anterior al alta
> ni al último movimiento del equipo.

### 5.1 Asignar (equipo Disponible)

1. Botón **Asignar**.
2. **Asignar a**: **Empleado** o **Departamento**.
   - Los empleados y departamentos muestran su país entre paréntesis, por
     ejemplo *IT (México)*, para distinguir los que se repiten por compañía.
3. La **Compañía** se toma sola del empleado o departamento elegido.
4. **Ubicación** (ej. *Culiacán, Sinaloa – Home Office*).
5. ¿Hay que mandarlo por paquetería? Marca **Requiere envío** (ver 5.3).
6. **Cartas**: marca **Generar carta responsiva** y elige el **Idioma de la
   carta** (ver [sección 6](#6-cartas-responsiva-y-de-devolución)).
7. **Notas** y **Adjuntos** (opcional) → **Confirmar**.

> 💡 **Varios equipos a la vez**: en la lista de activos selecciona varios
> equipos *Disponibles* → menú **Acción → Asignar**. Se asignan todos al mismo
> responsable y, si lo pides, salen en **una sola carta responsiva**.

### 5.2 Reasignar (equipo Asignado)

Botón **Reasignar**: igual que Asignar, pero el equipo ya tenía responsable.

- **Entre países**: si reasignas a un empleado de otro país (ej. de USA a
  México), el equipo **cambia de compañía** automáticamente y el historial lo
  registra. Necesitas tener ambas compañías seleccionadas.
- **Cartas**: puedes marcar **ambas** casillas, la **responsiva** para el
  nuevo empleado y la **devolución** para el anterior.
- Si el equipo tiene **distribución analítica** y cambia de departamento,
  verás un aviso amarillo para revisarla (no bloquea).

### 5.3 Envíos (En tránsito)

Al asignar o reasignar con **Requiere envío**, captura:

- **Paquetería**, **Número de guía**, **Fecha de envío** y **Fecha estimada
  de entrega**;
- **Costo del envío** y su moneda (y, si la hay, **Factura / póliza del
  envío**);
- en **Adjuntos**, la guía en PDF.

El equipo queda **En tránsito**, ya con su nuevo responsable. Después:

- **Confirmar entrega** → el equipo pasa a **Asignado** (la fecha del
  movimiento es la fecha real de entrega).
- **Cancelar envío** (con motivo) → el equipo **vuelve exactamente a como
  estaba** antes de mandarlo (mismo responsable, compañía y ubicación).

> ⚠️ Si pasa la fecha estimada y no confirmas la entrega, el equipo aparece en
> **Envíos retrasados** del tablero.

### 5.4 Devolver (equipo Asignado)

Botón **Devolver** (o, para varios, **Acción → Devolver** desde la lista):

1. **Ubicación** donde queda el equipo (ej. bodega).
2. **Condición** en la que se recibe.
3. **Generar carta de devolución** (opcional) e idioma.
4. **Confirmar** → el equipo queda **Disponible** y sin responsable.

### 5.5 Reubicar

Botón **Reubicar**: cambia la **ubicación** sin cambiar de responsable (ej. de
una oficina a la bodega). Si el equipo está **Disponible**, también puedes
cambiarlo de **compañía** (ej. un equipo en bodega de USA que se lleva a la de
México).

### 5.6 Reparación

- **Enviar a reparación** (con motivo) → queda **En reparación**, conservando
  a su responsable.
- **Regreso de reparación** → vuelve al estatus que tenía antes; puedes
  actualizar la condición.

> 💡 Si la reparación se lleva como **mantenimiento** con *Sacar el activo de
> servicio*, estos dos movimientos se hacen solos (ver [sección 7](#7-mantenimiento-y-garantía)).

### 5.7 Dar de baja, extravío y recuperación

- **Dar de baja**: elige el **Motivo de baja** (y adjunta evidencia). El
  equipo queda **Dado de baja**, sin responsable. **Es definitivo.** Sus
  preventivos pendientes se cancelan solos.
- **Reportar extravío / robo** (con motivo; adjunta la denuncia si la hay):
  el equipo queda **Extraviado / Robado** y **conserva al empleado** que lo
  tenía.
- **Recuperar**: si un equipo extraviado aparece, vuelve a **Disponible**.

### 5.8 El Historial

Pestaña **Historial** del equipo: todos sus movimientos, del más reciente al
más antiguo, con fecha, **Hasta** (fin de ese periodo), estatus, responsable,
compañía, ubicación y quién lo hizo. Haz clic en un renglón para ver el
detalle (envío, motivo, adjuntos).

- Los movimientos **no se pueden editar ni borrar**. Solo puedes agregar
  **notas** y **adjuntos** después.
- **Hardware → Movimientos** muestra los movimientos de **todos** los
  equipos, con filtros como *Envíos*, *Envíos cancelados* y *Entre
  compañías*.

---

## 6. Cartas responsiva y de devolución

### 6.1 Generarlas

- **Al asignar / reasignar a un empleado** → casilla **Generar carta
  responsiva**.
- **Al devolver (o al reasignar)** → casilla **Generar carta de
  devolución**.
- **Para equipos que ya estaban asignados** (ej. los que se dieron de alta con
  la carga inicial): botón **Carta responsiva** del equipo, o selecciona
  varios equipos del **mismo empleado** en la lista → **Acción → Generar carta
  responsiva**.

En todos los casos eliges el **idioma** (inglés o español) y el PDF se
descarga al confirmar.

### 6.2 Qué contiene

- Encabezado con logo, código y título.
- Lugar y fecha, razón social y domicilio de la compañía.
- El párrafo con el **nombre del empleado** (y en la devolución, **tu
  nombre** como encargado de TI).
- La tabla de equipos (etiqueta, categoría, marca, modelo, especificaciones,
  serie y, en la devolución, **condición**).
- Las cláusulas, y las líneas de firma **Receptor** y **Otorgante** **sin
  nombres**: se firman a mano.
- En el pie, los datos del control de documentos y el número de página.

### 6.3 Subir la carta firmada

1. **Hardware → Cartas** (o, desde el equipo, pestaña **Historial** → sección
   **Cartas** → **Abrir cartas**).
2. Abre la carta.
3. En **Carta firmada** → **PDF firmado** → adjunta el archivo escaneado.
4. **Guarda**. El estatus pasa de *Pendiente de firma* a **Firmada**.

> 💡 Usa el filtro **Pendiente de firma** en *Hardware → Cartas* para
> perseguir las cartas sin firmar.
>
> 💡 Puedes **volver a descargar** cualquier carta en el otro idioma con
> **Descargar (español)** / **Descargar (inglés)**. Siempre sale igual,
> porque guarda los datos de los equipos del momento en que se generó.

---

## 7. Mantenimiento y garantía

### 7.1 Plan preventivo automático

1. En **Configuración → Hardware → Categorías**, marca **Requiere
   mantenimiento preventivo** y captura la **Periodicidad preventiva
   (meses)** (ej. 3 meses para laptops).
2. Odoo programa **solo** el siguiente preventivo de cada equipo
   **Disponible** o **Asignado** de esa categoría:
   - el primero, a *fecha de alta + N meses*;
   - al terminar uno, el siguiente a *fecha de fin + N meses*;
   - si **cancelas** uno, se salta ese ciclo y se programa el siguiente.
3. La fecha del próximo preventivo se ve en el equipo (**Próximo
   preventivo**) y en el calendario del tablero.

### 7.2 Registrar un mantenimiento

Desde el equipo, pestaña **Mantenimiento** → **Registrar mantenimiento**, o
desde **Hardware → Mantenimiento → Nuevo**:

- **Tipo**: **Preventivo**, **Correctivo** o **Garantía**.
- **Sacar el activo de servicio**: márcalo si el equipo deja de usarse
  mientras tanto (ej. se envía al proveedor). Al **Iniciar**, el equipo pasa
  a *En reparación*; al terminar o cancelar, regresa solo a su estatus
  anterior.
- **Fecha programada**, **Técnico** (empleado de TI) y/o **Proveedor**. En
  *Garantía*, el proveedor es **obligatorio** y puedes capturar el **Caso de
  garantía / No. RMA**.
- **Costo** y moneda, y **Factura de proveedor / Póliza**.
- Pestaña **Detalles**: *Descripción del problema* y *Trabajo realizado*.
- Pestaña **Envío**: si mandas el equipo a garantía por paquetería.
- Pestaña **Notas y adjuntos**: reportes técnicos, fotos, órdenes de
  servicio.

### 7.3 Flujo

**Programado → (Iniciar) → En curso → (Marcar como terminado) → Terminado**

- **Marcar como terminado** abre una ventana que pide la **fecha de fin**, la
  **condición final** del equipo y el trabajo realizado. Se puede usar desde
  *Programado* directamente (para preventivos rápidos).
- **Cancelar**: disponible en *Programado* y *En curso*.
- Un mantenimiento **terminado** ya no se edita; solo sus notas y adjuntos.

> 💡 En la pestaña *Mantenimiento* del equipo, la ventana que se abre al hacer
> clic en un renglón es solo de consulta. Para **editar**, usa **Abrir
> mantenimientos** o el menú *Hardware → Mantenimiento*.
>
> 💡 *Hardware → Mantenimiento* tiene vista de **calendario** y el filtro
> **Vencido** (preventivos cuya fecha ya pasó).

---

## 8. Software, suscripciones y licencias

### 8.1 Catálogo de software

**Software → Catálogo de software → Nuevo**: nombre (ej. *Google
Workspace*), tipo de software, fabricante y sitio web. Es **global** (se usa
en todas las compañías).

### 8.2 Crear una suscripción

**Software → Suscripciones → Nuevo** (una por software + plan + compañía):

- **Software**, **Plan / Edición** (ej. *Business Plus*) y **Compañía**.
- **Tipo de licencia**: *Por usuario*, *Tarifa fija* o *Perpetua*.
- **Renovación automática** y, opcionalmente, **Aumento esperado al renovar
  (%)**.
- Pestaña **Analítica y justificación**: distribución analítica por
  departamento (suma 100% por plan; actualízala cuando haya altas o bajas de
  personal), descripción y justificación.
- Pestaña **Claves de licencia**: códigos de activación. **Solo los ven los
  administradores.** ⚠️ **Nunca guardes contraseñas** aquí (usa LastPass).

### 8.3 Periodos (costos)

Pestaña **Periodos → Agregar una línea**:

- **Fecha de inicio / fin** (la de fin es opcional en licencias perpetuas),
  **No. de contrato** y **Frecuencia de cobro** (Mensual / Anual / Pago
  único).
- **Licencias compradas** y **Usuarios por licencia** (normalmente 1; en WPS,
  3). Los **Usuarios permitidos** se calculan solos (ej. 6 × 3 = 18).
- **Costo**:
  - *Por usuario*: captura el **Costo unitario**; el **Cargo por cobro** se
    calcula solo (costo unitario × licencias).
  - *Tarifa fija / Perpetua*: captura el **Cargo por cobro**.
  - El **Total del periodo** se calcula solo (cargo × número de cobros).
- **Compra**: por orden de compra (facturas automáticas) u otro método, igual
  que en los equipos.
- **Notas y contrato**: adjunta el contrato.
- **Cambio contra el periodo anterior**: el sistema muestra cuánto subió el
  precio unitario y el total, en monto y en %.

### 8.4 Renovaciones y cambios de precio

- **Renovar**: crea el siguiente periodo con las mismas cantidades y costo;
  ajústalo si cambió el precio.
- **Renovación automática**: el día que termina el periodo, Odoo crea solo el
  siguiente, aplicando el **aumento esperado** si lo capturaste.
- **Cambio de precio** (ícono 📈 en el renglón del periodo): si el proveedor
  sube el precio a mitad del periodo, indica la **fecha efectiva** y el
  **nuevo costo**. El periodo se divide en dos tramos, cada uno con su
  precio.

**Estatus de la suscripción:** *Activo* · *Por renovar* (con renovación
automática, faltan ≤ 10 días) · *Por vencer* (sin renovación automática,
faltan ≤ 10 días) · *Vencida* · *Cancelado* · *Sin periodo*.

### 8.5 Asignar licencias

Pestaña **Asignaciones → Agregar una línea**: elige **Empleado** o
**Departamento** y la **Fecha de inicio**. La columna *Departamento* muestra
el departamento del empleado en RR. HH.

- Para **quitar** una licencia, usa **Cerrar** (pone la fecha de fin). Las
  asignaciones **no se borran**, para conservar quién la tuvo y cuándo.
- Si asignas más usuarios de los permitidos, aparece un **aviso rojo de
  excedente** (no bloquea).
- Si un empleado se **da de baja** en RR. HH. (se archiva), sus licencias
  aparecen como **Por revisar**: ciérralas para liberarlas.

> 💡 **Software → Asignaciones de licencias** muestra todas las asignaciones:
> agrupa por *Empleado* para ver qué licencias tiene cada persona, o por
> *Departamento*.

### 8.6 Cancelar una suscripción

Botón **Cancelar suscripción**: indica fecha y motivo. Sus asignaciones
abiertas se cierran solas y sus periodos se conservan como historial de gasto.
Si fue un error, usa **Reactivar**.

---

## 9. Costos

Pestaña **Costos** de cada equipo:

- Totales en USD por concepto: **Adquisición**, **Mantenimiento**,
  **Garantía** y **Envíos**, más el **Costo total (USD)**.
- **Detalle** con cada partida: fecha, concepto, referencia, monto en su
  moneda original y equivalente en USD con el **tipo de cambio de su propia
  fecha**.

En la lista de activos puedes activar las columnas **Adquisición (USD)** y
**Costo total (USD)** (ícono ⇄ al final de los encabezados), con suma al pie.

---

## 10. Búsquedas, filtros y reportes

Todas las listas tienen **buscador**, **filtros** y **agrupar por**. Algunos
útiles:

| Lista | Filtros / agrupaciones útiles |
|---|---|
| **Activos** | Activos vigentes (por defecto) · por estatus · Oficina / Home Office · En garantía / Por vencer / Vencida · Sin asignar · agrupar por compañía, categoría, marca, ubicación, departamento o empleado. Busca por etiqueta, serie, IMEI, empleado u orden de compra. |
| **Mantenimiento** | Preventivo / Correctivo / Garantía · Vencido · Fuera de servicio · vista calendario. |
| **Movimientos** | Asignaciones · Devoluciones · Reparaciones · Envíos · Entre compañías · por fecha. |
| **Cartas** | Pendiente de firma · Firmada · Responsivas / Devoluciones. |
| **Suscripciones** | Por estatus · Renovación automática · Excedente · Asignaciones por revisar · Con aumento de precio · por tipo de licencia. |
| **Asignaciones de licencias** | Activas / Cerradas · Por revisar · agrupar por empleado o departamento. |

> 💡 **Exportar a Excel**: selecciona registros en cualquier lista → **Acción
> → Exportar**.
>
> 💡 **Guarda tus búsquedas**: arma los filtros y usa **Favoritos → Guardar
> búsqueda actual**.

---

## 11. Reglas importantes del sistema

- **Estatus, responsable, compañía y ubicación** de un equipo solo cambian con
  movimientos.
- **Los movimientos no se editan ni se borran** (solo notas y adjuntos). Un
  error se corrige con un movimiento nuevo.
- **Un equipo con movimientos no se puede borrar**: usa **Dar de baja**.
- **Dar de baja es definitivo**; *Extraviado / Robado* se puede recuperar.
- **Mantenimientos terminados** y **asignaciones de licencia cerradas** no se
  editan (solo notas).
- **Las cartas no se borran**: son parte del historial.
- **Nunca guardes contraseñas** en el módulo.

---

## 12. Preguntas frecuentes

**No veo un equipo / una suscripción.**
Revisa las compañías seleccionadas en Odoo (arriba a la derecha) y quita el
filtro *Activos vigentes* si buscas equipos dados de baja o extraviados.

**Me equivoqué en un movimiento.**
No se puede editar: registra un movimiento nuevo que lo corrija (ej. otra
reasignación) y explica el motivo en *Notas*.

**No aparece el botón que necesito.**
Los botones dependen del estatus del equipo. Ej.: *Confirmar entrega* solo
aparece *En tránsito*; *Recuperar*, solo en *Extraviado / Robado*.

**La carta sale "pendiente de firma".**
Súbela firmada desde *Hardware → Cartas* (ver 6.3).

**Quiero cambiar el texto de las cláusulas o la revisión del formato.**
*Configuración → Documentos → Plantillas de cartas* (texto) y *Control de
documentos* (código, revisión, firmas de control).

**El equipo sale sin preventivo programado.**
Revisa que su categoría tenga marcado *Requiere mantenimiento preventivo* y
que el equipo esté *Disponible* o *Asignado*.

**¿Por qué el valor del tablero no incluye mantenimientos?**
Porque la tarjeta *Valor de activos* es el **costo de adquisición**. El gasto
en mantenimiento, garantías y envíos aparece en *Gasto del periodo por
concepto* y en la pestaña *Costos* de cada equipo.

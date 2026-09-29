# pao_it_asset_management — Contexto del proyecto

> Léelo antes de tocar este módulo, junto con `ODOO_MODULE_DEVELOPMENT_GUIDE.md`
> en la raíz del repo. Aquí están las decisiones de alcance acordadas con el
> usuario (2026-09-24) y el estado de cada entregable. Si una decisión cambia,
> actualízala aquí.

## 1. Qué es

"IT Asset Management" (ITAM & SAM): registro, control y optimización de los
activos de TI de PAO dentro de Odoo 17: hardware, software, licencias y
suscripciones, con su ciclo de vida (compra → asignación → mantenimiento →
reasignación → devolución → baja) y su información financiera. Reemplaza a
AssetTiger y al Excel "IT Platforms Pricing - Savings plan".

**Fuera de esta fase (alcances complementarios futuros):**
- depreciación conectada a contabilidad;
- Odoo Sign;
- seguimiento del saving plan y de reemplazos de plataformas;
- cambios de plan de una suscripción.

Si llegan, van en **módulos complementarios** con el mismo ícono.

## 2. Decisiones base

- **Un solo módulo, sin satélites.** No agrega campos a `res.users`,
  `res.partner` ni `res.company` (ver la guía, punto 1). La configuración por
  país vive en modelos propios del módulo.
- **Todo en inglés + traducción completa `es_MX`**, a diferencia de los
  formularios OSP, que nunca se traducen.
- **Perfiles:**
  - **Administrator** (TI): hace todos los movimientos y administra los catálogos.
  - **User** (Finanzas): solo consulta, pero SÍ ve costos.
  - No hay portal para empleados.
- **Multi-compañía:** `company_id` es obligatorio en activos, ubicaciones y
  suscripciones. Cada usuario ve lo de las compañías que tiene activas en el
  selector (MX, USA, Chile, Costa Rica).
- **`company_id` = compañía donde el activo está EN USO** (no hay "compañía
  dueña"). Cambia al reasignar entre compañías, y el historial conserva la
  compañía anterior y la nueva.
- **Responsable:** un empleado (`hr.employee`) **o** un departamento
  (`hr.department`), nunca ambos. Ej.: access points asignados al
  departamento de TI.
- **Todo vive dentro del módulo:** no hay botones ni vistas en la ficha de
  empleado ni en otros módulos.
- **Empleados y departamentos con país** (decidido el 2026-09-28): PAO
  repite departamentos y empleados por compañía por control de gastos. Por
  ejemplo, hay un "IT" en USA y otro en MX, y una misma persona puede ser
  empleado en ambas. Dentro del módulo se muestran siempre como "IT
  (México)" o "Hector Cortes (Estados Unidos)", con el país de la compañía.
  - Se activa con la llave de contexto `pao_it_show_company`, que ponen las
    acciones del módulo y el asistente.
  - Está en `models/hr_company_label.py` y solo extiende
    `_compute_display_name`: sin campos ni columnas nuevas en
    `hr.department` / `hr.employee`.
  - Fuera del módulo, Odoo no cambia.
  - Ojo: para que la **lista desplegable** de un Many2one muestre el país, la
    llave debe ir en el `context` del propio campo en la vista. Con ponerla
    solo en el contexto de la acción, las pruebas del 2026-09-28 mostraron
    que no bastaba.

## 3. Hardware (entregable 1)

- **Estados** (fijos en código): Available, Assigned, In Transit, In Repair,
  Retired (final), Lost/Stolen (final; solo se sale con Recover → Available).
- **Asset Tag:**
  - lo captura el administrador;
  - obligatorio y único en todo el sistema;
  - se normaliza a MAYÚSCULAS y sin espacios;
  - no hay secuencia automática ni impresión de etiquetas.
- **Ubicación:** catálogo propio con ciudad, estado (`res.country.state`),
  tipo Office / Home Office y compañía obligatoria. `name` guarda "Ciudad,
  Estado", y el nombre visible agrega el tipo traducido. NO se reutiliza
  `pao_offices`, que son oficinas de clientes.
- **Especificaciones y notas:** dos campos de texto libre, iguales para
  cualquier tipo de equipo. No hay campos por categoría.
- **IMEI:** visible solo si la categoría tiene "Requires IMEI" (Mobile Phone,
  Tablet), pero NO es obligatorio (hay tablets solo Wi-Fi).
- **Compra:**
  - Registro manual; una PO NUNCA crea activos.
  - Origen `purchase_order`: se elige la PO y **su línea**. Se prellenan la
    fecha, la moneda y el **costo unitario sin impuestos**
    (`price_subtotal / product_qty`), todos editables. El proveedor es de
    solo lectura y siempre sale de la PO.
  - Origen `other`: catálogo "Other Purchase Method" (Amazon, Mercado Libre…)
    más texto libre de cómo se pagó. La captura libre nunca crea contactos.
  - Facturas con origen PO: se toman **automáticamente** de la línea de la PO
    (`purchase_move_ids`, calculado y no guardado). Se muestran **todas**
    (parciales y notas de crédito), en borrador o publicadas, con su estado;
    las canceladas no. Si la factura se crea después que el activo, aparece
    sola. Decidido con el usuario el 2026-09-25, tras su primera prueba: al
    principio era una liga manual.
  - Con origen `other`: liga **manual** opcional, capturable después, a
    `account.move`, factura de proveedor O póliza (hay compras con tarjeta
    que se solventan con pólizas de ajuste).
- **Accesos de Finanzas:** si un usuario no tiene acceso a Compras o a
  Contabilidad, la vista le muestra `purchase_order_ref` /
  `account_move_ref` (related guardados) en lugar del Many2one, para no
  provocar errores de acceso.
- **Garantía:** inicio, fin, proveedor y notas. Estatus calculado: none /
  active / expiring (≤ 30 días) / expired.
- **Galería:** modelo `pao.it.asset.image`. Las fotos de mantenimientos NO se
  copian aquí.
- **Condición** (Good, Normal, Bad, Broken): catálogo, independiente del
  estatus.
- **Borrado de activos:** permitido al administrador en el entregable 1. A
  partir del entregable 2, solo si no tiene movimientos más allá del alta;
  en los demás casos se usa Retire.

## 4. Movimientos e historial (entregable 2)

- El estatus, el responsable, la compañía y la ubicación solo cambian con
  **botones de acción** (wizards). Cada acción crea una línea de historial
  propia; no se depende del chatter.
- **Tipos:**
  - Register (automático al crear)
  - Assign
  - Reassign (puede cambiar de compañía)
  - Relocate
  - Ship → Confirm Delivery (confirmación manual)
  - Return (de varios activos a la vez)
  - Send to Repair → Back from Repair (regresa al estatus previo)
  - Retire (motivo de catálogo, con evidencia)
  - Report Lost/Stolen
  - Recover
- **Cada línea guarda:**
  - fecha efectiva (puede ser pasada, nunca futura) y fecha de captura;
  - tipo de movimiento;
  - antes → después de: estatus, empleado o departamento, compañía,
    ubicación y condición;
  - usuario que lo generó;
  - notas, adjuntos y periodo desde/hasta calculado.
- **Inalterable:** nadie puede editar ni borrar una línea, ni un admin.
  Solo las notas se pueden modificar.
- **Envío (In Transit):**
  - paquetería (catálogo propio; no se usa `pao_shippers`) y número de guía;
  - fechas de envío, estimada de entrega y real de entrega;
  - guía adjunta;
  - **costo y moneda** del envío;
  - liga opcional a `account.move`.
- **Distribución analítica** en el activo: opcional, debe sumar 100% y solo
  se conserva la vigente. Al reasignar a otro departamento se muestra un
  aviso para revisarla (no bloquea).
- No hay préstamos ni fecha de devolución esperada.
- Los adjuntos de cada movimiento se consultan en el detalle del movimiento
  (pestaña History o menú Movements). Se DESCARTÓ un botón "Documents" que
  concentrara todos los adjuntos del activo (decisión del usuario,
  2026-09-28).
- **Decisiones del diseño técnico (2026-09-25):**
  - Campo **Registration Date** en el activo: por defecto hoy y editable al
    crearlo. Es la fecha del movimiento Register, y ningún movimiento puede
    ser anterior a ella (necesario para la carga inicial con fechas reales).
  - **Relocate** puede cambiar de compañía SOLO si el activo está Available.
    Si está asignado, la compañía la manda el responsable.
  - **Report Lost/Stolen CONSERVA al empleado** en el activo. Recover lo
    libera (→ Available). Retire sí libera al responsable.
  - **Envío cancelado (Cancel Shipment):** un movimiento propio desde In
    Transit, con motivo, que deja asentado que fue por cancelación del
    envío. **Deshace el envío**: el activo vuelve exactamente a como estaba
    antes de mandarlo (estatus, responsable, compañía y ubicación, tomados
    del "antes" de la línea del envío). Tras un Assign vuelve a Available;
    tras un Reassign, al responsable anterior.
  - Assign y Return se pueden hacer sobre varios activos a la vez.
  - Solo se puede borrar un activo si no tiene más movimientos que el
    Register.
  - Los usuarios de TI y Finanzas tienen el permiso de Contabilidad
    analítica.

## 5. Mantenimiento y garantía (entregable 3)

- **Modelo propio**, no el módulo nativo `maintenance`.
- **Tipos:** Preventive, Corrective, Warranty.
- **Estatus:** Scheduled → In Progress → Done / Cancelled.
- **Campos:**
  - fechas programada, de inicio y de fin;
  - realizado por (empleado de TI) o proveedor (`res.partner`);
  - descripción del problema y trabajo realizado;
  - costo y moneda, con liga opcional a `account.move`;
  - número de caso RMA;
  - condición al terminar;
  - adjuntos propios;
  - datos de envío.
- **"Take asset out of service":** al iniciar genera Send to Repair; al
  terminar, Back from Repair.
- **Plan preventivo:**
  - La categoría define "Requires preventive maintenance" y la
    periodicidad en meses. Correctivo y garantía se pueden registrar en
    cualquier activo.
  - La próxima fecha es el último preventivo Done + N meses; si no hay
    ninguno, se cuenta desde el alta o la compra.
  - Se crea solo el siguiente preventivo en Scheduled.
  - Entran al plan los activos Available y Assigned.
  - Un cambio de periodicidad aplica solo a los preventivos siguientes.
  - Al pasar a Retired o Lost se cancelan los pendientes.
- Un mantenimiento Done queda inalterable, salvo las notas y los adjuntos.
- **Decisiones del diseño técnico (2026-09-28):**
  - Referencia automática `MNT/<año>/0001`.
  - El primer preventivo de un activo sin historial se cuenta desde la
    **fecha de alta**, no desde la compra.
  - Cancelar un mantenimiento en curso "fuera de servicio" genera
    automáticamente el Back from Repair.
  - Base del plan: la fecha más reciente entre el fin del último preventivo
    Done, la fecha programada del último preventivo cancelado (cancelar
    "salta" ese ciclo) y la fecha de alta, + N meses. Una tarea diaria
    asegura un preventivo pendiente por activo Available/Assigned de las
    categorías con preventivo.
  - Los movimientos Send to Repair / Back from Repair generados por un
    mantenimiento pasan por el mismo asistente del entregable 2 y quedan
    ligados al mantenimiento.
  - La columna "Compañía (después)" del historial se queda así (el usuario
    descartó cambiarla).

## 6. Software y licencias (entregable 4)

- **Software:** catálogo GLOBAL (sin compañía). **Suscripción:** por
  compañía.
- **Suscripción:**
  - tipo de licencia: Per user, Flat fee, Perpetual;
  - auto-renew;
  - tipo de software;
  - distribución analítica opcional (debe sumar 100%, solo la vigente);
  - claves de licencia visibles SOLO para el Administrator (restricción a
    nivel de campo, sin tracking);
  - NUNCA se guardan contraseñas (usan LastPass).
- **Periodo** = ciclo de contrato (normalmente anual), y también es el
  contrato (Contract No. + adjunto):
  - frecuencia de cobro mensual o anual;
  - "Licenses purchased" (base del costo) y "Allowed users" (capacidad),
    independientes; allowed se prellena con purchased (WPS: 6 → 18);
  - costo en la moneda real de cobro;
  - compra por PO u otro método;
  - liga a `account.move`.
- **Estatus:** Active, Expiring soon (10 días), Expired, Cancelled. Con
  auto-renew se avisa de la renovación en lugar del vencimiento.
- **Decisiones del diseño técnico (2026-09-28):**
  - **Auto-renew:** una tarea diaria crea el siguiente periodo al llegar la
    fecha de fin (copia cantidades y costo); el admin ajusta después. Una
    suscripción con auto-renew nunca queda vencida.
  - **Estatus:** Active, Renewing Soon (auto-renew, ≤ 10 días), Expiring
    Soon (sin auto-renew, ≤ 10 días), Expired, Cancelled y No Period.
  - **Costo:** Per user = costo unitario × licencias compradas por cobro;
    Flat fee = cargo por cobro capturado; Perpetual = pago único. Total del
    periodo = cargo × número de cobros (calculado, nunca a mano).
  - **Perpetual:** la fecha de fin es opcional y queda Active salvo que se
    cancele.
  - **Aumentos de precio** (las licencias suben año con año):
    - Cada periodo muestra su **variación contra el periodo anterior**,
      unitaria y total, en monto y en %, solo si ambos están en la misma
      moneda. La suscripción muestra el "último aumento", con filtro.
    - **Price Change:** parte un periodo en la fecha efectiva de un cambio
      de precio a mitad del periodo.
    - **"Aumento esperado al renovar (%)"** (opcional) en la suscripción: la
      renovación automática lo aplica al costo del nuevo periodo.
  - Al cancelar una suscripción se cierran sus asignaciones abiertas con la
    fecha de cancelación.
  - **Ajustes tras las pruebas (2026-09-28):**
    - **Usuarios por licencia:** el periodo captura licencias compradas y
      **usuarios por licencia** (por defecto 1). Usuarios permitidos se
      CALCULA: compradas × usuarios por licencia (WPS 6 × 3 = 18). Esto
      reemplaza el total capturado a mano. La función
      `_migrate_users_per_license` (en cada actualización) convierte los
      periodos capturados con el esquema anterior cuando la división es
      exacta.
    - **Departamento del responsable** (`effective_department_id`, guardado)
      en las asignaciones: el departamento del empleado en RR. HH., o el
      asignado directamente. Es una sola columna en la pestaña de la
      suscripción (solo lectura en renglones de empleado) y sirve para
      agrupar y filtrar.
- **Asignaciones:**
  - opcionales, a un empleado o a un departamento;
  - al quitarse se cierran con fecha de fin (no se borran);
  - si se excede la capacidad, solo se ADVIERTE;
  - si se archiva un empleado, sus asignaciones se marcan para revisión.

## 7. Responsiva y devolución (entregable 5)

- **Dos documentos controlados independientes**, con datos editables por
  país (código, título, revisión, elaborado/revisado/aprobado, fechas).
  Valores por defecto:
  - "FTI-01 Carta Responsiva de Equipo de Cómputo";
  - "FTI-02 Carta de Devolución de Equipo de Cómputo".
- El sistema **pregunta el idioma** (EN / ES) al generar.
- **Tabla:** Asset Tag, Category, Brand, Model, Specifications, Serial No.
  La devolución agrega **Condition**.
- **Nombres:**
  - Párrafo de la responsiva: incluye el nombre del empleado.
  - Párrafo de la devolución: incluye el nombre del empleado y el del
    administrador que descarga la carta. Dice "en las condiciones descritas
    en la tabla".
  - Líneas de firma "Receptor" y "Otorgante": SIN nombres.
- **Roles:** en la devolución se invierten (receptor = TI, otorgante =
  empleado).
- **Cláusulas:** un solo texto global en EN/ES.
- **Firma:**
  - no se usa Odoo Sign; se firma aparte;
  - en el historial queda el registro de la carta generada, donde se sube
    el PDF firmado;
  - el PDF en blanco no se guarda.
- Solo aplica a asignaciones a empleados. Una carta agrupa varios activos.
- **Decisiones del diseño técnico (2026-09-28):**
  - **Plantilla global editable** por tipo (Responsiva / Devolución): título
    y cláusulas en EN y ES. **Control del documento por compañía**: código,
    revisión, elaborado/revisado/aprobado, edición original y emisión.
  - **Otorgante = nombre de la compañía** (`res.company.name`), no un
    nombre corto.
  - **Lugar:** ubicación del primer activo; si no hay, la ciudad de la
    compañía.
  - **Papel:** el formato de papel configurado en cada compañía (A4 / Letter).
  - **Reasignación:** ofrece dos casillas opcionales, responsiva para el
    nuevo empleado y devolución para el anterior.
  - Cada carta es un registro (`pao.it.asset.letter`) con renglones que
    guardan una **foto** de los datos de cada activo al generarla, para que
    el PDF regenerado sea siempre idéntico. El PDF en blanco no se guarda;
    el firmado se sube al registro (estatus Pendiente de firma / Firmada).
  - Los textos fijos del PDF (párrafos, encabezados de tabla, pie) salen de
    un diccionario Python por idioma y no del `.po`. Así el PDF sale en el
    idioma elegido sin depender de cómo Odoo parte los términos de un
    reporte QWeb.

## 8. Costos y tablero (entregable 6)

- **Costo total por activo** con desglose (Acquisition, Maintenance,
  Warranty, Shipping), cada concepto en su moneda original, con el total en
  **USD a tipo de cambio histórico**. Los tipos se actualizan a diario en
  los 4 países.
- **Tablero** (pantalla de inicio):
  - **Tarjetas:** activos activos/total, valor en USD, compras del periodo,
    gasto en software, uso de licencias.
  - **Conteos:** asignaciones por revisar, preventivos vencidos, envíos
    retrasados.
  - **Calendario de alertas:** Maintenance Due, Warranty Expiring (30 d),
    Subscription Renewal/Expiring (10 d), In Transit (fecha estimada).
  - **Gráfica:** valor por categoría.
  - **Filtros:** compañía o país (solo entre las activas), rango de fechas
    (por defecto el año en curso) y Hardware/Software.
  - El rango de fechas solo afecta compras, gasto en software y la gráfica
    de software.
- Sin notificaciones por correo por ahora. Finanzas ve el mismo tablero.
- **Decisiones del diseño técnico (2026-09-28):**
  - "Valor de activos" = **costo de adquisición** de los activos vigentes,
    con una leyenda que lo aclara y remite a la pestaña Costs del activo
    para los costos complementarios.
  - **Gasto en software del periodo = por fecha de INICIO del periodo**
    (el total completo cuenta en el año en que inicia, como en el Excel).
  - Sección **"Gasto del periodo por concepto"** (petición del usuario), en
    USD y sobre todos los activos del rango: Adquisiciones (fecha de
    compra), Mantenimiento y Garantías (fecha de fin → inicio → programada;
    se excluyen los cancelados), Envíos (fecha de envío → fecha del
    movimiento; incluye los envíos de mantenimientos), Software (inicio
    del periodo) y Total.
  - El costo total del activo se guarda por concepto en USD (tipo de
    cambio histórico de la fecha de cada partida). El detalle se ve en la
    pestaña Costs.
  - Tablero hecho con OWL (acción cliente), sin librerías externas: la
    gráfica es un SVG propio y el calendario una cuadrícula propia. Las
    etiquetas llegan ya traducidas desde Python (sin traducciones en JS).

## 9. Estado de entregables

| # | Entregable | Estado |
|---|---|---|
| 1 | Base y hardware | **Probado y funcionando en staging (2026-09-25)**, incluido el ajuste de facturas automáticas desde la PO |
| 2 | Movimientos e historial | **Probado y funcionando en staging (2026-09-28)**, incluido el país en empleados y departamentos |
| 3 | Mantenimiento y garantía | **Probado y funcionando en staging (2026-09-28)**. "Marcar como terminado" abre una ventana (fecha de fin, condición, trabajo realizado) para que funcione también desde la pestaña de solo lectura del activo |
| 4 | Software y licencias | **Probado y funcionando en staging (2026-09-28)**, con usuarios por licencia y departamento del responsable |
| 5 | Responsiva y devolución | **Probado y funcionando en staging (2026-09-28)**. El PDF firmado se sube desde el registro de la carta (menú Cartas / "Abrir cartas"), no desde la lista de solo lectura del activo |
| 6 | Costos y tablero | **Programado (2026-09-28), pendiente de pruebas del usuario** |

- **Carga inicial** (AssetTiger + Excel de suscripciones): pospuesta hasta
  después de las pruebas funcionales del usuario.
- La versión del manifest NO se sube en cada entrega; la decide el usuario al
  liberar (guía, punto 2).
- La traducción `i18n/es_MX.po` se escribe a mano (no hay Odoo local). Al
  probar en staging hay que revisar la interfaz en español; si falta algo,
  exportar la traducción desde Odoo y completarla.

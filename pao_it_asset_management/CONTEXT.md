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
  - Liga opcional, capturable después, a `account.move`: factura de
    proveedor O póliza (hay compras con tarjeta que se solventan con pólizas
    de ajuste).
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
- Un mantenimiento Done queda inalterable, salvo las notas.

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

## 9. Estado de entregables

| # | Entregable | Estado |
|---|---|---|
| 1 | Base y hardware | **Programado (2026-09-24), pendiente de pruebas del usuario** |
| 2 | Movimientos e historial | Pendiente |
| 3 | Mantenimiento y garantía | Pendiente |
| 4 | Software y licencias | Pendiente |
| 5 | Responsiva y devolución | Pendiente |
| 6 | Costos y tablero | Pendiente |

- **Carga inicial** (AssetTiger + Excel de suscripciones): pospuesta hasta
  después de las pruebas funcionales del usuario.
- La versión del manifest NO se sube en cada entrega; la decide el usuario al
  liberar (guía, punto 2).
- La traducción `i18n/es_MX.po` se escribe a mano (no hay Odoo local). Al
  probar en staging hay que revisar la interfaz en español; si falta algo,
  exportar la traducción desde Odoo y completarla.

# pao_addenda — contexto

Primera etapa: Addenda CFDI **solo para Hortifrut** (compañía PRIMUS AUDITING
OPERATIONS MEXICO). Hortifrut exige, desde el 26-oct-2026, el folio de su orden
de compra en el XML de cada factura. La etapa 2 (addendas genéricas para otros
clientes) queda fuera; el campo tiene nombre neutral (`pao_po_number`) para no
tener que migrarlo entonces.

## Decisiones acordadas

| Tema | Decisión |
|---|---|
| Dónde se guarda el folio | En cada factura (`account.move.pao_po_number`, `Char`), nunca en el contacto |
| Formato del folio | **Exactamente 10 dígitos numéricos** (requisito de Hortifrut, 27-oct-2026: con más o menos no lo pueden procesar). Se valida al guardar (`@api.constrains`), al confirmar y antes de timbrar. Se ignoran espacios al inicio/final. `Char` y no numérico para conservar ceros iniciales |
| Quién es "Hortifrut" | Contacto cuya addenda (Ventas y compras) es **esta** addenda (`pao_addenda.addenda_hortifrut`). Se revisa `partner_id` y luego `commercial_partner_id`, igual que `l10n_mx_edi`. Sin IDs ni RFC en el código |
| Fecha límite | No se valida fecha: si el contacto tiene la addenda, el folio siempre es obligatorio |
| Cuándo se bloquea | Al confirmar (`_post`) y antes de timbrar (`_l10n_mx_edi_cfdi_check_invoice_config`) |
| Tipos de documento | Solo facturas de ingreso (`out_invoice`). Notas de crédito y complementos de pago: sin addenda |
| Folio tras timbrar | Solo lectura en estados `sent` / `cancel_requested`. Tras cancelar vuelve a ser editable |
| Al duplicar / revertir | El folio no se copia (`copy=False`) |
| Historial | Cambios del folio quedan en el chatter (`tracking=True`) |
| Asignación al contacto | Manual (no hay XML ID estable del contacto entre staging y producción) |
| Estructura XML | `<ClienteAdicional><OrdenCompra>…</OrdenCompra></ClienteAdicional>`, sin namespace. Tomada de la imagen de referencia de otra empresa: **pendiente de confirmar con Hortifrut** |
| Pruebas automáticas | No en esta etapa (riesgo de tumbar el build de Odoo.sh); lista manual abajo |

## Cómo funciona (código nativo revisado: enterprise `de773a5`, 16-oct-2026)

- `l10n_mx_edi/models/account_move.py:1776` — en `on_success` de
  `_l10n_mx_edi_cfdi_invoice_try_send`, **después** de que el PAC timbra, toma
  `partner_id.l10n_mx_edi_addenda or commercial_partner_id.l10n_mx_edi_addenda`
  y llama `_l10n_mx_edi_cfdi_invoice_append_addenda`. La addenda no forma parte
  del sello: no puede alterar impuestos, sello, UUID ni timbre.
- `:248` — la plantilla recibe `{'record': factura, 'cfdi': xml}`.
- `:251` — si la plantilla renderiza vacío, no se agrega addenda. La plantilla
  usa esto para no emitir nada en notas de crédito o sin folio.
- `:258-262` — si el nodo raíz no es `cfdi:Addenda`, Odoo lo envuelve.
- `:937` — `_l10n_mx_edi_cfdi_check_invoice_config` devuelve una lista de
  errores; `try_send` los muestra como fallo del documento sin llamar al PAC.
- `l10n_mx_edi/views/ir_ui_view.xml:12` — Odoo **ya** muestra
  `l10n_mx_edi_addenda_flag` en el formulario de vistas (solo `base.group_system`).
  Por eso el módulo no agrega vista heredada para ese campo.

## Archivos

- `models/account_move.py` — campo, campo calculado `pao_addenda_requires_po`
  (no almacenado; controla pestaña y validaciones), validación en `_post` y en
  `_l10n_mx_edi_cfdi_check_invoice_config`.
- `data/addenda_hortifrut.xml` — plantilla QWeb marcada como addenda.
- `views/account_move_views.xml` — pestaña "Información de Addenda" (al final
  del notebook; solo visible si aplica).

## Instalación en staging (Odoo.sh)

1. Push a `staging/17.0`; esperar el build.
2. Apps → actualizar lista → instalar **PAO Addenda**.
3. Contacto **HORTIFRUT** (id 23464 en staging) → Ventas y compras → Addenda:
   cambiar "Addenda de prueba" por **"Addenda Hortifrut"**. Sus contactos hijos
   heredan la addenda; no hay que asignarla en ellos.
4. Hacer las pruebas de abajo.
5. Archivar la vista "Addenda de prueba" (id 6374 en staging).
6. Restaurar la vista estándar `base.view_view_form` (id 74), editada a mano
   para mostrar `l10n_mx_edi_addenda_flag`: modo desarrollador → Ajustes →
   Técnico → Vistas → `ir.ui.view form` → restablecer arquitectura. Revisar
   antes cómo quedó; el campo seguirá visible para administradores gracias a
   `l10n_mx_edi.view_l10n_mx_edi_ir_ui_view_form_inherit`.

## Pruebas manuales en staging

1. Factura a HORTIFRUT con folio `4501312302` → confirmar → timbrar: el XML
   tiene `<cfdi:Addenda><ClienteAdicional><OrdenCompra>4501312302</OrdenCompra>…`
   al final, después de `cfdi:Complemento`.
2. Factura a HORTIFRUT sin folio → Confirmar: mensaje de error, no se confirma.
3. Factura a un hijo de HORTIFRUT (ej. "Hortifrut SA de CV, Ana Miranda"):
   aparece la pestaña y se exige folio.
4. Factura a otro cliente: no aparece la pestaña, no se exige folio, XML sin addenda.
5. Formato del folio en una factura Hortifrut:
   - `450131230` (9 dígitos), `45013123021` (11) y `OC-4501312` → error al guardar.
   - `0000450130` (10 con ceros iniciales) → se guarda y sale exacto en el XML.
   - ` 4501312302 ` (con espacios) → se acepta; el XML lleva `4501312302`.
6. Guardar, cerrar, reabrir: el folio persiste.
7. Factura timbrada: el folio queda de solo lectura.
8. Nota de crédito de una factura Hortifrut: no lleva addenda, no pide folio,
   no copia el folio.
9. Duplicar una factura Hortifrut: el duplicado sale sin folio.
10. Factura Hortifrut confirmada **antes** de instalar el módulo (o antes de la
    regla de 10 dígitos), sin folio o con folio inválido → timbrar: falla con
    el mensaje en el documento, sin llamar al PAC.
11. Revisar en el XML que impuestos, sello, UUID y `tfd:TimbreFiscalDigital`
    estén normales.
12. Actualizar el módulo (`-u pao_addenda`) y confirmar que nada cambia.

## Reversión

- **Sin perder datos:** quitar la addenda del contacto HORTIFRUT. La pestaña
  desaparece, no se exige folio y no se genera addenda. Los folios capturados
  se conservan.
- **Desinstalar el módulo:** borra la columna `pao_po_number` y con ella
  **todos los folios capturados**, y elimina la plantilla (el contacto queda
  sin addenda). Solo si de verdad se quiere retirar todo.

## Notas y pendientes

- **Estructura XML:** el XML de ejemplo de staging funcionó (confirmado por el
  usuario el 27-oct-2026).
- **Contactos de correo sueltos** (`aprado@hortifrut.com`, `jvaldez@hortifrut.com`,
  …) no tienen padre: una factura a ellos no lleva addenda ni pide folio. Si se
  usan para facturar, ligarlos a HORTIFRUT.
- **Confirmación automática:** si alguna vez una factura de Hortifrut se confirma
  por cron (publicación automática), el bloqueo en `_post` haría fallar ese lote.
- El bloqueo del folio tras timbrar es solo de interfaz (atributo `readonly` en
  la vista).

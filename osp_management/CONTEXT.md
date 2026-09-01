# Contexto del proyecto: `osp_management` (Odoo 17)

Este documento resume el contexto de negocio y técnico acumulado hasta ahora, para que puedas continuar el desarrollo sin perder el hilo de las decisiones ya tomadas.

## 1. Qué es esto (contexto de negocio)

Primus Auditing Ops certifica operaciones orgánicas (NOP/USDA). Antes de cotizar un servicio, el cliente debe llenar un **Organic System Plan (OSP)** — hoy es un documento de Word larguísimo (21 páginas, 20 secciones). El objetivo es **digitalizarlo**:

1. El **usuario de portal** (cliente externo) llena el formulario en línea, sección por sección, dentro de su portal de Odoo.
2. Puede guardar avance parcial cuantas veces quiera ("Save progress", estado `draft`) — el formulario es largo y no se llena de una sentada.
3. Cuando termina, presiona **Submit** → el registro pasa a estado `submitted` y se vuelve visible para el administrador interno. El cliente puede seguir haciendo Submit varias veces sobre el mismo registro (actualiza, no duplica) hasta que quede satisfecho o el proceso avance.
4. Una vez `submitted`, el formulario queda **de solo lectura para el cliente**.
5. El **Administrador de OSP** (usuario interno de Odoo, módulo backend "Administración de OSP") solo ve en su lista los registros ya `submitted`. Revisa la información y marca `review_status` como `done`/`pending` (esto es independiente del estado `draft`/`submitted`, y por ahora no bloquea edición).

Hay varios **tipos de formulario** (catálogo `osp.form.template`, campo `technical_code`). El primero y único construido hasta ahora es **"Crop"** (`form_crop`). Puede haber más tipos en el futuro (ej. "Handler") con su propia plantilla web.

## 2. Estructura del módulo

```
osp_management/
├── __manifest__.py
├── controllers/
│   └── portal.py          # Rutas del portal de cliente (/my/osp/...)
├── data/
│   ├── osp_service_data.xml        # Seed de Catálogo de Servicios (noupdate="1")
│   └── osp_form_template_data.xml  # Seed de Catálogo de Formularios (noupdate="1")
├── models/
│   ├── osp_request.py     # Modelo principal: el "expediente" de cada solicitud
│   └── osp_form_template.py
├── security/
│   ├── osp_security.xml   # Grupo "Administrador de OSP"
│   └── ir.model.access.csv
├── views/
│   ├── osp_menu_views.xml       # Vistas backend (lista/form) para el admin
│   ├── osp_portal_templates.xml # Lista de formularios del cliente (/my/osp)
│   ├── osp_form_crop.xml        # FORMULARIO "CROP" (QWeb) — body compartido + wrappers portal/público
│   ├── osp_form_handler.xml     # FORMULARIO "HANDLER" (QWeb) — mismo patrón que Crop
│   ├── osp_form_handler_trader.xml # FORMULARIO "HANDLER (TRADER)" (QWeb) — mismo patrón
│   └── osp_public_templates.xml # Pantalla de "Gracias" del formulario público
├── report/
│   ├── osp_report_common.py            # MOTOR GENÉRICO: _resolve_report_sections() + get_report_sections() (despacha por technical_code)
│   ├── osp_crop_report_data.py         # Manifest de las ~300 preguntas del PDF de Crop (sección, key, label, tipo)
│   ├── osp_crop_report.py              # get_crop_report_sections() — una línea, llama al motor común
│   ├── osp_handler_report_data.py      # Manifest de las preguntas del PDF de Handler
│   ├── osp_handler_report.py           # get_handler_report_sections() — una línea, llama al motor común
│   ├── osp_handler_trader_report_data.py # Manifest de las preguntas del PDF de Handler (Trader)
│   ├── osp_handler_trader_report.py    # get_handler_trader_report_sections() — una línea, llama al motor común
│   └── osp_report_templates.xml        # Template QWeb GENÉRICO del PDF + ir.actions.report (sirve a cualquier formulario)
└── static/src/
    ├── js/osp_form.js       # Lógica JS del formulario Crop (tablas dinámicas, guardado AJAX/localStorage)
    └── img/primus_logo.png  # Logo de marca (formulario web + encabezado del PDF)
```

## 3. Modelo de datos clave

**`osp.request`** — un registro por solicitud/expediente:
- `partner_id` — el cliente (portal)
- `service_id` (→ `osp.service`), `form_template_id` (→ `osp.form.template`)
- `state`: `draft` / `submitted`
- `review_status`: `pending` / `done` (marca interna del admin, independiente de `state`)
- **Campos "resumen"** (se muestran en la lista del admin, hoy se llenan por sincronización automática desde la Sección 1 del formulario — ver punto 5): `organization_name`, `dba_name` (ojo: su label en español es "Sitio", no "DBA"), `city`, `state_id` (Many2one a `res.country.state`), `zip_code`, `country_id` (Many2one a `res.country`)
- `form_data` — campo `fields.Json` (nativo Odoo 17) donde vive **todo** lo que el cliente contesta en el formulario, como diccionario plano `{clave: valor}`. No hace falta `json.loads`/`json.dumps` manual, Odoo lo maneja como dict directamente.

**`osp.service`** y **`osp.form.template`** — catálogos simples de configuración.

## 4. El patrón de "tabla dinámica" (MUY IMPORTANTE)

El formulario PDF original tiene **9 tablas de filas dinámicas** (agregar/quitar fila con inputs mixtos: texto, selects, checkboxes) repartidas en distintas secciones:

| Sección | Tabla | Estado |
|---|---|---|
| 1j | Authorized Contacts (Name/Email/Phone) | ⏳ Pendiente |
| **4g** | **Sites** (Site ID, Address, City/State, Zip, Contact, Description) | ✅ **Construida y funcionando** |
| 4h | Fields | ⏳ Pendiente |
| 4j | Crops | ⏳ Pendiente |
| 5d | Products (con checkboxes múltiples + Y/N por fila) | ⏳ Pendiente |
| 8a | Seeds | ⏳ Pendiente |
| 8g | Planting stock perenne | ⏳ Pendiente |
| 10 | Crop Rotation (5 checkboxes por fila) | ⏳ Pendiente |
| 12 | Inputs (6 columnas, select + Y/N) | ⏳ Pendiente |
| 14 | Equipment | ⏳ Pendiente |
| 19 | Field History Affidavit (por año) | ⏳ Pendiente |
| 20 | Search Record (formato especial, numerado 1/2/3, sub-campos Crop/Traits) | ⏳ Pendiente |

**Estado actual (17/ago): las 12 tablas dinámicas están construidas** mediante un motor genérico (`TABLE_CONFIGS` en `osp_form.js`) — una sola definición de columnas por tabla, nunca escritas por separado en HTML y JS, evitando el bug de desalineación que ya se pisó una vez con Sites.

| Sección | Tabla | Estado |
|---|---|---|
| 1j | Authorized Contacts (Name/Email/Phone) | ✅ Construida |
| 4g | Sites (Site ID, Address, City/State, Zip, Contact, Description) | ✅ Construida |
| 4h | Fields | ✅ Construida |
| 4j | Crops | ✅ Construida |
| 5d | Products | ✅ Construida |
| 8a | Seeds | ✅ Construida |
| 8g | Planting stock perenne | ✅ Construida |
| 10 | Crop Rotation | ✅ Construida |
| 12a | Inputs | ✅ Construida |
| 14a | Equipment | ✅ Construida |
| 19 | Field History Affidavit (por año) | ✅ Construida |
| 20 | Search Record | ✅ Construida |

**Cómo se generalizó el patrón**: cada tabla es una entrada en `TABLE_CONFIGS` con `jsonInputId`, `tbodyId`, `addBtnId` y una lista `columns` (cada columna con `key`, `type`: `text`/`select`/`date`, y `options` si aplica). Un único motor (`renderDynTable`, `cellHtml`, `bindDynTableEvents`, `initDynTable`) sirve a las 12 — agregar una tabla nueva en el futuro es solo agregar una entrada al config + el `<table>` skeleton en el XML, sin tocar lógica JS.

## 5. Sincronización Sección 1 → campos del registro (IMPLEMENTADA)

Las respuestas de la Sección 1 (`1a_org_name`, `1b_dba_name`, `1c_address`, `1d_city`, `1f_zip`, `1e_state`, `1g_country`) se copian a los campos "resumen" del modelo (`organization_name`, `dba_name`, `street`, `city`, `zip_code`, `state_id`, `country_id`) **únicamente al hacer Submit** (no en cada Save progress). Cada submit **sobreescribe** estos valores con lo más reciente. Esto vive en `controllers/portal.py`, ruta `portal_save_osp`. El campo `street` (para `1c_address`) ya existe en el modelo (agregado 17/ago).

`1e_state` y `1g_country` son **selects reales conectados a `res.country.state` / `res.country`** (no texto libre), con filtro en cascada en JS: al elegir un país, el select de estado solo muestra los de ese país.

## 6. Modo Administrador de OSP / edición del cliente (IMPLEMENTADO — 17/ago, corregido 17/ago)

- Ruta `/my/osp/form/<id>` y `/my/osp/save/<id>` en `portal.py` aceptan **dos tipos de usuario**: el cliente dueño del registro (`partner_id` coincide), o cualquier usuario del grupo `osp_management.group_osp_administrator`.
- **Cliente**: puede editar/guardar **siempre**, sin importar el `state` (`draft` o `submitted`). `readonly` en `portal_osp_form` es constante `False` — ya no existe el bloqueo "solo lectura tras submit" que había antes (se quitó porque el admin no tenía manera de regresar el registro a `draft`, y eso dejaba al cliente sin poder corregir nada tras un primer submit).
  - **"Save progress"** (`is_submit=False`) sobre un formulario ya `submitted`: se guarda `form_data` normalmente, pero **no** toca `state`, **no** sincroniza los campos resumen y **no** notifica al admin — queda como avance privado del cliente.
  - **"Submit"** (`is_submit=True`), sea la primera vez o una actualización: sincroniza los campos resumen (Sección 1 → `organization_name`/`dba_name`/etc., vía `_sync_osp_summary_fields`), (re)marca `state = 'submitted'`, y dispara la notificación al admin (punto 8).
- **Administrador de OSP**: entra vía el botón "Ver Formulario Web" (`action_open_portal_form`, ver punto 7 — se abre incrustado en el backend). Solo tiene botón de guardar ("Save changes"), **nunca Submit**. Cada guardado del admin también corre `_sync_osp_summary_fields` (bug corregido 17/ago: antes solo se sincronizaba en el submit del cliente, así que si el admin corregía la Sección 1 —p. ej. `1a_org_name`/`1b_dba_name`— la lista del admin quedaba desactualizada) y deja rastro en el chatter.
- `_sync_osp_summary_fields` vive en `controllers/portal.py` como método compartido de `OSPPortal`, usado tanto por el submit del cliente como por el guardado del admin — una sola fuente de verdad para evitar que se repita el bug anterior.

## 7. Formulario del admin incrustado en el backend (IMPLEMENTADO — 17/ago, puntos 2+3)

**Decisión de arquitectura** (en vez de reconstruir ~300 campos + 12 tablas como widgets nativos de Odoo, lo cual duplicaría `osp_form_crop.xml`/`osp_form.js` y arriesgaría que la vista admin y la vista cliente diverjan con el tiempo): se **reutiliza el mismo formulario del portal**, incrustado dentro del backend de Odoo vía un client action con `<iframe>`.

- `action_open_portal_form` (`osp_request.py`) ahora detecta si quien llama es del grupo `osp_management.group_osp_administrator`: en ese caso devuelve `{'type': 'ir.actions.client', 'tag': 'osp_admin_form_view', 'params': {'osp_id': self.id}, 'target': 'current'}` en vez de un `act_url` a pestaña nueva. Cualquier otro caso conserva el `act_url` de respaldo.
- Componente Owl `OspAdminFormView` (`static/src/js/osp_admin_form_view.js` + template `static/src/xml/osp_admin_form_view.xml`), registrado en `web.assets_backend` vía el manifest. Simplemente renderiza un `<iframe>` hacia `/my/osp/form/<osp_id>` — la misma URL que usa el cliente.
- **Resultado**: el botón "Ver Formulario Web" abre el formulario **dentro del top menu / breadcrumbs de Odoo** (no en pestaña nueva), mostrando **exactamente** las mismas capturas que ve el cliente, y todo guardado del admin usa el **mismo endpoint** `/my/osp/save/<id>` que ya existía — sincronización garantizada por diseño, sin lógica duplicada.
- **Limitación conocida / mejora futura**: dentro del `<iframe>` todavía se ve el "cascarón" `portal.portal_layout` completo (navbar/footer del sitio web), duplicado visualmente con el top menu de Odoo por encima. Si se quiere un embed más limpio, se podría agregar un modo `?embed=1` que la ruta `/my/osp/form/<id>` detecte para omitir navbar/footer del portal y dejar solo el contenido del formulario.
- **Corregido 17/ago**: el link "Back to list" del encabezado del formulario (`osp_form_crop.xml`) ahora solo se muestra `t-if="not is_admin"` — para el admin no tenía sentido (lo mandaba a `/my/osp`, el listado del *cliente*, que el admin no usa).
- **Corregido 17/ago**: el título "Nuevo" que aparecía en la ficha del admin (campo `name`, default de Odoo) se reemplaza automáticamente al crear el registro por `"<Servicio> - <Tipo de Formulario>"` (override de `create()` en `osp_request.py`). Los registros que ya existían con `name = 'Nuevo'` **sí se migran retroactivamente**: ver `migrations/17.0.1.0.4/post-migrate.py` (bump de versión a `17.0.1.0.4` en `__manifest__.py` — corre solo, una vez, en el próximo `-u osp_management`).

## 8. Notificaciones al Administrador de OSP (IMPLEMENTADO — 17/ago, punto 4)

- En `controllers/portal.py`, dentro de `portal_save_osp`, cuando el **cliente** (no el admin) hace `is_submit=True`, se distingue si es el primer submit o una actualización (`was_submitted = record.state == 'submitted'` antes del `write`).
- Se llama `record.message_notify(partner_ids=<partners del grupo Administrador de OSP>, subject=..., body=...)`. Esto hace dos cosas a la vez, de forma nativa (sin código extra): deja el mensaje en el **chatter** del registro, y genera una notificación **needaction** que aparece en la **campanita** (icono de notificaciones) del perfil de cada Administrador de OSP en Odoo — sin necesidad de que ya sigan el registro.
- Si por algún motivo el grupo no tiene usuarios, se hace `message_post` normal como respaldo (para no perder el rastro en el chatter).
- Nota: esto cubre las acciones del **cliente**. Los guardados del **admin** sobre un registro ya `submitted` siguen dejando su propio mensaje de chatter (ver punto 6) pero no generan campanita — no fue parte de lo solicitado.
- 🐛 **Bug corregido 17/ago**: al probar como usuario de portal, "Save progress" funcionaba pero **"Submit" fallaba** ("Error al guardar", consola sin nada útil — motivó además agregar `console.error` en `osp_form.js` para exponer errores JSON-RPC que antes se tragaba en silencio). Causa raíz: `admin_group.users.partner_id` intenta leer `res.users` para resolver a qué administradores notificar, y un usuario de portal **no tiene permiso de lectura sobre `res.users`** → `AccessError` silencioso (Save progress no pasa por este código, por eso sí funcionaba). Fix: `admin_group.sudo().users.partner_id` y `record.sudo().message_notify(...)` / `record.sudo().message_post(...)` en ese bloque — es plomería interna para resolver destinatarios, el cliente no necesita (ni debe) tener visibilidad sobre `res.users`.

## 9. Subida de archivos adjuntos del cliente (IMPLEMENTADO — 17/ago, punto 6; corregido 17/ago)

- Nueva sección **"Attachments"** al final del formulario Crop (`osp_form_crop.xml`, `id="sec21"`), con link propio en la barra lateral.
- Nueva ruta `POST /my/osp/upload/<osp_id>` (`portal.py`): actúa si quien llama es el **dueño** del registro — **sin importar el estado** (`draft` o `submitted`; se quitó esa restricción para ser consistente con que "el cliente siempre puede editar", ver punto 6). Fuera de esa condición, el formulario ni siquiera muestra el botón de subir (variable de contexto `can_upload`). Cada archivo se crea como `ir.attachment` normal (`res_model='osp.request'`, `res_id=<id>`), con `description` indicando que fue "Subido por el cliente vía portal" — la "fuente" del archivo queda registrada de forma nativa en `create_uid`/`create_date` de ese `ir.attachment`, sin necesidad de un campo nuevo.
- Nueva ruta `GET /my/osp/attachment/delete/<attachment_id>`: mismo candado (solo dueño, cualquier estado), permite al cliente borrar un adjunto que subió por error.
- **El admin no necesita nada nuevo para verlos**: el botón inteligente "Archivos Adjuntos" (icono de clip, `action_view_attachments` + campo `attachment_count`) que ya existía en la vista de formulario del backend (`osp_menu_views.xml`) lista automáticamente todos los `ir.attachment` ligados al registro. Como cada subida crea un `ir.attachment` nuevo y distinto, "solo agregar si hay archivos nuevos" es el comportamiento natural de Odoo — no hace falta lógica de deduplicación.
- La misma sección "Attachments" también lista los archivos (con link de descarga) cuando el formulario lo abre el admin — solo se ocultan los controles de subir/borrar según `can_upload` (el admin nunca sube/borra desde aquí; usa el widget del backend).

## 10. Lecciones aprendidas / bugs ya corregidos (para no repetirlos)

1. **Desajuste header/fila en tablas dinámicas**: si el `<thead>` tiene N columnas y el JS solo genera M `<td>` por fila (M≠N), la tabla se ve rota/desalineada visualmente sin lanzar ningún error. Siempre generar ambos desde la misma fuente de verdad.
2. **`DOMContentLoaded` no dispara en bundles "lazy"**: el bundle de assets del portal (`web.assets_frontend_lazy.min.js`) a veces se inyecta en la página **después** de que el DOM ya está listo. Si el script hace `document.addEventListener("DOMContentLoaded", fn)` en ese momento, el evento ya pasó y `fn` nunca se ejecuta — sin ningún error visible en consola. Patrón defensivo correcto ya aplicado en `osp_form.js`:
   ```js
   if (document.readyState === 'loading') {
       document.addEventListener('DOMContentLoaded', initOspForm);
   } else {
       initOspForm();
   }
   ```
3. Al debuggear builds fallidos en Odoo.sh: el archivo relevante es **`update.log`** (proceso de instalación/upgrade con `-u modulo`), no `odoo.log` (que es el log del servidor ya corriendo — puede mostrar todo verde aunque el build haya fallado antes). Si el "Test: Failed" no aparece reflejado en logs recientes, probablemente el log se sobreescribió con un rebuild posterior — hacer un Rebuild fresco y revisar el log inmediatamente después. Muchos fallos de build en Odoo.sh son transitorios (condiciones de carrera al clonar la BD de producción) y un simple Rebuild los resuelve.
4. **Todo campo usado en un modifier (`invisible`/`readonly`/`required`) debe estar presente en el arch de esa vista**, aunque sea con `invisible="1"` — si no, Odoo ni siquiera deja instalar el módulo (`ParseError: Field 'x' used in modifier... must be present in view but is missing`). Bug real (18/ago): el botón "Descargar OSP" usaba `invisible="state != 'submitted'"` en `view_osp_request_form`, pero esa vista nunca declaraba el campo `state` en ningún lado — se agregó `<field name="state" invisible="1"/>` junto a él. Si se desinstala y reinstala el módulo (en vez de solo actualizarlo) para recuperarse de un error así, la reinstalación es una instalación NUEVA — los scripts de migración (`migrations/`) no aplican (esos solo corren en upgrades desde una versión anterior), pero tampoco hacen falta: partiendo de cero, los `.po` de idioma aplican correctamente sin necesitar el truco de "forzar traducción por ORM" que se usó para arreglar una base que ya tenía traducciones en blanco.

## 11. Seed data de catálogos: Servicios y Formularios (IMPLEMENTADO — 17/ago)

- `data/osp_service_data.xml` (3 registros: NOP/USDA, LPO, RN 29782) y `data/osp_form_template_data.xml` (6 registros: Crop, Handler, Handler (Trader), Cultivo, Manejo o Proceso, Comercializador — todos bajo el servicio NOP/USDA) se agregaron a `'data'` en `__manifest__.py`, ambos con `noupdate="1"`.
- **Comportamiento de `noupdate="1"`**: los registros se crean la primera vez que Odoo carga ese XML ID — ya sea en una **instalación nueva** del módulo, o la primera vez que un `-u osp_management` "ve" un XML ID que nunca había cargado antes (p. ej. porque el archivo se agregó en una versión posterior). Una vez creado ese registro, **futuras actualizaciones del módulo ya no lo tocan** (no lo re-crea, no lo pisa si el usuario lo editó a mano). Es decir: "solo aplica al instalar" es cierto de aquí en adelante, pero **no retroactivo**.
- ⚠️ **Base de staging actual**: los 3 servicios y 6 formularios ya existían ahí, creados **a mano** desde la UI (sin XML ID) — decisión tomada con el usuario (17/ago): en vez de dejar que se dupliquen y luego limpiar, **se borran manualmente antes** del próximo `-u osp_management`, así el update los crea limpios desde cero con los XML IDs de arriba, sin duplicados. Antes de borrar, revisar que ningún `osp.request` ya esté usando esos `service_id`/`form_template_id` (no son `required`, así que un borrado no bloquea — solo deja esos campos vacíos en el expediente que los usaba).
- Versión del manifest: `17.0.1.0.5`.

### Códigos `technical_code` reservados para los próximos formularios (mapa de continuidad)

`osp.form.template.technical_code` es el campo que liga cada renglón del catálogo con la plantilla QWeb real que arma `controllers/portal.py` (`if record.form_template_id.technical_code == 'form_crop': ...`). Ya están sembrados en `data/osp_form_template_data.xml` estos 6 códigos — cuando se construya cada formulario nuevo, usar exactamente este código (no inventar uno distinto a mitad de esa sesión):

| Formulario | `technical_code` | Estado |
|---|---|---|
| Crop | `form_crop` | ✅ Construido (ver `FORM_SPEC_CROP.md`) |
| Handler | `form_handler` | ✅ Construido (ver `FORM_SPEC_HANDLER.md`, punto 18) |
| Handler (Trader) | `form_handler_trader` | ✅ Construido (ver `FORM_SPEC_HANDLER_TRADER.md`, punto 21) |
| Cultivo | `form_cultivo` | ⏳ Pendiente |
| Manejo o Proceso | `form_manejo_proceso` | ⏳ Pendiente |
| Comercializador | `form_comercializador` | ⏳ Pendiente |

**Checklist completo para construir cada formulario nuevo** (sin tocar los ya construidos):

1. **`FORM_SPEC_<NOMBRE>.md`** — spec de referencia (JSON keys, opciones de selects, condicionales, qué tablas son dinámicas), mismo formato que `FORM_SPEC_CROP.md`. Se arma junto con el usuario a partir del `.docx`/`.md` que comparta (ver punto sobre archivos `.md` más abajo) — **es el documento del que salen tanto el formulario web como los datos del reporte PDF**, para no tener que inventar/adivinar dos veces.
2. **Formulario web**: template QWeb propio (`views/osp_form_<nombre>.xml`, patrón de `osp_form_crop.xml`/`osp_form_handler.xml` — body reutilizable + wrappers portal/público) + agregar su renglón a los diccionarios `FORM_BODY_TEMPLATES` en `portal_osp_form_new` y `portal_osp_form` (`controllers/portal.py`). Si trae tablas dinámicas, agregar sus configs a `TABLE_CONFIGS` en `osp_form.js` (con claves/ids propios, no reutilizar los de otro formulario aunque el concepto se parezca — ver punto 18).
3. **Formulario público**: agregar su renglón en `OSPPublicController.PUBLIC_FORM_SLUGS` (slug → technical_code) y en `PUBLIC_BODY_TEMPLATES` (technical_code → xmlid del wrapper público) — ver puntos 14 y 18.
4. **Reporte PDF** (punto 15/18, **la funcionalidad de impresión aplica a todos los formularios, no solo Crop**, y el motor QWeb ya es 100% genérico — no hace falta tocarlo): por cada formulario nuevo solo hace falta —
   - `report/osp_<nombre>_report_data.py` (su propio manifest de secciones/preguntas, mismo formato que `CROP_REPORT_SECTIONS`/`HANDLER_REPORT_SECTIONS`, sacado del `FORM_SPEC_<NOMBRE>.md`),
   - un método de una línea `get_<nombre>_report_sections()` en `report/osp_<nombre>_report.py`, que llame a `self._resolve_report_sections(<NOMBRE>_REPORT_SECTIONS)` (motor común en `report/osp_report_common.py`) — `get_report_sections()` lo descubre solo por convención de nombre a partir del `technical_code`, sin tocar ningún dispatcher.
   - **Ya NO hace falta** tocar el botón "Descargar OSP" ni el link "PDF" del portal — ambos usan la `ir.actions.report`/template únicos y genéricos (`action_report_osp`/`report_osp_document`), que sirven a cualquier `osp.request` sin importar su `technical_code`.

## 12. Idioma / traducción (IMPLEMENTADO — 17/ago)

**Regla acordada con el usuario, muy importante para no romperla a futuro**: el **formulario web en sí NUNCA se traduce** — `osp_form_crop.xml` completo (sus 20 secciones, preguntas, opciones de respuesta, botones de guardar/submit) se queda tal cual está, sea cual sea el idioma del usuario. Solo se traducen los **"elementos de pantalla"** alrededor de él: título de módulo, menús, columnas de listas, labels de la ficha, nombres de catálogos/opciones, y el log de actividades (chatter). Cualquier trabajo de i18n futuro sobre este módulo debe respetar este límite salvo que el usuario diga explícitamente lo contrario.

- **Mecanismo**: archivos `.po` estándar de Odoo en `i18n/`, auto-detectados por Odoo (no requieren entrada en `__manifest__.py`). Se recargan solos en cada `-u osp_management` para cualquier idioma ya instalado en la base (en este caso English (US) y Spanish (MX), ambos ya activos).
- **`i18n/en_US.po`** — traduce el **backend** (perfil Administrador de OSP, escrito originalmente en español) → inglés. Cubre: nombre del módulo/app (→ **"OSP Management"**), categoría y grupo de seguridad, menús, acciones, las 3 vistas de "Planes de manejo orgánico" (→ **"Organic System Plans"**), catálogos de Servicios/Formularios, buscador y filtros, todos los labels/grupos/botones/placeholders de la ficha, **todas** las etiquetas de campo de los 3 modelos (`osp.request`, `osp.service`, `osp.form.template`), las opciones de los 2 campos `Selection` (`review_status`, `state`), y los mensajes de chatter que genera `controllers/portal.py`/`models/osp_request.py` (ya usaban `_()`). **`Sitio` → `"DBA name"`** (regla explícita del usuario).
- **`i18n/es_MX.po`** — traduce solo la pantalla `/my/osp` del **portal** (`views/osp_portal_templates.xml`: título, columnas de la tabla, badges Draft/Submitted, botones Duplicate/Open/Delete, modal "New Form") — escrita originalmente en inglés → español. **`DBA Name` → `"Sitio"`** (misma regla, en la dirección opuesta). El propio formulario (`osp_form_crop.xml`) queda fuera, tal como se acordó.
- De paso, `en_US.po` también traduce 2 frases que ya estaban en español por una inconsistencia previa dentro de `osp_portal_templates.xml` (el mensaje de "no hay planes creados" y el placeholder de formularios aún no construidos) — para que el default de esa pantalla sea coherente en ambos idiomas.
- Se envolvió con `_()` el `'name': 'Archivos Adjuntos'` de `action_view_attachments` en `osp_request.py` (antes era un string suelto, no traducible).
- **Limitaciones conocidas / no cubiertas en esta pasada**:
  1. El texto del `confirm()` de JavaScript al borrar un borrador ("¿Estás seguro de eliminar este borrador?", en `osp_portal_templates.xml`) no se tradujo — vive dentro de un atributo `onclick`, que no está garantizado en la lista de atributos traducibles de Odoo (`title`/`placeholder`/`aria-label` sí lo están; `onclick` es dudoso), y como es una cadena JS embebida, un error de escape ahí rompería el diálogo. Se dejó fuera para no arriesgar. Queda en español como está hoy.
  2. Las 4 traducciones de opciones de `Selection` (`Pendiente`/`Completo (Hecho)`/`Borrador (En Portal)`/`Enviado`) usan el xmlid auto-generado `selection__<modelo>__<campo>__<valor>` — es el patrón estándar de Odoo 17, pero no se pudo verificar contra una instancia corriendo. Si al probar no aparecen traducidas, es el primer lugar a revisar.
  3. Los datos de catálogo (`data/osp_service_data.xml`, `data/osp_form_template_data.xml` — nombres como "NOP/USDA", "Crop", "Handler") son datos de negocio, no elementos de pantalla — no se tradujeron a propósito (además, algunos nombres de catálogo coinciden con nombres de plantillas de formulario futuras, traducirlos generaría confusión).
- **Cómo probar**: cambiar el idioma del usuario en su perfil (Mi Perfil → Preferencias → Idioma) entre "English (US)" y "Spanish (MX) / Español (MX)", y recargar. Si algo no se tradujo, lo más probable es un desajuste entre el `msgid` del `.po` y el texto real renderizado (típicamente espacios/comillas) — hay que revisar el string exacto en el archivo fuente correspondiente.
- 🐛 **Bug corregido 17/ago**: tras el primer despliegue, el **portal** tradujo perfecto, pero el **backend** casi no cambió (solo las columnas "Creación"/"Última actualización", que sí venían de un `string=` dentro del arch de la vista). Causa: Odoo tiene dos mecanismos de traducción distintos. Los términos `model_terms:ir.ui.view` (texto dentro del arch de una vista) se re-sincronizan solos en cada `-u módulo`, porque la vista se reprocesa entera. Pero los términos `model:X,Y` planos —nombre de módulo (`ir.module.module.shortdesc`), menús (`ir.ui.menu.name`), acciones (`ir.actions.act_window.name`), grupo (`res.groups.name`), y **las etiquetas de campo** (`ir.model.fields.field_description`, la fuente de la mayoría de las columnas de lista que no tienen `string=` explícito en la vista)— **no se recargan solos** en un `-u` normal, porque esos registros ya existían desde antes de que existiera el `.po` (creados en español, sin traducción a inglés) y Odoo no pisa una traducción "vacía pero ya existente" salvo que se le pida con `overwrite=True`. Fix: `migrations/17.0.1.0.6/post-migrate.py`, que llama `env['ir.module.module']._update_translations(overwrite=True)` una sola vez (mismo mecanismo que Configuración → Traducciones → Cargar una Traducción, pero disparado solo, sin que el usuario tenga que ir a la UI). Versión bump a `17.0.1.0.6`.
- 🐛 **17.0.1.0.6 tampoco funcionó** (probado 17/ago): el backend siguió en español pese al `overwrite=True`. En vez de seguir dependiendo de que el importador de `.po` resuelva bien esos registros "model:X,Y" (cuya mecánica interna no se pudo verificar sin una instancia real), **`migrations/17.0.1.0.7/post-migrate.py`** escribe la traducción **directo en cada registro vía el ORM** con `record.with_context(lang='en_US').write({...})` — el mismo mecanismo que usa la UI cuando un humano traduce un campo a mano con el ícono de "globo", sin pasar por el importador de `.po` en absoluto. Para las etiquetas de campo (`ir.model.fields`) busca el registro por `(model, name)` en vez de por external id, evitando depender de que el xmlid auto-generado exista con el patrón esperado. Cubre: shortdesc del módulo, categoría, grupo, los 5 menús, las 3 acciones (+ su `help`), 17 etiquetas de campo de `osp.request`, 5 de `osp.service`/`osp.form.template`, y las 4 opciones de `Selection`.
- 🐛 **Causa raíz real, confirmada por el usuario con capturas (17/ago)**: 17.0.1.0.7 SÍ escribió — pero **de forma uniforme para TODOS los idiomas**, no solo `en_US` (ej. el campo "Sitio"/`dba_name` quedó como "DBA Name" en inglés Y en las 3 variantes de español). Motivo: en Odoo 17 los campos traducibles se guardan como JSONB por idioma. Mientras un campo **nunca tuvo una traducción explícita por idioma** (nuestro caso — el texto fuente en español se mostraba igual para cualquier idioma por simple fallback, sin estar "dividido" en el JSONB), el primer `write()` bajo un `lang=` específico no separa el valor: lo reemplaza de forma uniforme para todos los idiomas, porque no había nada previo con qué dividir. Además la base tiene **4 idiomas activos**, no 2: English (US), Spanish (CL), Spanish (CR), Spanish (MX) (visible en el diálogo "Translate" de Odoo con developer mode).
  Fix: **`migrations/17.0.1.0.8/post-migrate.py`** — detecta los idiomas realmente instalados (`env['res.lang'].search([])`, sin asumir cuáles son) y escribe **cada idioma explícitamente**: el texto en español para todos los `es_*` instalados, inglés solo para `en_US`. Así el JSONB queda correctamente dividido por idioma desde el primer momento. Versión bump a `17.0.1.0.8` — **este es el que hay que probar ahora**. Si tampoco funciona, el siguiente sospechoso sería revisar si `field_description`/`name` de estos modelos realmente tienen `translate=True` en el core de Odoo (se asumió que sí, no se pudo verificar contra el código fuente de Odoo 17 en este entorno).

## 13. Creación diferida del draft (IMPLEMENTADO — 17/ago)

**Bug reportado**: entrar a ver el formulario (botón "Open" del modal "New Form") ya creaba un registro `osp.request` en estado `draft`, aunque el usuario no tocara ni guardara nada — con solo abrir y cerrar el formulario varias veces se acumulaban drafts "basura" en la lista (visto en captura: 6 registros `N/A` sin ningún dato).

- **Antes**: `portal_create_osp` (`/my/osp/create`, el submit del modal) creaba el registro inmediatamente y redirigía a `/my/osp/form/<id>`.
- **Ahora**: `/my/osp/create` ya NO crea nada — solo redirige a la nueva ruta `/my/osp/form/new?service_id=X&template_id=Y`, que renderiza el mismo template `osp_form_crop.xml` pero con un objeto `osp` de relleno (`SimpleNamespace(id=0, form_data={})`, ya que el template solo usa `osp.form_data` y `osp.id` — se verificó que no usa nada más del registro). El hidden input `osp_id` queda en `0`, y se agregan 2 hidden inputs nuevos (`new_service_id`, `new_template_id`) para que el JS sepa qué crear.
- El registro **recién se crea** en el primer `Save progress` o `Submit` real: `osp_form.js` (`saveForm()`) detecta `ospId === 0` y en ese caso pega a la nueva ruta `/my/osp/save_new` (en vez de `/my/osp/save/<id>`), que sí hace el `create()`. La respuesta trae el `osp_id` real, que el JS guarda (`ospId` pasó de `const` a `let`) y usa para actualizar la URL sin recargar (`history.replaceState`) — así, guardados posteriores en la misma sesión van por la ruta normal, y un refresh de página no crea un segundo registro por accidente.
- Se extrajo la lógica de "submit" (sync de campos resumen + `state='submitted'` + notificación al admin) a un método compartido `_do_client_submit()`, usado tanto por `portal_save_osp` (registro existente) como por `portal_save_osp_new` (recién creado) — evita duplicar esa lógica dos veces.
- Formularios de tipo `technical_code` distinto a `form_crop` (ej. Handler, aún no construido): igual se muestra el placeholder de "en construcción" de siempre, también sin crear ningún registro — solo necesitaba `osp.form_template_id.name`, cubierto con el mismo objeto de relleno.
- **Los 6 drafts basura que ya existían** (de antes de este fix) no se borraron automáticamente — el usuario ya tiene el botón de basurero en la lista del portal para cada draft y puede limpiarlos a mano cuando quiera.
- **Resuelto 17/ago**: en `/my/osp/form/new` (`osp.id == 0`), la sección "Attachments" ahora muestra un aviso explícito (`#attachments_save_first_notice`) explicando que hay que guardar progreso primero, en vez de solo ocultar el botón de subir sin decir por qué. En cuanto el primer `Save progress`/`Submit` tiene éxito, `osp_form.js` (`enableAttachmentsUpload()`) oculta ese aviso y construye el formulario de subida al vuelo (con el `osp_id` real recién creado) — **sin recargar la página**. Si el formulario de subida ya existía en el DOM (caso normal: formulario que ya se había guardado antes), solo se actualiza su `action` con el id correcto.
- 🐛 **Bug corregido 17/ago**: al probar lo anterior, el primer "Save progress" de un formulario nuevo fallaba con 404 en `/my/osp/save/NaN`. Causa: el hidden input `osp_id` usaba `t-att-value="osp.id"` — y Odoo/QWeb **omite el atributo por completo** cuando el valor es `0` (lo trata como "falsy", igual que `None`/`False`). Con el atributo `value` ausente, `parseInt(ospIdInput.value)` en el JS daba `NaN`, y como `NaN !== 0`, el código pensaba que el registro YA existía y armaba la URL `/my/osp/save/NaN` en vez de usar `/my/osp/save_new`. Fix: los 3 hidden inputs (`osp_id`, `new_service_id`, `new_template_id`) pasaron de `t-att-value` a `t-attf-value="#{...}"` (interpolación de texto), que siempre escribe el valor literal sin importar si es `0`. **Ojo para el futuro**: cualquier `t-att-*` en este módulo cuyo valor pueda legítimamente ser `0` corre el mismo riesgo — usar `t-attf-*` en esos casos, no `t-att-*`.
- **Resuelto 17/ago**: se quitó el `confirm()` de JS al hacer clic en "Submit Organic System Plan" ("Are you sure...? You will not be able to edit it after submission.") — ese texto ya era falso desde que se implementó que el cliente siempre puede seguir editando después de Submit (punto 6). Ahora Submit va directo (sigue validando que Name/Signature/Date estén llenos antes) y redirige a `/my/osp` sin ningún diálogo de confirmación.

## 14. Formulario público (sin login) para navegantes — IMPLEMENTADO 17/ago

**Contexto de negocio**: además del cliente de portal y el Administrador de OSP, ahora un **navegante sin cuenta** puede llenar y enviar el formulario Crop desde una URL pública. El registro llega al admin **sin `partner_id`** (no hay sesión de la que sacar un cliente); el admin lo vincula después a mano a un contacto existente de Odoo. En cuanto queda vinculado, los usuarios de portal de ese contacto ven el registro en su `/my/osp` automáticamente — **no hizo falta programar nada para eso**: la regla de acceso portal ya filtra por `partner_id = user.partner_id`, y tanto la lista como el formulario ya usan ese campo.

**Decisiones de arquitectura acordadas con el usuario** (importante para no romperlas a futuro):
1. **"Save progress" del navegante es 100% local (localStorage del navegador)** — cero llamadas al servidor hasta el Submit final. Si borra caché del navegador o cambia de dispositivo antes de enviar, pierde el avance (sin forma de retomarlo por link) — trade-off aceptado a propósito por ser mucho más simple y seguro que un modelo de "borrador en el servidor sin dueño real".
2. **Adjuntos solo se habilitan DESPUÉS del Submit**, en la pantalla de "Gracias" — nunca antes (no hay registro contra el cual subir nada).
3. **Sin protección anti-bot por ahora** (ni honeypot ni reCAPTCHA) — es un link controlado, se puede agregar después si hay abuso real.
4. **El admin gestiona el alta de portal aparte** — vincular el registro solo asigna `partner_id`; si ese contacto no tiene ya un usuario de portal, el admin usa el flujo estándar de Odoo ("Otorgar acceso al portal" desde Contactos) por separado.

**Cómo se construyó (reutilizando al máximo lo ya existente)**:

- **Refactor de `osp_form_crop.xml`**: el contenido real del formulario (encabezado, 20 secciones, 12 tablas, adjuntos — las ~2100 líneas) se movió a un template `osp_form_crop_body`, llamado vía `t-call` desde DOS wrappers delgados:
  - `portal_osp_form_crop` → envuelve con `portal.portal_layout` (cliente/admin, como antes).
  - `public_osp_form_crop` → envuelve con `website.layout` (navegante público, sin los links de "Mi cuenta" que no podría usar).
  Cero contenido duplicado — cualquier cambio futuro a una pregunta/tabla se hace en un solo lugar y aplica a los tres perfiles.
- **Nuevo módulo depende de `website`** (agregado a `depends` en `__manifest__.py`, antes solo `base`/`mail`/`portal`) — necesario por `website.layout`.
- **`OSPPublicController(OSPPortal)`** en `controllers/portal.py` — hereda de `OSPPortal` únicamente para reutilizar `_sync_osp_summary_fields` (no re-registra ninguna ruta existente, cada una sigue con su propio `auth`). Todas sus rutas usan `auth="public"` + `sudo()` en las escrituras (mismo criterio que ya usábamos para adjuntos): el visitante no tiene ningún permiso ORM propio, la validación vive en el código de cada ruta, no en reglas de acceso nuevas.
  - `GET /osp/public/crop` — resuelve la plantilla `form_crop` por `technical_code` (y de ahí su `service_id`, así que no hace falta que el navegante elija servicio) y renderiza `public_osp_form_crop` con un `osp` de relleno (`SimpleNamespace(id=0, form_data={})`) — igual patrón que ya usábamos para "formulario nuevo" del cliente logueado.
  - `POST /osp/public/submit` (json) — el único punto que de verdad crea el `osp.request`: `sudo().create(...)` con `partner_id` ausente, `state='submitted'` directo, sincroniza campos resumen, y notifica al admin (mensaje adaptado: "Un visitante del sitio web... no tiene un cliente asignado — vincúlalo...").
  - `GET /osp/public/thankyou/<id>` — pantalla de confirmación; muestra la sección de adjuntos **solo si el registro sigue sin `partner_id`** (en cuanto el admin lo vincula, esta ruta dejar de aceptar subidas para ese id — control natural, sin necesidad de tokens ni expiración).
  - `POST /osp/public/upload/<id>` — mismo candado (`not record.partner_id`).
- **`osp_form.js`**: nuevo flag `window.OSP_PUBLIC_MODE`. `saveForm()` ahora delega a `savePublicForm()` cuando está activo: "Save progress" escribe a `localStorage` (clave `osp_public_crop_draft`) sin red; Submit hace un único `fetch` a `/osp/public/submit`, limpia el `localStorage` al tener éxito, y redirige a la pantalla de gracias. Nueva función `hydrateFormFromData()` (inversa de `gatherFormData()`) restaura los inputs desde el JSON guardado si el navegante vuelve a esa misma URL en el mismo navegador — corre ANTES de que el motor de tablas dinámicas lea sus inputs ocultos `*_json`, así las tablas también se hidratan solas.
- **Backend admin**: banner de aviso (`invisible="partner_id"`) en la ficha de `osp.request` cuando `partner_id` está vacío, explicando que es un envío del sitio web sin cliente asignado y que hay que vincularlo — el campo `partner_id` ya era editable en esa vista, no hizo falta agregar ningún botón ni lógica nueva para "vincular", solo hacerlo evidente.
- **Logo de marca**: `<img>` al inicio de `osp_form_crop_body` (visible para las tres audiencias) apuntando a `static/src/img/primus_logo.png` — **listo**, el archivo ya se copió ahí (18/ago).
- **Ligas públicas por formulario (18/ago)**: la ruta pública ya no está fija a Crop — es `/osp/public/<slug>` genérica, resuelta vía el diccionario `OSPPublicController.PUBLIC_FORM_SLUGS` (`slug -> technical_code`). Hoy solo tiene `'crop': 'form_crop'`. Para publicar un formulario nuevo (Handler, Cultivo, etc.) cuando ya esté construido: (1) agregar su renglón en `PUBLIC_FORM_SLUGS`, (2) agregar su rama en `_render_public_form()` (qué template QWeb renderizar). `/osp/public/submit` y el JS (`window.OSP_TECHNICAL_CODE`, seteado desde el `technical_code` que ahora pasan las 3 rutas que renderizan `osp_form_crop_body`) ya viajan con el código técnico correcto de punta a punta — incluida la llave de `localStorage` (`osp_public_draft_<technical_code>`), para que llenar dos formularios públicos distintos en el mismo navegador no se pise el avance guardado del uno con el del otro.

## 15. Reporte PDF del formulario Crop — IMPLEMENTADO 18/ago

**Decisiones acordadas con el usuario** (importantes, no cambiarlas sin confirmar): se imprimen **todas** las preguntas siempre, aunque estén vacías (nunca se omiten secciones); Sí/No y checkboxes se ven como glifos reales `☐`/`☑`; el PDF **no** lista los nombres de los adjuntos (esos se manejan aparte, vía el widget de "Archivos Adjuntos" que ya existe); el nombre del archivo descargado usa el campo `name` del registro (`Referencia.pdf`).

**Decisión de arquitectura clave**: en vez de escribir a mano ~2000 líneas de QWeb repitiendo cada una de las ~300 preguntas (como se tuvo que hacer para el formulario web), se centralizó **una sola fuente de verdad** en Python:

- **`report/osp_crop_report_data.py`** — `CROP_REPORT_SECTIONS`: lista de las 20 secciones, cada una con sus preguntas (`key` exacto tal como vive en `form_data`, `label`, y `type`: `text`/`textarea`/`date`/`yn`/`yn_na`/`checkbox`/`checkbox_group`/`m2o_state`/`m2o_country`/`table`/`static`). Los `key` se verificaron **uno por uno contra el `osp_form_crop.xml` real** (no se confió solo en `FORM_SPEC_CROP.md`, que se escribió antes de la implementación final) — se leyó el archivo completo para esta tarea.
- **`report/osp_crop_report.py`** — método `osp.request.get_crop_report_sections()`: recorre ese manifest y lo resuelve contra `self.form_data`, devolviendo una estructura ya lista para imprimir (resuelve nombres de `res.country`/`res.country.state` a partir del id guardado, decodifica el JSON de las 12 tablas dinámicas y descarta filas completamente vacías, arma la lista de seleccionados de cada `checkbox_group`).
- **`report/osp_report_templates.xml`** — el template QWeb es **genérico**: no conoce ninguna pregunta por su nombre, solo sabe pintar cada `kind` (`text`, `textarea`, `options`, `checkbox`, `checkbox_group`, `table`, `static`). Si se agrega una pregunta nueva al formulario web, **alcanza con agregarla en `osp_crop_report_data.py`** — el template no se toca.
- **Encabezado/pie de página**: estructura estándar de reportes Odoo (`web.html_container` → `div.page` con `div.header`/`div.article`/`div.footer`). El header repite el logo en cada página; el footer usa los spans nativos de wkhtmltopdf `<span class="page"/>`/`<span class="topage"/>` (paginado automático) + el campo `form_template_id.version` del registro (ej. "Org-007 R7 1/9/2024", ya sembrado en `data/osp_form_template_data.xml`).
- **Acceso**: botón **"Descargar OSP"** en el header de la ficha admin (`osp_menu_views.xml`, junto a "Marcar como Completo", `type="action"` referenciando `%(osp_management.action_report_osp_crop)d` — solo visible si `state == 'submitted'`) y link **"PDF"** en la columna Action de `/my/osp` (`osp_portal_templates.xml`, solo visible si `osp.state == 'submitted'`), apuntando directo a `/report/pdf/osp_management.report_osp_crop_document/<id>`.
- **Orden de carga en el manifest**: `report/osp_report_templates.xml` se cargó **antes** que `views/osp_menu_views.xml` a propósito — el botón `type="action"` con `%(xmlid)d` necesita que ese xmlid ya exista al parsearse esa vista.
- **Dependencias nuevas**: `web` (se usa `web.html_container` directamente).

**Limitaciones conocidas / posibles ajustes tras la primera prueba visual** (no se pudo renderizar/previsualizar el PDF en este entorno, así que es esperable 1-2 rondas de ajuste):
1. Márgenes/paginación de wkhtmltopdf no se probaron contra una instancia real — si el header/footer se ven muy pegados al contenido o se cortan, hay que ajustar el `paperformat` del reporte (hoy usa el default de Odoo).
2. Los `checkbox_group` (ej. "Select all that applies") solo listan las opciones **seleccionadas** con `☑` — no reproducen la lista completa de opciones no marcadas con `☐` (a diferencia de los Sí/No, que sí muestran ambas opciones). Habría que enumerar la lista completa de opciones por cada `checkbox_group` en `osp_crop_report_data.py` si se quiere el mismo nivel de fidelidad ahí también.
3. Los `label` de las preguntas de las Secciones 5–20 se tomaron del texto real de `osp_form_crop.xml` verificado línea por línea durante esta tarea — se prestó atención a que coincidan exactamente, pero si algo se ve distinto al comparar contra el formulario web, es fácil de corregir (un solo archivo, `osp_crop_report_data.py`).

## 16. Backend en inglés fijo (IMPLEMENTADO — 18/ago)

**Decisión del usuario**: el **backend** (perfil Administrador de OSP) queda **siempre en inglés**, sin importar el idioma que tenga seleccionado el usuario — ya no es bilingüe en_US/es_MX como se había construido antes. El **portal del cliente** (`/my/osp`, `osp_portal_templates.xml`) **sigue bilingüe** (inglés por defecto, español vía `i18n/es_MX.po`) — eso no se tocó. El formulario Crop en sí (`osp_form_crop.xml`) tampoco se tocó, como siempre.

- Se reescribió directo en el código (ya no vía `.po`) todo el texto que estaba en español: `_description`/`string=`/`help=` de los 3 modelos (`models/osp_request.py`, `models/osp_form_template.py`), toda la vista backend (`views/osp_menu_views.xml`), nombre/descripción del grupo y categoría de seguridad (`security/osp_security.xml`), nombre/summary/description del módulo (`__manifest__.py`), y los mensajes de chatter/notificación que solo lee el admin (`controllers/portal.py` — los `_()` de `_do_client_submit`, `_do_public_submit`, el guardado del admin, y las descripciones de adjuntos).
- **`i18n/en_US.po` se eliminó** (ya no tiene sentido — la fuente ya es inglés, no hay nada que traducir *a* inglés).
- **Migración `migrations/17.0.1.1.3/post-migrate.py`**: como ya habíamos forzado por ORM (`migrations/17.0.1.0.8`) que ciertos campos `model:X,Y` (nombre de módulo, categoría, grupo, menús, acciones, etiquetas de campo, opciones de Selection) mostraran **español** para usuarios con ese idioma, esas traducciones por idioma quedaban "pegadas" y no se limpian solas al cambiar el texto fuente. Este script sobreescribe **todos los idiomas instalados** con el mismo texto en inglés, para que quede uniforme sin importar el idioma del usuario — mismo patrón ya probado (`with_context(lang=...).write(...)`), esta vez convergiendo todo a un solo valor.
- 🐛 **Casi-incidente durante esta tarea**: al ejecutar `rm` sobre `i18n/en_US.po`, se descubrió que la carpeta **`i18n/` completa ya no existía en disco** (incluyendo `es_MX.po`, que **no** se pidió tocar) — border ajeno a esta sesión, no causado por este cambio. Se restauró `es_MX.po` completo desde el último commit que lo tenía (`git show a270145:osp_management/i18n/es_MX.po`), verificando que incluyera las entradas más recientes ("Last Updated", "Download PDF") antes de continuar. **Lección**: si algo similar vuelve a pasar, `git status`/`git log -- <archivo>` es la forma rápida de confirmar si un archivo "desaparecido" es recuperable desde el historial antes de asumir que hay que rehacerlo.
- Versión del manifest: `17.0.1.1.3`.

## 17. Backend vuelve a ser bilingüe vía es_MX.po exportado (IMPLEMENTADO — 18/ago)

**Contra-orden parcial del punto 16**: el usuario exportó su propio `i18n/es_MX.po` completo desde Odoo (Ajustes → Traducciones → Exportar) — 606 términos, junto con `i18n/osp_management.pot` (el molde, **nunca se toca**). Pidió traducir ese archivo a español, **excepto las preguntas del formulario Crop**. Es decir: el backend deja de ser "solo inglés siempre" y vuelve a ser bilingüe — pero ahora vía este `.po` que el propio usuario generó y mantiene, no uno que yo escribí desde cero.

- **456 de las 606 entradas son del formulario Crop** (`model_terms:ir.ui.view,arch_db:osp_management.osp_form_crop_body`) — se dejaron con `msgstr ""` (vacío = sin traducir), tal como se pidió.
- **~40 entradas son campos genéricos heredados de `mail.thread`/`mail.activity.mixin`** (Followers, Activities, Created by, Message Delivery error, etc.) — se dejaron vacías a propósito: Odoo ya trae su propia traducción al español para estos campos estándar (vienen del módulo `mail`, no de `osp_management`), traducirlos aquí sería trabajo redundante sin ningún efecto adicional.
- **~95 entradas restantes SÍ se tradujeron**: vistas backend, campos propios, menús, acciones, chatter, portal (`portal_my_osps`, `portal_my_home_osp_raw`, `public_osp_thankyou`), y el texto fijo del reporte PDF (`report_osp_crop_document` — "Page X of Y", no las preguntas).
- Se dejaron sin traducir a propósito 3 casos especiales: **"Primus Auditing Ops"** (nombre de marca), y **2 textos que ya eran fuente en español** desde antes (`Cargando Formulario:`, `La versión web...`, `Volver a mi lista`, `No hay planes de manejo orgánico creados todavía...` — la placeholder de formularios no construidos; traducir español→español no aplica).
- 🐛 **Detalle encontrado de paso**: el nombre interno del reporte (`ir.actions.report.name` en `report/osp_report_templates.xml`) se había quedado como "Descargar OSP" cuando pasamos el backend a inglés (punto 16) — se corrigió a "Download OSP", y ya tiene su traducción a "Descargar OSP" en el `.po`.
- ⚠️ **Consecuencia técnica importante, ya explicada al usuario antes de traducir**: de las ~95 entradas traducidas, las de tipo `model_terms:ir.ui.view` (botones, títulos de grupo, placeholders — recargan solas en cada `-u`) **sí van a mostrarse en español** para un admin con ese idioma seleccionado. Las de tipo `model:X,Y` (menús, acciones, `field_description`, opciones de `Selection`, nombre de módulo/grupo/categoría) **probablemente NO cambien** de inglés a español, porque `migrations/17.0.1.1.3` ya forzó por ORM que esos campos específicos mostraran inglés en TODOS los idiomas — esa escritura previa tiene prioridad sobre lo que traiga el `.po`. Si el usuario quiere que esos también vuelvan a español, hace falta una migración nueva que revierta/complemente la de `17.0.1.1.3` (mismo patrón, escribiendo el texto en español en vez de en inglés) — no se hizo todavía porque no se pidió explícitamente.
- ⚠️ **Casi-incidente ya documentado en el punto 16** (recordatorio): al trabajar en `i18n/` hay que tener cuidado — la carpeta completa desapareció una vez de forma ajena a esta sesión.
- Versión del manifest: `17.0.1.1.4`.

## 18. Formulario "Handler" implementado + generalización del reporte PDF a multi-formulario (IMPLEMENTADO — 18/ago)

**Segundo formulario construido** (después de Crop), y primero en probar que la arquitectura generalizaba bien a un formulario nuevo sin tocar el motor genérico. Spec completa en `FORM_SPEC_HANDLER.md` (extraída directo de `Handler.docx`, 15 secciones — más corto que Crop). Decisiones cerradas con el usuario antes de programar (ver el propio FORM_SPEC_HANDLER.md, "Decisiones confirmadas"): State/Country como selects reales (igual que Crop), Sección 7b (Storage) como 4 grupos de campos fijos en vez de tabla, 11c/13d con control Sí/No agregado (el Word no lo traía) + textbox de explicación condicional, campo Date agregado en la Afirmación (Sección 15) aunque el Word no lo pide.

- **`views/osp_form_handler.xml`** (nuevo) — mismo patrón que Crop: `osp_form_handler_body` (contenido real) + dos wrappers delgados (`portal_osp_form_handler` con `portal.portal_layout`, `public_osp_form_handler` con `website.layout`). 15 secciones, 3 tablas dinámicas (`4b_sites_json`, `5d_products_json`, `9a_inputs_json`) y la Sección 7b con 4 grupos de campos fijos armados vía `t-foreach` sobre una lista Python de tuplas `(row_key, row_label, editable_label)` — sin inventar un componente nuevo, cada campo de cada fila fija es un `osp-input` normal con `name="7b_<row_key>_<columna>"`.
- **`static/src/js/osp_form.js`** — se agregaron 3 entradas a `TABLE_CONFIGS` (`handler_sites`, `handler_products`, `handler_inputs`) con sus propios `jsonInputId`/`tbodyId`/`addBtnId`, distintos de los de Crop aunque el concepto se parezca (ej. "sites") — conviven en el mismo objeto compartido sin pisarse, porque `initDynTable()` hace no-op en cualquier página que no tenga ese `jsonInput` en el DOM. **No hizo falta tocar nada más del motor** (condicionales, cascada país/estado, guardado público/portal, hidratación desde localStorage) — todo ya era genérico por diseño.
- **`controllers/portal.py`** — los 3 puntos que antes tenían un `if template.technical_code == 'form_crop':` ahora usan un diccionario `FORM_BODY_TEMPLATES`/`PUBLIC_BODY_TEMPLATES` (`technical_code -> xmlid del template QWeb`) en `portal_osp_form_new`, `portal_osp_form` y `OSPPublicController._render_public_form` — agregar un formulario nuevo a futuro es agregar un renglón al diccionario correspondiente, no una rama `if/elif` nueva. `OSPPublicController.PUBLIC_FORM_SLUGS` ya tiene `'handler': 'form_handler'` activo (antes comentado) — liga pública propia: `/osp/public/handler`.
- **Generalización del reporte PDF** (antes solo existía para Crop, con todo el switch de tipos de campo embebido en `osp_crop_report.py`): se extrajo esa lógica a **`report/osp_report_common.py`** (nuevo) — método `_resolve_report_sections(sections_manifest)`, que recibe cualquier manifest con el mismo formato que `CROP_REPORT_SECTIONS` y lo resuelve contra `self.form_data`. `osp_crop_report.py` quedó reducido a `get_crop_report_sections()` (una línea, llama al motor común con `CROP_REPORT_SECTIONS`), y el nuevo `report/osp_handler_report.py` es análogo con `get_handler_report_sections()` y `HANDLER_REPORT_SECTIONS` (`report/osp_handler_report_data.py`, nuevo).
  - **Nuevo tipo de campo en el manifest**: `fixed_rows` — para secciones como la 7b de Handler (filas fijas armadas desde varias claves sueltas de `form_data`, no desde un solo blob JSON). Lo resuelve `_report_fixed_rows()` en el motor común, sintetizando una columna extra `__label` con el nombre de cada categoría — el template QWeb del reporte no necesitó ningún cambio porque ya sabía pintar `kind: 'table'` de forma genérica (recorre `field['columns']`/`row.get(col[0], '')`, sin saber qué campo es cuál).
  - **Despacho automático por convención de nombre**: `get_report_sections()` (en `osp_report_common.py`, es el método que llama el template QWeb) ya no tiene ningún `if technical_code == ...` — toma `form_template_id.technical_code`, le quita el prefijo `form_`, y llama `get_<resto>_report_sections()` vía `getattr`. Agregar un formulario nuevo a futuro (ej. Cultivo, `technical_code='form_cultivo'`) solo requiere que exista un método `get_cultivo_report_sections()` en algún archivo — cero cambios en `osp_report_common.py` ni en el template.
  - **`report/osp_report_templates.xml`**: el template QWeb y la `ir.actions.report` se renombraron de específicos-de-Crop a genéricos — `report_osp_crop_document` → **`report_osp_document`**, `action_report_osp_crop` → **`action_report_osp`** (el `name` visible ya decía "Download OSP", genérico desde antes). El título/encabezado del PDF ahora usa `o.form_template_id.name` en vez del texto fijo "Crop", y el pie de página arma "Organic System Plan — `<nombre del formulario>` | Version: ...". Se actualizaron las 2 referencias a los xmlids viejos: el botón "Download OSP" en `osp_menu_views.xml` y el link "PDF" del portal en `osp_portal_templates.xml`.
- **`data/osp_form_template_data.xml`**: no requirió cambios — el registro de catálogo para Handler (`technical_code='form_handler'`) ya estaba sembrado desde antes (ver punto 11).
- Versión del manifest: `17.0.1.2.0`.
- **Lección para el próximo formulario** (Cultivo/Manejo o Proceso/Comercializador): el checklist de continuidad del punto 11 sigue vigente, pero ya no hace falta "generalizar el botón Descargar OSP" como se advertía ahí — eso ya se hizo aquí. El trabajo real de cada formulario nuevo se reduce a: su `FORM_SPEC_<NOMBRE>.md`, su `views/osp_form_<nombre>.xml`, sus entradas en `TABLE_CONFIGS` si tiene tablas dinámicas, sus 2 renglones en los diccionarios de `controllers/portal.py`, su renglón en `PUBLIC_FORM_SLUGS`/`PUBLIC_BODY_TEMPLATES`, y su `osp_<nombre>_report_data.py` + `get_<nombre>_report_sections()` de una línea.

## 19. Formulario "Handler (Trader)" implementado — tercer formulario, primera prueba real de la generalización (IMPLEMENTADO — 18/ago)

**Tercer formulario construido**, y el primero en probarse en vivo por el usuario antes de pedir el siguiente ("lo probé y funciona" — sobre Handler, confirmado antes de compartir este `.docx`). Spec completa en `FORM_SPEC_HANDLER_TRADER.md`. Es el formulario más corto (10 secciones) porque es **para operaciones sin instalación física** — el propio Word lo dice en una nota introductoria, mostrada como texto fijo al inicio del formulario web.

- **Punto real de ambigüedad encontrado y resuelto con el usuario**: la Sección 6 del Word original reutiliza las letras `6c`-`6f` **dos veces** para preguntas completamente distintas (Waste Management/Energy Conservation, y luego otra vez para Water Use) — un error de numeración real del documento fuente, no algo resoluble por inferencia. Se le preguntó al usuario cómo distinguir el segundo grupo; **decisión: continuar la numeración natural** (`6g`-`6j` para todo el bloque de Water Use) en vez de inventar un prefijo artificial (`6w`). Precedente útil: cuando un Word fuente tiene un error de numeración real (letras repetidas, huecos), se pregunta en vez de asumir — ya pasó una vez con los controles Sí/No faltantes de Handler (11c/13d).
- Otras diferencias de contenido reales vs. Handler (no ambigüedades, solo el formulario siendo más corto por no tener instalación física): sin Sección de Equipment/Sanitation ni de Inputs ni de Transportation ni de Pest Management por separado — todo lo de integridad orgánica se combina en una sola Sección 7 ("Maintenance of Organic Integrity" con subsecciones Storage & Shipping / Quality Testing / Packaging). La tabla de sitios (4a) tiene una columna combinada "Address: City, State, Zip" en vez de las 3 columnas separadas de Handler. La tabla de productos (5d) no tiene la columna "¿Empacará con este ID Mark?". La Sección 10 (Affirmation) sí trae Name/Signature/**Date** completos en el Word — a diferencia de Handler, no hizo falta agregar el campo Date manualmente.
- **`views/osp_form_handler_trader.xml`** (nuevo) — mismo patrón body+wrappers. 10 secciones, 2 tablas dinámicas (`4a_sites_json`, `5d_products_json`).
- **`static/src/js/osp_form.js`** — 2 entradas nuevas en `TABLE_CONFIGS` (`trader_sites`, `trader_products`). Nota: `trader_products` comparte el mismo `jsonInputId` (`5d_products_json`) que `handler_products` de Handler (mismo concepto/key, columnas distintas) — es seguro porque `renderDynTable()` corta temprano si el `tbody` de esa config no existe en la página actual, así que solo el config cuyo `tbody` sí está presente llega a escribir en el input compartido; nunca se pisan entre sí.
- **`controllers/portal.py`** — `form_handler_trader` agregado a los 2 diccionarios `FORM_BODY_TEMPLATES` (portal) y a `PUBLIC_FORM_SLUGS`/`PUBLIC_BODY_TEMPLATES` (público) — liga pública activa: `/osp/public/handler-trader`.
- **Reporte PDF** — mismo patrón de una línea: `report/osp_handler_trader_report_data.py` (manifest) + `report/osp_handler_trader_report.py` (`get_handler_trader_report_sections()`). Cero cambios al motor común ni al template — el despacho por convención de nombre (`get_report_sections()`) ya lo resuelve solo.
- Versión del manifest: `17.0.1.3.0`.

## 20. Pendientes conocidos

- Plantillas **"Cultivo"**, **"Manejo o Proceso"**, **"Comercializador"**: el usuario las subirá después — por ahora existen "Crop", "Handler" y "Handler (Trader)"; otros `technical_code` caen al placeholder genérico sin construir.
- Los marcadores `_attachment_needed` (ver `FORM_SPEC_*.md`) siguen siendo solo checkboxes informativos por pregunta — la subida real de archivos (punto 9) es general (una sola sección "Attachments"), no está ligada campo por campo a esos marcadores. Si se necesita adjuntar un archivo específico a una pregunta puntual, habría que extender esto.
- Embed del iframe admin (punto 7): limpiar el cascarón duplicado del portal dentro del iframe (modo `?embed=1`) — mejora visual, no bloqueante.
- Notificación al admin (punto 8): solo cubre submits del cliente; no se pidió notificar sobre guardados del propio admin.
- Formulario público (punto 14): sin protección anti-bot, sin captcha, sin alta automática de portal al vincular cliente — todo por decisión explícita del usuario, no por descuido. Si en el futuro hay abuso real (envíos basura) o se quiere agilizar el alta de portal, ya está identificado qué tocar.
- Reporte PDF (puntos 15, 18, 19): márgenes/paginación sin probar visualmente; `checkbox_group` no muestra opciones no marcadas; nombres de adjuntos no se listan en el PDF (a propósito).
- Backend bilingüe (punto 17): las traducciones tipo `model:X,Y` (menús, acciones, `field_description`, opciones de Selection, nombre de módulo/grupo) probablemente sigan en inglés pase lo que pase, porque `migrations/17.0.1.1.3` las forzó por ORM en todos los idiomas — el usuario confirmó (18/ago) que así está bien, no se pidió una migración reversora.
- Handler (Trader) no se probó visualmente contra una instancia real todavía — es esperable alguna ronda de ajuste de maquetado/labels tras la primera prueba (como pasó con Crop y con Handler).

## 21. Cómo pedir ayuda de forma efectiva sobre este proyecto

- Este es un módulo de Odoo 17, desplegado vía **Odoo.sh** (rama de staging llamada `test`).
- Al reportar un bug del formulario, lo más útil es: captura de pantalla + **contenido de la consola del navegador** (F12 → Console), ya que varios bugs reales no lanzan errores rojos, solo dejan de ejecutar código silenciosamente (ver punto 10.2).

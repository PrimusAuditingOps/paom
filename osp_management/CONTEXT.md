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
│   └── osp_form_crop.xml        # EL FORMULARIO "CROP" COMPLETO (QWeb, portal)
└── static/src/js/
    └── osp_form.js         # Lógica JS del formulario Crop (tablas dinámicas, guardado AJAX)
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
| Handler | `form_handler` | ⏳ Pendiente (el usuario subirá el PDF/spec después) |
| Handler (Trader) | `form_handler_trader` | ⏳ Pendiente |
| Cultivo | `form_cultivo` | ⏳ Pendiente |
| Manejo o Proceso | `form_manejo_proceso` | ⏳ Pendiente |
| Comercializador | `form_comercializador` | ⏳ Pendiente |

Para cada uno nuevo: agregar su rama en `portal_osp_form` (`controllers/portal.py`) junto a la de `form_crop`, su template QWeb propio (`views/osp_form_<nombre>.xml`, siguiendo el patrón de `osp_form_crop.xml`), y su archivo `FORM_SPEC_<NOMBRE>.md` de referencia — todos sin tocar los ya construidos.

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
- 🐛 **17.0.1.0.6 tampoco funcionó** (probado 17/ago): el backend siguió en español pese al `overwrite=True`. En vez de seguir dependiendo de que el importador de `.po` resuelva bien esos registros "model:X,Y" (cuya mecánica interna no se pudo verificar sin una instancia real), **`migrations/17.0.1.0.7/post-migrate.py`** escribe la traducción **directo en cada registro vía el ORM** con `record.with_context(lang='en_US').write({...})` — el mismo mecanismo que usa la UI cuando un humano traduce un campo a mano con el ícono de "globo", sin pasar por el importador de `.po` en absoluto. Para las etiquetas de campo (`ir.model.fields`) busca el registro por `(model, name)` en vez de por external id, evitando depender de que el xmlid auto-generado exista con el patrón esperado. Cubre: shortdesc del módulo, categoría, grupo, los 5 menús, las 3 acciones (+ su `help`), 17 etiquetas de campo de `osp.request`, 5 de `osp.service`/`osp.form.template`, y las 4 opciones de `Selection`. Versión bump a `17.0.1.0.7` — **este es el que hay que probar ahora**.

## 13. Pendientes conocidos

- Plantilla **"Handler"**: el usuario la subirá después — por ahora solo existe "Crop"; otros `technical_code` caen al placeholder genérico sin construir.
- Los ~18 marcadores `_attachment_needed` (ver `FORM_SPEC_CROP.md`) siguen siendo solo checkboxes informativos por pregunta — la subida real de archivos (punto 9 de arriba) es general (una sola sección "Attachments"), no está ligada campo por campo a esos marcadores. Si se necesita adjuntar un archivo específico a una pregunta puntual, habría que extender esto.
- Embed del iframe admin (punto 7): limpiar el cascarón duplicado del portal dentro del iframe (modo `?embed=1`) — mejora visual, no bloqueante.
- Notificación al admin (punto 8): solo cubre submits del cliente; no se pidió notificar sobre guardados del propio admin.

## 14. Cómo pedir ayuda de forma efectiva sobre este proyecto

- Este es un módulo de Odoo 17, desplegado vía **Odoo.sh** (rama de staging llamada `test`).
- Al reportar un bug del formulario, lo más útil es: captura de pantalla + **contenido de la consola del navegador** (F12 → Console), ya que varios bugs reales no lanzan errores rojos, solo dejan de ejecutar código silenciosamente (ver punto 10.2).

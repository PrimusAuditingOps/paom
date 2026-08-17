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

## 6. Modo Administrador de OSP / solo-lectura (IMPLEMENTADO — 17/ago)

- Ruta `/my/osp/form/<id>` y `/my/osp/save/<id>` en `portal.py` ahora aceptan **dos tipos de usuario**: el cliente dueño del registro (`partner_id` coincide), o cualquier usuario del grupo `osp_management.group_osp_administrator`.
- **Cliente**: puede editar/guardar mientras `state == 'draft'`. Una vez que hace Submit (`state == 'submitted'`), el formulario queda **de solo lectura** — el backend rechaza más guardados suyos y el frontend deshabilita todos los inputs (`window.OSP_READONLY`, aplicado en `osp_form.js`).
- **Administrador de OSP**: puede entrar y editar el formulario **aunque ya esté `submitted`**, vía el botón "Ver Formulario Web" (`action_open_portal_form` en `osp_request.py`, ya implementado — redirige a `/my/osp/form/<id>`). Solo tiene botón de guardar (relabeled "Save changes"), **nunca Submit**. Cada guardado del admin se registra en el chatter del registro (`record.message_post(...)`).
- **Limitación conocida**: el modo solo-lectura se aplica vía JS (deshabilita inputs en el cliente), no hay un `readonly`/`disabled` a nivel de renderizado QWeb por cada campo individual (habría sido ~300 atributos extra). Si se necesita una garantía más fuerte a futuro (por si JS falla), habría que reforzarlo server-side.

## 6. Lecciones aprendidas / bugs ya corregidos (para no repetirlos)

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

## 7. Pendientes conocidos (no urgentes, mencionados pero no iniciados)

- ~~Quitar el botón "Nuevo" de la vista de lista del admin~~ → ✅ resuelto (17/ago): `action_osp_request` en `osp_menu_views.xml` ahora tiene `context="{'create': False}"`, que oculta "Nuevo" tanto en la vista lista como en el form (los registros solo deben aparecer vía submit desde el portal, nunca creados manualmente ahí).
- Construir el **widget de detalle** para que el admin vea de forma legible (no como JSON crudo) todo lo que el cliente respondió — sigue pausado. Ahora es más urgente que antes, dado que el formulario completo ya tiene ~300 campos + 12 tablas guardados en `form_data`.
- Decidir el layout visual del formulario cuando lo abre el admin (hoy reutiliza `portal.portal_layout`, el mismo "cascarón" que ve el cliente externo — funciona pero no es la decisión de diseño definitiva).
- Notificación al administrador cuando el cliente hace submit (correo, actividad, chatter) — no se ha discutido a fondo.
- Solo existe la plantilla "Crop"; otros `technical_code` caen al placeholder genérico sin construir.
- Los ~18 marcadores `_attachment_needed` (ver `FORM_SPEC_CROP.md`) son solo checkboxes informativos — el manejo real de subida de archivos sigue fuera de alcance.

## 8. Cómo pedir ayuda de forma efectiva sobre este proyecto

- Este es un módulo de Odoo 17, desplegado vía **Odoo.sh** (rama de staging llamada `test`).
- Al reportar un bug del formulario, lo más útil es: captura de pantalla + **contenido de la consola del navegador** (F12 → Console), ya que varios bugs reales no lanzan errores rojos, solo dejan de ejecutar código silenciosamente (ver punto 6.2).

# Guía general de desarrollo de módulos Odoo (aprendida en `osp_management`)

> Este documento **no es específico de OSP**. Recoge patrones, convenciones y
> lecciones generales de desarrollo de módulos Odoo 17 en este repo/entorno
> (Odoo.sh), extraídas durante la construcción de `osp_management` +
> `osp_management_portal_only`. Léelo antes de empezar (o de dar
> mantenimiento a) cualquier otro módulo de este monorepo — la idea es no
> repetir los mismos incidentes ni redescubrir los mismos patrones desde
> cero. Para el detalle específico de OSP, ver `osp_management/CONTEXT.md`.

## 1. Aislar extensiones a modelos núcleo (`res.users`, `res.partner`, `res.company`) en un módulo satélite

**Regla**: cualquier campo nuevo que se agregue a un modelo **núcleo, consultado en cada request** (`res.users`, `res.partner`, `res.company`, y similares) debe vivir en un **módulo delgado y separado** del módulo principal de la feature — nunca mezclado con el modelo/las tablas propias del proyecto.

**Por qué**: un modelo núcleo se consulta en absolutamente cada página (login, idioma, empresa activa, cron jobs). Si un build/`-u` no corre limpio hasta el final y ese campo queda declarado en Python pero sin su columna en la base de datos, **el sitio entero se cae para todos los usuarios**, no solo la parte relacionada a esa feature. Un campo nuevo en un modelo propio del proyecto no carga ese mismo riesgo — un desfase de esquema ahí solo rompe las páginas de esa feature puntual.

**Cómo aplicarlo**: el módulo satélite puede depender del módulo principal (`depends: [..., 'modulo_principal']`) para reutilizar sus ids/templates si hace falta, pero **nunca al revés**. Ejemplo real: `osp_management_portal_only` (campo `osp_portal_only` en `res.users` + su vista + su plantilla de ocultamiento) depende de `osp_management`, no lo contrario. Desinstalar el módulo satélite en cualquier momento no debe romper nada del módulo principal.

**Cuidado al separar**: si el módulo principal tenía una plantilla que mezclaba funcionalidad núcleo (que debe seguir funcionando sin el satélite) con la funcionalidad exclusiva del satélite, al separar hay que **separar también la plantilla en dos partes** — no copiar el archivo completo al satélite y borrar el original del principal (eso deja al módulo principal dependiendo funcionalmente de un módulo opcional, invirtiendo la relación de dependencia esperada). Ver `osp_management/CONTEXT.md` §37 para el incidente real y la corrección.

## 2. Número de versión del manifest: no es funcional, es una decisión de release

El campo `version` de `__manifest__.py` **no afecta si un `-u`/install funciona o no** — es metadata (aparece en la lista de Apps) y solo dispara qué carpetas de `migrations/<version>/` corren. Durante desarrollo activo en un staging de pruebas, **no hay obligación de subirlo en cada cambio** — de hecho, subirlo constantemente puede hacer que el número de versión en staging quede muy adelantado respecto a lo que realmente se quiere liberar a producción. Deja que quien decide el release elija manualmente cuándo y a qué número subir la versión.

## 3. Diagnóstico de builds fallidos en Odoo.sh

- **`update.log` ≠ el log de tests.** Un `update.log` que termina en "Registry loaded" / "Modules loaded" es un **éxito** de la actualización de esquema — no significa que el build completo pasó. Si Odoo.sh marca el build como "failed" con el mensaje *"At least one test failed when loading the modules (X)"*, ese mensaje viene de una fase **separada** (`--test-enable`), y el traceback real hay que buscarlo en `odoo.log`, con `Ctrl+F` sobre `FAIL:` o `Traceback`.
- **El módulo señalado en el mensaje de error no siempre es el culpable real.** Odoo.sh etiqueta el fallo con el módulo que disparó el `-u`, pero el test que realmente falla puede pertenecer a **cualquier otro módulo ya instalado** en la misma base — especialmente en un monorepo con decenas de módulos custom como este. No asumir causalidad sin ver el traceback completo.
- **Un traceback real (`UndefinedColumn: ... does not exist`) en cada request** significa que el código (definición del modelo en Python) y el esquema de la base de datos están desincronizados — normalmente porque un build no llegó a correr su `-u` completo (p. ej. porque el paso de tests lo abortó a medio camino). Esto rompe **el sitio entero**, no solo el módulo nuevo, si el campo está en un modelo núcleo (ver punto 1).
- **Recuperación sin perder datos**: en vez de desinstalar/reinstalar el módulo completo (lo cual borra las tablas propias del módulo, incluidos todos sus registros), correr directo en la terminal **Shell** de Odoo.sh:
  ```bash
  odoo-bin -u <modulo> --stop-after-init -d <nombre_de_la_base>
  ```
  Esto sincroniza el esquema sin pasar por el filtro de tests (`--test-enable` no está activo en este comando manual), y sin tocar ningún dato de las tablas propias del módulo.

## 4. Patrón "catálogo de documentos": cuando un módulo maneja varios tipos de un mismo formulario/documento

Si un módulo va a manejar **N variantes de un mismo tipo de documento** (formularios, reportes, plantillas...), evitar construir N copias independientes de la lógica. Patrón usado en `osp_management` para sus 6 formularios:

- **Diccionario `technical_code` → xmlid de plantilla**, usado en el/los controlador(es) para resolver qué renderizar — agregar un tipo nuevo es agregar una línea al diccionario, no una rama de código nueva.
- **Un solo template QWeb de "cuerpo"** por tipo de documento, reutilizado por **todos los contextos** donde se muestra (portal autenticado, público sin login, admin embebido en iframe) — envuelto por "wrappers" delgados distintos según el contexto. Esto garantiza que las 3 vistas **nunca puedan divergir entre sí**, porque literalmente es el mismo HTML.
- **Motor de reporte PDF genérico + manifest declarativo por tipo**: una sola función que sabe recorrer una lista de secciones/campos con tipos (`text`, `yn`, `table`, `checkbox`, `static`...) y generar el PDF, más un archivo `<tipo>_report_data.py` por variante que solo declara la estructura (label, key, type) — nunca HTML repetido a mano. Agregar un tipo de documento nuevo = escribir su manifest, no tocar el motor.
- **Motor de tablas dinámicas genérico en JS**, dirigido por un objeto `TABLE_CONFIGS` (columnas + tipos por tabla) en vez de HTML+JS escritos a mano por tabla. Extenderlo con un tipo de columna nuevo (ej. `checkbox`) beneficia a **todas** las tablas que alguna vez lo necesiten, no solo la que lo motivó.
- **Mecanismo genérico de campos condicionales** (`data-conditional-field`/`data-conditional-value` + una sola función JS que los observa) en vez de lógica de mostrar/ocultar hecha a mano por campo.
- **Convención de nombres + escaneo genérico** para campos de propósito especial: ej. sufijo `_attachment_needed` en el `name`/`id` de un checkbox, detectado automáticamente tanto en JS (`querySelectorAll('input[id$="_attachment_needed"]')`) como en un catálogo Python — permite construir funcionalidad transversal (como un checklist de "qué documentos dijiste que ibas a adjuntar") sin mantener una lista hardcodeada en tres lugares distintos.

## 5. Seguridad y control de acceso

- **Regla estándar de multi-compañía** (`ir.rule`): `['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]` — un `company_id` vacío queda visible para cualquier compañía, por convención nativa de Odoo (útil para no tener que hacer backfill manual de registros viejos al agregar multi-compañía a un modelo que no la tenía).
- **Grupos de seguridad "casi iguales, con una diferencia puntual"**: centralizar la verificación (`has_group(...)`) en **un solo método helper**, reutilizado en todos los puntos donde aplica — nunca repetir `has_group('modulo.grupo_admin')` copiado en N controladores/métodos distintos. Si más adelante se agrega un segundo grupo con el mismo trato, alcanza con tocar el helper una vez. (Nota: el helper se duplica una sola vez entre modelo y controlador si uno tiene acceso a `request` y el otro no — pero sigue siendo un único punto de verdad por capa.)
- **Ocultar navegación ≠ restringir acceso real.** Si la feature es "que el usuario no vea la opción X" mediante CSS/JS, dejar documentado explícitamente que es solo cosmético — no asumir que reemplaza una regla de seguridad (`ir.rule`) real. Si de verdad hace falta bloquear el acceso, es una decisión aparte y consciente.
- **Multi-compañía en formularios públicos/portal**: `request.website.company_id` es la forma confiable de detectar la compañía correcta según el dominio por el que entró el visitante — pero solo funciona bien si **cada dominio de producción tiene su propio registro `Website` mapeado a su compañía**. Un dominio sin ese mapeo explícito (ej. un subdominio de staging) cae al sitio "por defecto" de la instancia, lo que puede parecer un bug pero es el comportamiento esperado de Odoo.

## 6. Rutas públicas (`auth="public"`) sin login

- **Anti-abuso con "fail-open"**: cualquier capa nueva de protección (captcha, límite de intentos, etc.) debe degradar de forma segura si no está configurada — es decir, si el administrador todavía no la activó, el flujo público debe seguir funcionando normal, en vez de romperse en silencio. No bloquear usuarios legítimos por una mala configuración de la capa de seguridad.
- **Ventana de acceso reutilizable**: cuando un registro público existe antes de estar vinculado a un cliente real (ej. `not record.partner_id`), esa misma condición de "todavía es público" debe ser la **única y consistente** puerta de acceso en **todas** las rutas relacionadas a ese registro (subir adjuntos, descargar PDF, etc.) — no reinventar el criterio en cada ruta nueva.
- **`_render_qweb_pdf()` en Odoo 17** se llama sobre el **modelo** `ir.actions.report`, pasándole el xmlid/id del reporte como primer argumento (`env['ir.actions.report']._render_qweb_pdf('modulo.xmlid_reporte', res_ids)`) — **no** sobre un recordset ya resuelto del reporte (`report_action._render_qweb_pdf(res_ids)` produce un 500 silencioso).

## 7. Herencia de vistas XML: puntos de inserción riesgosos vs. seguros

Insertarse en un punto **"concurrido"** de una vista compartida por muchos módulos (ej. justo después de un campo como `login` en el formulario de Usuario) es más propenso a chocar con otro módulo que también lo modifique — la inserción de uno puede desalinear el anclaje (xpath) del otro, y el error resultante puede señalar al módulo equivocado, dificultando el diagnóstico.

Cuando exista ese riesgo (o ya se haya confirmado un choque real), preferir un punto de inserción **puramente aditivo** — por ejemplo, agregar una pestaña (`<page>`) nueva a un `<notebook>` existente en vez de insertarse entre campos ya existentes. No depende de ni altera ninguna estructura de la que otro módulo pueda depender.

*(Nota honesta: en el incidente real que motivó esta entrada, la causa final resultó ser otra — desfase de esquema, ver punto 3 — no un choque de vistas. Aun así, el principio de "preferir el punto de inserción menos concurrido cuando sea razonablemente posible" sigue siendo una buena práctica defensiva de bajo costo.)*

## 8. Validar cambios sin acceso directo a un servidor Odoo corriendo

Herramientas disponibles en este entorno (sin Python/pandoc/soffice ni Odoo local):
- **XML bien formado**: PowerShell `[xml]$doc = Get-Content -Raw -Encoding UTF8 <archivo>` — falla con un error claro si el XML no es válido.
- **Sintaxis JS**: `node --check <archivo>.js`.
- **Sanidad básica de un archivo Python** (sin intérprete Python disponible): un script corto en Node.js que cuenta profundidad de `[`, `(`, `{` a lo largo del archivo y confirma que termina en 0 — detecta paréntesis/corchetes desbalanceados tras una edición.

Ninguna de estas reemplaza una prueba real contra una instancia Odoo corriendo — son una red de seguridad rápida antes de desplegar, no una garantía de que el código funcione.

## 9. Disciplina de flujo de trabajo con el usuario

- Ante un requerimiento de diseño/ambiguo, **confirmar el entendimiento explícitamente antes de programar** — incluso si la respuesta esperada es un simple "adelante". Sirve para detectar alcance mal entendido (ej. "esto también aplica a los otros 3 formularios que no mencionaste") antes de escribir código.
- **No diagnosticar una causa raíz sin evidencia directa** (traceback real, log real) — una hipótesis razonada mostrada como tal, y retractada abiertamente cuando la evidencia real la contradice, genera más confianza que aferrarse a la primera teoría.
- Cuando el usuario reporta que algo "se omitió" o "no funciona", **verificar primero contra el código real** antes de asumir que hay que reconstruir algo — varias veces la funcionalidad ya existía pero estaba oculta detrás de una condición no evidente (ver el caso de la Sección 19 de Crop, `osp_management/CONTEXT.md` punto 20).

## 10. Traducción (i18n) de la interfaz propia del módulo

Esto es sobre la mecánica de Odoo para traducir los **elementos que el propio módulo define** (menús, acciones, columnas de tree/search, `string=` de campos, nombres de grupo/categoría de seguridad, opciones de `Selection`, etc.) — no sobre si el *contenido/documento* que un módulo gestiona debe traducirse o no, eso es una decisión de negocio propia de cada proyecto (en `osp_management`, por ejemplo, el cuerpo de cada formulario nunca se traduce — ver `osp_management/CONTEXT.md` y la memoria `osp-forms-never-translated.md` — pero esa regla es de ese proyecto, no una generalidad de Odoo).

- **Mecanismo estándar**: archivos `.po` en `i18n/<idioma>.po`, **auto-detectados por Odoo sin tocar `__manifest__.py`**, y recargados solos en cada `-u` del módulo, para cualquier idioma ya instalado en la base. El `.pot` (`i18n/<modulo>.pot`) es el molde/plantilla — se regenera, **nunca se edita a mano**.
- **Dos categorías de término traducible, con comportamiento distinto**:
  - **`model_terms:ir.ui.view`** — texto que vive dentro del `arch` de una vista (botones, títulos de grupo, columnas de tree/search, placeholders). Se recarga fresco en cada `-u` a partir del `.po` — es el caso "normal", sin sorpresas.
  - **`model:X,Y`** — términos que Odoo resuelve por su propio mecanismo de traducción de campos de modelo: nombre de menús (`ir.ui.menu`), de acciones (`ir.actions.act_window`), `field_description` de un campo, las opciones de un `Selection`, el nombre de un módulo/grupo/categoría de seguridad. Estos también se traducen vía `.po`, pero con una trampa real (ver siguiente punto).
- **Trampa real y ya vivida**: si en algún momento se **fuerza por ORM/migración** (`with_context(lang=...).write(...)` dentro de un script en `migrations/`) el valor de un término `model:X,Y` para todos los idiomas — por ejemplo, para que un menú muestre siempre el mismo texto sin importar el idioma del usuario — esa escritura **queda pegada** y tiene prioridad sobre cualquier `.po` posterior: un `.po` nuevo que traduzca ese mismo término **no lo va a sobreescribir**. Si más adelante se necesita revertir ese comportamiento, hace falta **otra migración** que vuelva a escribir el valor deseado — no alcanza con editar el `.po`. Antes de forzar una traducción por ORM, vale la pena preguntarse si de verdad hace falta (vs. dejar que el `.po` normal haga su trabajo), porque es una decisión que cuesta trabajo revertir después.
- **Cómo probar**: cambiar el idioma del usuario (Mi Perfil → Preferencias → Idioma) y recargar. Si algo no se tradujo, lo primero a revisar es un desajuste entre el `msgid` del `.po` y el texto real renderizado (típicamente espacios/comillas), y lo segundo es si ese término específico fue forzado por una migración anterior (punto arriba).
- **Cuidado al tocar la carpeta `i18n/`**: en este proyecto la carpeta desapareció una vez del disco por una causa ajena a la sesión que la tocaba. Ante un archivo/carpeta "desaparecido", `git status` / `git log -- <ruta>` es el primer paso para confirmar si es recuperable desde el historial (`git show <commit>:<ruta>`) antes de asumir que hay que rehacerlo desde cero.

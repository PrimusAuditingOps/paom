// Este mensaje saldrá en la consola en TODAS las páginas del portal
// y nos confirmará que Odoo ya enlazó el archivo.
console.log("🟢 [OSP] Archivo Javascript cargado exitosamente por Odoo 17.");

function initOspForm() {
    // Solo ejecutamos el código si estamos en la página del formulario
    const formContent = document.getElementById('form-content');
    if (!formContent) return;

    console.log("🟢 [OSP] Formulario detectado. Arrancando motor de formulario dinámico...");

    const READONLY = !!window.OSP_READONLY;
    const IS_ADMIN = !!window.OSP_IS_ADMIN;
    // Navegante sin login (no es cliente de portal): "Save progress" no
    // toca el servidor en absoluto — se guarda en localStorage del propio
    // navegador, y solo el Submit final crea el registro en Odoo (ver
    // CONTEXT.md, sección del formulario público, y OSPPublicController
    // en controllers/portal.py).
    const PUBLIC_MODE = !!window.OSP_PUBLIC_MODE;
    const TECHNICAL_CODE = window.OSP_TECHNICAL_CODE || 'form_crop';
    // Verificación anti-bot (Cloudflare Turnstile) — solo aplica al
    // navegante público (PUBLIC_MODE), nunca a un cliente de portal ya
    // logueado. Vacío si el administrador todavía no configuró la Site Key
    // en Ajustes > OSP Management: en ese caso simplemente no se inyecta
    // ningún widget, el formulario sigue funcionando igual que antes.
    const TURNSTILE_SITE_KEY = window.OSP_TURNSTILE_SITE_KEY || '';
    // Con el código técnico en la llave, cada tipo de formulario público
    // (Crop, y a futuro Handler, Cultivo, etc.) guarda su propio avance
    // en localStorage sin pisar el de otro si el navegante llena más de
    // uno en el mismo navegador.
    const PUBLIC_STORAGE_KEY = 'osp_public_draft_' + TECHNICAL_CODE;
    // Retro de usuario piloto: el navegante público quería poder elegir el
    // archivo de cada sección desde ya (para no olvidarlo), sin reabrir el
    // problema de registros basura en el servidor (nunca se crea nada hasta
    // el Submit final). Los File objects solo viven en memoria del
    // navegador — no son serializables a localStorage, así que "Save
    // progress" no los conserva; solo necesitan sobrevivir hasta el Submit
    // de esta misma carga de página (ver initPublicFileUploads() y el envío
    // automático dentro de savePublicForm() más abajo). Llave: el id del
    // checkbox "..._attachment_needed" -> el File elegido para esa pregunta.
    const pendingPublicFiles = {};

    // Widget de Cloudflare Turnstile: se inyecta ya, al cargar la página
    // (no hasta que el visitante haga clic en Submit), para que Turnstile
    // tenga tiempo de correr su verificación en segundo plano (modo
    // "Managed") ANTES de que el token se necesite. Ver savePublicForm()
    // más abajo, donde se lee el resultado con turnstile.getResponse().
    if (PUBLIC_MODE && TURNSTILE_SITE_KEY) {
        initTurnstileWidget(TURNSTILE_SITE_KEY);
    }

    const ospIdInput = document.querySelector('input[name="osp_id"]');
    if (!ospIdInput) return;
    // "let" (no "const"): cuando el formulario es nuevo, ospId arranca en 0
    // y se actualiza con el id real que devuelve el servidor en cuanto el
    // primer guardado crea el registro (ver saveForm()/isNewRecord más abajo).
    let ospId = parseInt(ospIdInput.value);

    // Solo tienen valor cuando ospId === 0 (formulario nuevo, sin registro
    // creado todavía) — ver /my/osp/form/new en portal.py.
    const newServiceIdInput = document.querySelector('input[name="new_service_id"]');
    const newTemplateIdInput = document.querySelector('input[name="new_template_id"]');
    const newServiceId = newServiceIdInput ? parseInt(newServiceIdInput.value) : 0;
    const newTemplateId = newTemplateIdInput ? parseInt(newTemplateIdInput.value) : 0;

    // ============================================================
    // HIDRATACIÓN DESDE localStorage (solo modo público)
    // El resto de la página (todas las secciones, incluidas las 12 tablas
    // dinámicas) se rellena normalmente vía "data.get(...)" server-side
    // en el HTML — pero el navegante público nunca tiene un "data" real
    // del servidor (no hay registro todavía), así que si ya había un
    // avance guardado en este mismo navegador, se restaura aquí ANTES de
    // que el motor de tablas dinámicas (más abajo) lea los inputs ocultos
    // *_json — por eso corre primero: si un input oculto de tabla se
    // hidrata con el JSON guardado, initDynTable() ya lo toma en cuenta
    // al inicializarse.
    // ============================================================
    function hydrateFormFromData(data) {
        if (!data) return;
        document.querySelectorAll('.osp-input').forEach(el => {
            if (el.type === 'checkbox' && el.dataset.group) {
                const groupValues = data[el.dataset.group] || [];
                el.checked = groupValues.indexOf(el.value) !== -1;
            } else if (el.type === 'radio') {
                el.checked = (data[el.name] === el.value);
            } else if (el.type === 'checkbox') {
                el.checked = !!data[el.name];
            } else if (data[el.name] !== undefined) {
                el.value = data[el.name];
            }
        });
    }

    if (PUBLIC_MODE && ospId === 0) {
        try {
            const saved = localStorage.getItem(PUBLIC_STORAGE_KEY);
            if (saved) hydrateFormFromData(JSON.parse(saved));
        } catch (e) {
            console.error('🔴 [OSP] No se pudo leer el avance guardado localmente:', e);
        }
    }

    // ============================================================
    // MOTOR GENÉRICO DE TABLAS DINÁMICAS
    // Una sola definición de columnas por tabla; el header del HTML
    // y cada fila se generan siempre desde la misma fuente, para que
    // nunca puedan desalinearse (lección aprendida con la tabla Sites).
    // ============================================================
    const TABLE_CONFIGS = {
        contacts: { // 1j
            jsonInputId: '1j_contacts_json', tbodyId: 'contacts_tbody', addBtnId: 'btn_add_contact',
            columns: [
                { key: 'name', type: 'text', placeholder: 'Name...' },
                { key: 'email', type: 'text', placeholder: 'Email...' },
                { key: 'phone', type: 'text', placeholder: 'Phone...' },
            ],
        },
        sites: { // 4g
            jsonInputId: '4g_sites_json', tbodyId: 'sites_tbody', addBtnId: 'btn_add_site',
            columns: [
                { key: 'site_id', type: 'text', placeholder: 'Site ID / Name...' },
                { key: 'site_address', type: 'text', placeholder: 'Site Address...' },
                { key: 'city_state', type: 'text', placeholder: 'City, State...' },
                { key: 'zip', type: 'text', placeholder: 'Zip...' },
                { key: 'contact', type: 'text', placeholder: 'Contact Name and Phone Number...' },
                { key: 'description', type: 'text', placeholder: 'Description of Site activities and responsibilities...' },
            ],
        },
        fields: { // 4h (Crop)
            // El Word original trae, en una sola celda "units:", tanto el
            // valor numérico (ej. "8" en su propio ejemplo) como la unidad
            // (Acre/Hectare) — al construir la tabla web solo se tradujo el
            // selector de unidad y se perdió la columna numérica (retro de
            // usuario piloto, ver CONTEXT.md). Se agrega "total_land"
            // siguiendo el mismo patrón número+unidad ya usado en 4j.
            jsonInputId: '4h_fields_json', tbodyId: 'fields_tbody', addBtnId: 'btn_add_field',
            columns: [
                { key: 'field_id', type: 'text', placeholder: 'Field ID (Name/Code)...' },
                { key: 'parcel_address', type: 'text', placeholder: 'Parcel Address / Legal Description...' },
                { key: 'area_type', type: 'select', options: ['Organic', 'Transitional', 'Non-Organic'] },
                { key: 'total_land', type: 'text', placeholder: 'Total land...' },
                { key: 'units', type: 'select', options: ['Acre', 'Hectare'] },
                { key: 'rented_or_owned', type: 'select', options: ['Rented', 'Owned'] },
            ],
        },
        cultivo_fields: { // 4h (Cultivo) — config propia, ya no comparte la de Crop
            jsonInputId: '4h_fields_json', tbodyId: 'cultivo_fields_tbody', addBtnId: 'btn_add_cultivo_field',
            columns: [
                { key: 'field_id', type: 'text', placeholder: 'ID del sitio (Nombre/Código)...' },
                { key: 'parcel_address', type: 'text', placeholder: 'Dirección de la finca/Descripción legal...' },
                { key: 'area_type', type: 'select', options: ['Orgánico', 'En transición', 'No orgánico'] },
                { key: 'total_land', type: 'text', placeholder: 'Total de terreno...' },
                { key: 'units', type: 'select', options: ['Acres', 'Hectáreas'] },
                { key: 'rented_or_owned', type: 'select', options: ['Alquilado', 'Propio'] },
            ],
        },
        crops: { // 4j (Crop)
            jsonInputId: '4j_crops_json', tbodyId: 'crops_tbody', addBtnId: 'btn_add_crop',
            columns: [
                { key: 'crop_requested', type: 'text', placeholder: 'Crop requested for certification...' },
                { key: 'field_id', type: 'text', placeholder: 'Field ID where planted this year...' },
                { key: 'total_planted_area', type: 'text', placeholder: 'Total planted area...' },
                { key: 'area_units', type: 'select', options: ['Acre', 'Hectare'] },
                { key: 'projected_yield', type: 'text', placeholder: 'Projected yield...' },
                // Retro de usuario piloto: esta columna es la UNIDAD DEL
                // RENDIMIENTO (peso de cosecha, no área) — venía mal desde
                // su construcción original, reutilizando por error las
                // mismas opciones de área (Acre/Hectare) que "area_units".
                { key: 'yield_units', type: 'select', options: ['Kilogram', 'Ton'] },
            ],
        },
        cultivo_crops: { // 4j (Cultivo) — config propia, ya no comparte la de Crop
            jsonInputId: '4j_crops_json', tbodyId: 'cultivo_crops_tbody', addBtnId: 'btn_add_cultivo_crop',
            columns: [
                { key: 'crop_requested', type: 'text', placeholder: 'Cultivo solicitado para certificación...' },
                { key: 'field_id', type: 'text', placeholder: 'ID de terreno(s) donde fue sembrado este año...' },
                { key: 'total_planted_area', type: 'text', placeholder: 'Área total sembrada...' },
                { key: 'area_units', type: 'select', options: ['Acres', 'Hectáreas'] },
                { key: 'projected_yield', type: 'text', placeholder: 'Rendimiento proyectado...' },
                { key: 'yield_units', type: 'select', options: ['Kilogramos', 'Toneladas'] },
            ],
        },
        products: { // 5d (Crop)
            jsonInputId: '5d_products_json', tbodyId: 'products_tbody', addBtnId: 'btn_add_product',
            columns: [
                { key: 'product', type: 'text', placeholder: 'Product requested for certification...' },
                { key: 'id_mark', type: 'text', placeholder: 'ID Mark (Labels)...' },
                { key: 'label_type', type: 'multicheckbox', options: ['Retail', 'Non-Retail', 'Private Label'] },
                { key: 'packing_with_id', type: 'select', options: ['Y', 'N'] },
                { key: 'organic_or_100', type: 'select', options: ['Organic', '100% Organic'] },
                { key: 'international_market', type: 'text', placeholder: 'International market / equivalency request...' },
            ],
        },
        cultivo_products: { // 5d (Cultivo) — config propia, ya no comparte la de Crop
            jsonInputId: '5d_products_json', tbodyId: 'cultivo_products_tbody', addBtnId: 'btn_add_cultivo_product',
            columns: [
                { key: 'product', type: 'text', placeholder: 'Producto solicitado para certificación...' },
                { key: 'id_mark', type: 'text', placeholder: 'Marca de Identificación...' },
                { key: 'label_type', type: 'multicheckbox', options: ['Minorista', 'Mayoreo', 'Etiqueta Privada'] },
                { key: 'packing_with_id', type: 'select', options: ['Y', 'N'] },
                { key: 'organic_or_100', type: 'select', options: ['Orgánico', '100% Orgánico'] },
                { key: 'international_market', type: 'text', placeholder: 'Mercados internacionales / solicitud de equivalencia...' },
            ],
        },
        seeds: { // 8a (Crop)
            jsonInputId: '8a_seeds_json', tbodyId: 'seeds_tbody', addBtnId: 'btn_add_seed',
            columns: [
                { key: 'crop_variety', type: 'text', placeholder: 'Crop / Variety...' },
                { key: 'brand_supplier', type: 'text', placeholder: 'Brand / Supplier...' },
                { key: 'seed_type', type: 'select', options: ['Certified Organic', 'Non-Organic: Untreated', 'Non-Organic: Treated', 'Certified Organic Planting Stock', 'Non-Organic: Untreated Planting Stock', 'Non-Organic: Treated Planting Stock'] },
                { key: 'non_organic_treatment', type: 'text', placeholder: 'If treated: type/brand of treatment...' },
                { key: 'non_gmo_documented', type: 'select', options: ['Y', 'N'] },
                { key: 'seed_search_form_completed', type: 'select', options: ['Y', 'N'] },
            ],
        },
        cultivo_seeds: { // 8a (Cultivo) — config propia, ya no comparte la de Crop
            jsonInputId: '8a_seeds_json', tbodyId: 'cultivo_seeds_tbody', addBtnId: 'btn_add_cultivo_seed',
            columns: [
                { key: 'crop_variety', type: 'text', placeholder: 'Cultivo/Variedad...' },
                { key: 'brand_supplier', type: 'text', placeholder: 'Marca/Proveedor...' },
                { key: 'seed_type', type: 'select', options: ['Orgánico Certificado', 'No-Orgánico: Sin Tratar', 'No-Orgánico: Tratado', 'Material de Siembra Orgánico Certificado', 'Material de Siembra No-Orgánico: Sin Tratar', 'Material de Siembra No-Orgánico: Tratado'] },
                { key: 'non_organic_treatment', type: 'text', placeholder: 'Si es tratada: tipo/marca del tratamiento...' },
                { key: 'non_gmo_documented', type: 'select', options: ['Y', 'N'] },
                { key: 'seed_search_form_completed', type: 'select', options: ['Y', 'N'] },
            ],
        },
        planting_stock: { // 8g (Crop)
            jsonInputId: '8g_planting_stock_json', tbodyId: 'planting_stock_tbody', addBtnId: 'btn_add_planting_stock',
            columns: [
                { key: 'type_crop_variety', type: 'text', placeholder: 'Type (Crop - Variety)...' },
                { key: 'source_supplier', type: 'text', placeholder: 'Planting stock source / supplier...' },
                { key: 'seedling_type', type: 'select', options: ['Certified Organic', 'Non-Organic'] },
                { key: 'date_planted', type: 'date', placeholder: '' },
                { key: 'expected_harvest_date', type: 'date', placeholder: '' },
                { key: 'search_form_attached', type: 'select', options: ['Y', 'N'] },
            ],
        },
        cultivo_planting_stock: { // 8g (Cultivo) — config propia, ya no comparte la de Crop
            jsonInputId: '8g_planting_stock_json', tbodyId: 'cultivo_planting_stock_tbody', addBtnId: 'btn_add_cultivo_planting_stock',
            columns: [
                { key: 'type_crop_variety', type: 'text', placeholder: 'Tipo (Cultivo - Variedad)...' },
                { key: 'source_supplier', type: 'text', placeholder: 'Fuente/Proveedor del material...' },
                { key: 'seedling_type', type: 'select', options: ['Orgánico Certificado', 'No-Orgánico'] },
                { key: 'date_planted', type: 'date', placeholder: '' },
                { key: 'expected_harvest_date', type: 'date', placeholder: '' },
                { key: 'search_form_attached', type: 'select', options: ['Y', 'N'] },
            ],
        },
        rotation: { // 10 — reutilizada tal cual por Cultivo (mismo
            // tbodyId "rotation_tbody"). El Word original trae, por cada
            // plan de rotación, 5 checkboxes independientes (una casilla
            // por objetivo) en vez de un solo texto libre — se había
            // colapsado todo en un campo de texto genérico (retro de
            // usuario piloto, ver CONTEXT.md). Los 5 usan el nuevo tipo de
            // columna "checkbox" del motor (ver cellHtml()/bindDynTable()
            // más abajo), guardando "X"/"" igual que la convención
            // "check (x)" del propio Word — así el motor de reporte PDF no
            // necesita saber que son checkboxes, los trata como texto normal.
            jsonInputId: '10_rotation_json', tbodyId: 'rotation_tbody', addBtnId: 'btn_add_rotation',
            columns: [
                { key: 'rotation_plan', type: 'text', placeholder: 'Crop rotation plan (sequence of crops)...' },
                { key: 'increase_organic_matter', type: 'checkbox' },
                { key: 'nutrient_management', type: 'checkbox' },
                { key: 'pest_disease_management', type: 'checkbox' },
                { key: 'erosion_control', type: 'checkbox' },
                { key: 'other', type: 'checkbox' },
            ],
        },
        inputs: { // 12a (Crop)
            jsonInputId: '12a_inputs_json', tbodyId: 'inputs_tbody', addBtnId: 'btn_add_input',
            columns: [
                { key: 'input_used_for', type: 'select', options: ['Fertilization', 'Pest Control', 'Disease Control', 'Cleaning', 'Disinfection', 'Seed Treatment', 'Other'] },
                { key: 'brand_name', type: 'text', placeholder: 'Brand Name...' },
                { key: 'ingredients', type: 'text', placeholder: 'Ingredients...' },
                { key: 'compliance_approval_by', type: 'text', placeholder: 'Compliance approval by...' },
                { key: 'label_compliance_docs_attached', type: 'select', options: ['Y', 'N'] },
                { key: 'restrictions_compliance_description', type: 'text', placeholder: 'How you comply with NOP annotation...' },
            ],
        },
        cultivo_inputs: { // 12a (Cultivo) — config propia, ya no comparte la de Crop
            jsonInputId: '12a_inputs_json', tbodyId: 'cultivo_inputs_tbody', addBtnId: 'btn_add_cultivo_input',
            columns: [
                { key: 'input_used_for', type: 'select', options: ['Fertilización', 'Control de Plagas', 'Control de Enfermedades', 'Limpieza', 'Desinfección', 'Tratamiento de Semillas', 'Otro'] },
                { key: 'brand_name', type: 'text', placeholder: 'Nombre del Producto...' },
                { key: 'ingredients', type: 'text', placeholder: 'Ingredientes...' },
                { key: 'compliance_approval_by', type: 'text', placeholder: 'Aprobación de Conformidad Por...' },
                { key: 'label_compliance_docs_attached', type: 'select', options: ['Y', 'N'] },
                { key: 'restrictions_compliance_description', type: 'text', placeholder: 'Cumplimiento Anotación NOP...' },
            ],
        },
        equipment: { // 14a (Crop)
            jsonInputId: '14a_equipment_json', tbodyId: 'equipment_tbody', addBtnId: 'btn_add_equipment',
            columns: [
                { key: 'equipment_name_model_code', type: 'text', placeholder: 'Equipment Name / Model / Code...' },
                { key: 'owned_rented_custom', type: 'select', options: ['Owned', 'Rented', 'Custom'] },
                { key: 'used_for', type: 'select', options: ['Organic', 'Non-Organic', 'Both Organic and Non-Organic'] },
                { key: 'cleaning_method', type: 'text', placeholder: 'How is equipment cleaned before use...' },
            ],
        },
        cultivo_equipment: { // 14a (Cultivo) — config propia, ya no comparte la de Crop
            jsonInputId: '14a_equipment_json', tbodyId: 'cultivo_equipment_tbody', addBtnId: 'btn_add_cultivo_equipment',
            columns: [
                { key: 'equipment_name_model_code', type: 'text', placeholder: 'Nombre del Equipo/Modelo/Código...' },
                { key: 'owned_rented_custom', type: 'select', options: ['Propio', 'Alquilado', 'Compartido'] },
                { key: 'used_for', type: 'select', options: ['Orgánico', 'No-Orgánico', 'Ambos (Orgánico y No-Orgánico)'] },
                { key: 'cleaning_method', type: 'text', placeholder: '¿Cómo se limpia antes de su uso en campos orgánicos?...' },
            ],
        },
        // "history" (19) se retiró de aquí — la Sección 19 dejó de ser una
        // tabla plana y ahora es un bloque repetible por campo, con su
        // propio renderer dedicado (ver initFieldHistoryBlock() más abajo).
        search_record: { // 20
            jsonInputId: '20_search_record_json', tbodyId: 'search_record_tbody', addBtnId: 'btn_add_search_record',
            columns: [
                { key: 'crop', type: 'text', placeholder: 'Crop...' },
                { key: 'traits', type: 'text', placeholder: 'Traits...' },
                { key: 'why_not_met', type: 'text', placeholder: 'Why not met by equivalent variety...' },
                { key: 'suppliers_contacted', type: 'text', placeholder: 'Suppliers contacted...' },
                { key: 'date_contacted', type: 'date', placeholder: '' },
                { key: 'method_of_contact', type: 'text', placeholder: 'Method of contact...' },
            ],
        },
        // ---- Formulario Handler (ver views/osp_form_handler.xml) ----
        // Claves distintas a las de Crop aunque el concepto se parezca
        // (ej. "sites"), porque las columnas/JSON keys no son idénticas —
        // ambos configs conviven en el mismo objeto sin pisarse: initDynTable
        // hace no-op en la página que no tenga su jsonInput en el DOM.
        handler_sites: { // 4b
            jsonInputId: '4b_sites_json', tbodyId: 'handler_sites_tbody', addBtnId: 'btn_add_handler_site',
            columns: [
                { key: 'site_id', type: 'text', placeholder: 'Site ID / Name...' },
                { key: 'site_address', type: 'text', placeholder: 'Site Address...' },
                { key: 'city_state', type: 'text', placeholder: 'City, State...' },
                { key: 'zip_code', type: 'text', placeholder: 'Zip...' },
                { key: 'contact', type: 'text', placeholder: 'Contact Name and Phone Number...' },
                { key: 'description', type: 'text', placeholder: 'Description of Site activities...' },
            ],
        },
        handler_products: { // 5d
            jsonInputId: '5d_products_json', tbodyId: 'handler_products_tbody', addBtnId: 'btn_add_handler_product',
            columns: [
                { key: 'product', type: 'text', placeholder: 'Product requested for certification...' },
                { key: 'id_mark', type: 'text', placeholder: 'ID Mark (Labels)...' },
                { key: 'label_type', type: 'multicheckbox', options: ['Retail', 'Non-Retail', 'Private Label'] },
                { key: 'packing_with_id', type: 'select', options: ['Y', 'N'] },
                { key: 'organic_or_100', type: 'text', placeholder: 'Organic or 100% Organic?...' },
                { key: 'international_market', type: 'text', placeholder: 'International market...' },
            ],
        },
        handler_inputs: { // 9a
            jsonInputId: '9a_inputs_json', tbodyId: 'handler_inputs_tbody', addBtnId: 'btn_add_handler_input',
            columns: [
                { key: 'input_used_for', type: 'select', options: ['Pest Control (Facility)', 'Cleaning', 'Disinfection', 'Post-Harvest Treatment', 'Other'] },
                { key: 'brand_name', type: 'text', placeholder: 'Brand Name...' },
                { key: 'ingredients', type: 'text', placeholder: 'Ingredients...' },
                { key: 'food_contact', type: 'select', options: ['Y', 'N'] },
                { key: 'compliance_approval_by', type: 'text', placeholder: 'Compliance approval by...' },
                { key: 'label_docs_attached', type: 'select', options: ['Y', 'N'] },
                { key: 'restrictions_description', type: 'text', placeholder: 'If product has restrictions...' },
            ],
        },
        // ---- Formulario Handler (Trader) (ver views/osp_form_handler_trader.xml) ----
        trader_sites: { // 4a
            jsonInputId: '4a_sites_json', tbodyId: 'trader_sites_tbody', addBtnId: 'btn_add_trader_site',
            columns: [
                { key: 'site_id', type: 'text', placeholder: 'Site/ID Name...' },
                { key: 'site_address', type: 'text', placeholder: 'Site Address: City, State, Zip...' },
                { key: 'contact', type: 'text', placeholder: 'Contact Name and Phone Number...' },
                { key: 'description', type: 'text', placeholder: 'Description of Site activities...' },
            ],
        },
        trader_products: { // 5d
            jsonInputId: '5d_products_json', tbodyId: 'trader_products_tbody', addBtnId: 'btn_add_trader_product',
            columns: [
                { key: 'product', type: 'text', placeholder: 'Product requested for certification...' },
                { key: 'id_mark', type: 'text', placeholder: 'ID Mark (Labels)...' },
                { key: 'label_type', type: 'multicheckbox', options: ['Retail', 'Non-Retail', 'Private Label'] },
                { key: 'organic_or_100', type: 'text', placeholder: 'Organic or 100% Organic?...' },
                { key: 'international_market', type: 'text', placeholder: 'International market...' },
            ],
        },
        // ---- Formulario Manejo o Proceso (ver views/osp_form_manejo_proceso.xml) ----
        // Formulario nativo en español — los placeholders quedan en
        // español, pero eso no afecta nada (solo texto de ayuda visual).
        manejo_sites: { // 4b
            jsonInputId: '4b_sites_json', tbodyId: 'manejo_sites_tbody', addBtnId: 'btn_add_manejo_site',
            columns: [
                { key: 'site_id', type: 'text', placeholder: 'ID/Nombre del sitio...' },
                { key: 'site_address', type: 'text', placeholder: 'Dirección del sitio...' },
                { key: 'city_state', type: 'text', placeholder: 'Ciudad, Estado...' },
                { key: 'zip_code', type: 'text', placeholder: 'Código Postal...' },
                { key: 'contact', type: 'text', placeholder: 'Nombre y teléfono de contacto...' },
                { key: 'description', type: 'text', placeholder: 'Descripción de actividades...' },
            ],
        },
        manejo_products: { // 5d
            jsonInputId: '5d_products_json', tbodyId: 'manejo_products_tbody', addBtnId: 'btn_add_manejo_product',
            columns: [
                { key: 'product', type: 'text', placeholder: 'Producto solicitado para certificación...' },
                { key: 'id_mark', type: 'text', placeholder: 'Marca de Identificación...' },
                { key: 'label_type', type: 'multicheckbox', options: ['Minorista', 'Mayoreo', 'Etiqueta Privada'] },
                { key: 'packing_with_id', type: 'select', options: ['Y', 'N'] },
                { key: 'organic_or_100', type: 'text', placeholder: 'Orgánico o 100% Orgánico?...' },
                { key: 'international_market', type: 'text', placeholder: 'Mercados internacionales...' },
            ],
        },
        manejo_inputs: { // 9a
            jsonInputId: '9a_inputs_json', tbodyId: 'manejo_inputs_tbody', addBtnId: 'btn_add_manejo_input',
            columns: [
                { key: 'input_used_for', type: 'select', options: ['Control de Plagas (Instalaciones)', 'Limpieza', 'Desinfección', 'Tratamiento Postcosecha', 'Otro'] },
                { key: 'brand_name', type: 'text', placeholder: 'Marca comercial...' },
                { key: 'ingredients', type: 'text', placeholder: 'Ingredientes...' },
                { key: 'food_contact', type: 'select', options: ['Y', 'N'] },
                { key: 'compliance_approval_by', type: 'text', placeholder: 'Aprobación de conformidad por...' },
                { key: 'label_docs_attached', type: 'select', options: ['Y', 'N'] },
                { key: 'restrictions_description', type: 'text', placeholder: 'Si tiene restricciones...' },
            ],
        },
        // ---- Formulario Comercializador (ver views/osp_form_comercializador.xml) ----
        comercializador_sites: { // 4a
            jsonInputId: '4a_sites_json', tbodyId: 'comercializador_sites_tbody', addBtnId: 'btn_add_comercializador_site',
            columns: [
                { key: 'site_id', type: 'text', placeholder: 'ID/Nombre del sitio...' },
                { key: 'site_address', type: 'text', placeholder: 'Dirección (ciudad, estado, CP)...' },
                { key: 'contact', type: 'text', placeholder: 'Nombre y teléfono de contacto...' },
                { key: 'description', type: 'text', placeholder: 'Descripción de actividades...' },
            ],
        },
        comercializador_products: { // 5d
            jsonInputId: '5d_products_json', tbodyId: 'comercializador_products_tbody', addBtnId: 'btn_add_comercializador_product',
            columns: [
                { key: 'product', type: 'text', placeholder: 'Producto solicitado para certificación...' },
                { key: 'id_mark', type: 'text', placeholder: 'Marca de Identificación...' },
                { key: 'label_type', type: 'multicheckbox', options: ['Minorista', 'Mayoreo', 'Etiqueta Privada'] },
                { key: 'organic_or_100', type: 'text', placeholder: 'Orgánico o 100% Orgánico?...' },
                { key: 'international_market', type: 'text', placeholder: 'Mercados internacionales...' },
            ],
        },
    };

    function emptyRowFor(config) {
        const row = {};
        config.columns.forEach(c => { row[c.key] = ''; });
        return row;
    }

    function cellHtml(col, rowIndex, value) {
        const safeVal = (value === undefined || value === null) ? '' : String(value);
        if (col.type === 'select') {
            const opts = col.options.map(o =>
                `<option value="${o}" ${safeVal === o ? 'selected' : ''}>${o}</option>`
            ).join('');
            return `<td><select class="form-select form-select-sm border-0 bg-transparent dyn-input" data-index="${rowIndex}" data-field="${col.key}">
                <option value="">--</option>${opts}
            </select></td>`;
        }
        if (col.type === 'date') {
            return `<td><input type="date" class="form-control form-control-sm border-0 bg-transparent dyn-input" data-index="${rowIndex}" data-field="${col.key}" value="${safeVal}"/></td>`;
        }
        if (col.type === 'checkbox') {
            // Se guarda "X"/"" (no true/false) para imitar la convención
            // "check (x)" del Word y que el motor de reporte PDF (que solo
            // sabe imprimir texto de celda) no necesite tratarlo distinto.
            return `<td class="text-center"><input type="checkbox" class="form-check-input dyn-input" data-index="${rowIndex}" data-field="${col.key}" ${safeVal === 'X' ? 'checked' : ''}/></td>`;
        }
        if (col.type === 'multicheckbox') {
            // Varias casillas independientes dentro de una sola celda (ej.
            // "Label Type": Retail/Non-Retail/Private Label — el operador
            // puede marcar más de una). Se guarda como texto separado por
            // comas (ej. "Retail, Private Label") en vez de un array, para
            // que el motor de reporte PDF (que solo sabe imprimir texto de
            // celda) siga sin necesitar ningún cambio.
            const selected = safeVal ? safeVal.split(',').map(s => s.trim()).filter(Boolean) : [];
            const opts = col.options.map(o =>
                `<div class="form-check"><input type="checkbox" class="form-check-input dyn-multicheck" data-index="${rowIndex}" data-field="${col.key}" data-option="${o}" ${selected.includes(o) ? 'checked' : ''}/><label class="form-check-label small">${o}</label></div>`
            ).join('');
            return `<td>${opts}</td>`;
        }
        return `<td><input type="text" class="form-control border-0 bg-transparent dyn-input" data-index="${rowIndex}" data-field="${col.key}" value="${safeVal.replace(/"/g, '&quot;')}" placeholder="${col.placeholder || ''}"/></td>`;
    }

    function renderDynTable(key) {
        const config = TABLE_CONFIGS[key];
        const tbody = document.getElementById(config.tbodyId);
        if (!tbody) return; // esta tabla no está en el template actual (ej. placeholder)

        if (!config._data || config._data.length === 0) {
            config._data = config._data || [];
            config._data.push(emptyRowFor(config));
        }

        tbody.innerHTML = '';
        config._data.forEach((rowData, index) => {
            const tr = document.createElement('tr');
            const cells = config.columns.map(c => cellHtml(c, index, rowData[c.key])).join('');
            tr.innerHTML = `${cells}<td class="text-center"><button type="button" class="btn btn-sm text-danger dyn-delete" data-table="${key}" data-index="${index}"><i class="fa fa-trash"></i></button></td>`;
            if (READONLY) {
                tr.querySelectorAll('input, select, button').forEach(el => { el.disabled = true; });
            }
            tbody.appendChild(tr);
        });

        const jsonInput = document.getElementById(config.jsonInputId);
        if (jsonInput) jsonInput.value = JSON.stringify(config._data);
        bindDynTableEvents(key);
    }

    function bindDynTableEvents(key) {
        const config = TABLE_CONFIGS[key];
        const tbody = document.getElementById(config.tbodyId);
        if (!tbody) return;

        tbody.querySelectorAll('.dyn-input').forEach(el => {
            el.addEventListener('change', function () {
                const idx = this.getAttribute('data-index');
                const fld = this.getAttribute('data-field');
                // Checkbox: this.value siempre es "on" sin importar si está
                // marcado o no — hay que leer this.checked, y guardar
                // "X"/"" (ver cellHtml()) en vez de true/false.
                config._data[idx][fld] = (this.type === 'checkbox') ? (this.checked ? 'X' : '') : this.value;
                const jsonInput = document.getElementById(config.jsonInputId);
                if (jsonInput) jsonInput.value = JSON.stringify(config._data);
            });
        });
        tbody.querySelectorAll('.dyn-multicheck').forEach(el => {
            el.addEventListener('change', function () {
                const idx = this.getAttribute('data-index');
                const fld = this.getAttribute('data-field');
                const opt = this.getAttribute('data-option');
                let selected = config._data[idx][fld] ? config._data[idx][fld].split(',').map(s => s.trim()).filter(Boolean) : [];
                if (this.checked) {
                    if (!selected.includes(opt)) selected.push(opt);
                } else {
                    selected = selected.filter(v => v !== opt);
                }
                config._data[idx][fld] = selected.join(', ');
                const jsonInput = document.getElementById(config.jsonInputId);
                if (jsonInput) jsonInput.value = JSON.stringify(config._data);
            });
        });
        tbody.querySelectorAll('.dyn-delete').forEach(btn => {
            btn.addEventListener('click', function () {
                const idx = this.getAttribute('data-index');
                config._data.splice(idx, 1);
                renderDynTable(key);
            });
        });
    }

    function initDynTable(key) {
        const config = TABLE_CONFIGS[key];
        const jsonInput = document.getElementById(config.jsonInputId);
        if (!jsonInput) return; // sección/tabla no presente en este template
        try {
            config._data = JSON.parse(jsonInput.value || '[]');
        } catch (e) {
            config._data = [];
        }
        renderDynTable(key);

        const addBtn = document.getElementById(config.addBtnId);
        if (addBtn) {
            if (READONLY) {
                addBtn.disabled = true;
            } else {
                addBtn.addEventListener('click', function () {
                    config._data.push(emptyRowFor(config));
                    renderDynTable(key);
                });
            }
        }
    }

    Object.keys(TABLE_CONFIGS).forEach(initDynTable);

    // ============================================================
    // MOTOR DE CAMPOS CONDICIONALES
    // Un div con data-conditional-field="X" data-conditional-value="Yes"
    // solo se muestra si el campo X (radio, select, o grupo de checkbox)
    // tiene ese valor seleccionado/marcado.
    // ============================================================
    function isConditionMet(fieldName, expectedValue) {
        const single = document.querySelector(`[name="${fieldName}"]:checked, select[name="${fieldName}"]`);
        if (single) return single.value === expectedValue;

        const groupBoxes = document.querySelectorAll(`[data-group="${fieldName}"]`);
        if (groupBoxes.length > 0) {
            return Array.from(groupBoxes).some(cb => cb.checked && cb.value === expectedValue);
        }
        return false;
    }

    function applyConditionals() {
        document.querySelectorAll('.osp-conditional').forEach(div => {
            const fieldName = div.getAttribute('data-conditional-field');
            const expectedValue = div.getAttribute('data-conditional-value');
            div.style.display = isConditionMet(fieldName, expectedValue) ? '' : 'none';
        });
    }

    document.querySelectorAll('input[type=radio].osp-input, select.osp-input, input[type=checkbox].osp-input').forEach(el => {
        el.addEventListener('change', applyConditionals);
    });
    applyConditionals();

    // ============================================================
    // SECCIÓN 19 (Crop/Cultivo) — "Field History Affidavit" repetible.
    // Retro de usuario piloto: el formato original permite declarar el
    // historial de VARIOS campos nuevos, no solo uno — se había colapsado
    // toda la sección en un único set de preguntas. A diferencia del resto
    // de tablas dinámicas (TABLE_CONFIGS, filas planas de un solo tipo de
    // celda), aquí cada "entrada" es un bloque completo con preguntas
    // condicionales (radios Sí/No que revelan más campos) + su propia
    // tabla año-por-año anidada — no cabe en el motor genérico de tablas,
    // así que tiene su propio renderer dedicado. Reutiliza el motor
    // genérico de condicionales (osp-conditional/applyConditionals() de
    // arriba) dándole a cada radio un "name" único por entrada
    // (ej. "f19_managed3_0", "f19_managed3_1"...), en vez de reinventar
    // el show/hide.
    // ============================================================
    function initFieldHistoryBlock() {
        const jsonInput = document.getElementById('19_fields_json');
        const container = document.getElementById('fields19_container');
        const addBtn = document.getElementById('btn_add_field19');
        if (!jsonInput || !container) return; // sección no presente en este formulario (solo Crop/Cultivo)

        const isSpanish = TECHNICAL_CODE === 'form_cultivo';
        const L = isSpanish ? {
            field: 'Campo', fieldId: 'Nombre del campo/ID número:', farmName: 'Nombre de la Finca/Productor:',
            transitionDate: 'Fecha de inicio de transición:', managed3: '¿Ha administrado el campo por más de 3 años?',
            yes: 'Sí', no: 'No',
            statements: 'Si la respuesta es no, debe presentar las declaraciones firmadas del administrador anterior indicando el uso y aplicación de todos los insumos durante los 3 años anteriores. ¿Adjunto?',
            certified: '¿Está el área certificada actualmente?',
            attachCert: 'Adjunte una copia del certificado actual (no es necesario completar la tabla siguiente).',
            lastSubstance: 'Última sustancia prohibida aplicada — Sustancia (marca e ingrediente activo):',
            lastDate: 'Fecha de la última aplicación:',
            rowInstruction: 'Complete una fila por año durante todo el proceso de transición.',
            year: 'AÑO', crops: 'CULTIVO(S) PREVIOS', inputsUsed: 'INSUMOS APLICADOS',
            addYear: 'Agregar Año', action: 'ACCIÓN', addField: 'Agregar Campo Nuevo', deleteField: 'Eliminar este campo',
        } : {
            field: 'Field', fieldId: 'Field name / ID number:', farmName: 'Farm / Producer Name:',
            transitionDate: 'Transition Start Date:', managed3: 'Have you managed this field for 3 or more years?',
            yes: 'Yes', no: 'No',
            statements: 'If no, have you attached signed statements from the previous land manager stating use and all inputs applied during the previous 3 years?',
            certified: 'Is this field currently certified?',
            attachCert: 'Submit a copy of your certification (table below not required).',
            lastSubstance: 'Last prohibited substance applied — Substance (Brand name and active ingredient):',
            lastDate: 'Date of last application:',
            rowInstruction: 'Complete one row per year throughout the transition process.',
            year: 'YEAR', crops: 'CROP(S) (product planted)',
            inputsUsed: 'INPUTS USED (brand name, formulation, compost, manure, fertilizers, crop production aids, pest control, additives, etc.)',
            addYear: 'Add Year', action: 'ACTION', addField: 'Add New Field', deleteField: 'Remove this field',
        };

        function esc(v) {
            return (v === undefined || v === null ? '' : String(v)).replace(/"/g, '&quot;');
        }

        function emptyEntry() {
            return {
                field_id: '', farm_producer_name: '', transition_start_date: '',
                managed_3years: '', statements_attached: '', field_certified: '',
                certification_attachment_needed: '', last_substance_brand: '', last_substance_date: '',
                history: [{ year: '', crops: '', inputs_used: '' }],
            };
        }

        let data;
        try {
            data = JSON.parse(jsonInput.value || '[]');
        } catch (e) {
            data = [];
        }
        if (!data.length) data.push(emptyEntry());

        function sync() {
            jsonInput.value = JSON.stringify(data);
        }

        function radioHtml(idx, field, value, optValue, optLabel) {
            const id = 'f19_' + field + '_' + idx + '_' + optValue;
            return '<div class="form-check form-check-inline">' +
                '<input class="form-check-input" type="radio" name="f19_' + field + '_' + idx + '" id="' + id + '" value="' + optValue + '" ' + (value === optValue ? 'checked' : '') + (READONLY ? ' disabled' : '') + '/>' +
                '<label class="form-check-label" for="' + id + '">' + optLabel + '</label></div>';
        }

        function historyRowsHtml(idx, history) {
            return history.map(function (r, hIdx) {
                return '<tr>' +
                    '<td><input type="text" class="form-control form-control-sm border-0 bg-transparent f19-hist-input" data-idx="' + idx + '" data-hidx="' + hIdx + '" data-field="year" value="' + esc(r.year) + '" placeholder="' + (isSpanish ? 'Año...' : 'Year...') + '" ' + (READONLY ? 'disabled' : '') + '/></td>' +
                    '<td><input type="text" class="form-control form-control-sm border-0 bg-transparent f19-hist-input" data-idx="' + idx + '" data-hidx="' + hIdx + '" data-field="crops" value="' + esc(r.crops) + '" ' + (READONLY ? 'disabled' : '') + '/></td>' +
                    '<td><input type="text" class="form-control form-control-sm border-0 bg-transparent f19-hist-input" data-idx="' + idx + '" data-hidx="' + hIdx + '" data-field="inputs_used" value="' + esc(r.inputs_used) + '" ' + (READONLY ? 'disabled' : '') + '/></td>' +
                    '<td class="text-center"><button type="button" class="btn btn-sm text-danger f19-hist-del" data-idx="' + idx + '" data-hidx="' + hIdx + '" ' + (READONLY ? 'disabled' : '') + '><i class="fa fa-trash"></i></button></td>' +
                    '</tr>';
            }).join('');
        }

        function entryHtml(entry, idx) {
            const history = (entry.history && entry.history.length) ? entry.history : [{ year: '', crops: '', inputs_used: '' }];
            let html = '';
            html += '<div class="d-flex justify-content-between align-items-center mb-2">';
            html += '<div class="fw-bold text-muted">' + L.field + ' #' + (idx + 1) + '</div>';
            if (!READONLY) {
                html += '<button type="button" class="btn btn-sm text-danger f19-del-entry" data-idx="' + idx + '"><i class="fa fa-trash"></i> ' + L.deleteField + '</button>';
            }
            html += '</div>';

            html += '<div class="row"><div class="col-md-6 mb-3">' +
                '<label class="form-label fw-bold">' + L.farmName + '</label>' +
                '<input type="text" class="form-control f19-input" data-idx="' + idx + '" data-field="farm_producer_name" value="' + esc(entry.farm_producer_name) + '" ' + (READONLY ? 'disabled' : '') + '/>' +
                '</div><div class="col-md-3 mb-3">' +
                '<label class="form-label fw-bold">' + L.fieldId + '</label>' +
                '<input type="text" class="form-control f19-input" data-idx="' + idx + '" data-field="field_id" value="' + esc(entry.field_id) + '" ' + (READONLY ? 'disabled' : '') + '/>' +
                '</div><div class="col-md-3 mb-3">' +
                '<label class="form-label fw-bold">' + L.transitionDate + '</label>' +
                '<input type="date" class="form-control f19-input" data-idx="' + idx + '" data-field="transition_start_date" value="' + esc(entry.transition_start_date) + '" ' + (READONLY ? 'disabled' : '') + '/>' +
                '</div></div>';

            html += '<div class="mb-3"><label class="form-label fw-bold d-block">' + L.managed3 + '</label>' +
                radioHtml(idx, 'managed3', entry.managed_3years, 'Yes', L.yes) +
                radioHtml(idx, 'managed3', entry.managed_3years, 'No', L.no) +
                '</div>';

            html += '<div class="osp-conditional" data-conditional-field="f19_managed3_' + idx + '" data-conditional-value="No">' +
                '<div class="mb-3"><label class="form-label fw-bold d-block">' + L.statements + '</label>' +
                radioHtml(idx, 'statements', entry.statements_attached, 'Yes', L.yes) +
                radioHtml(idx, 'statements', entry.statements_attached, 'No', L.no) +
                '</div></div>';

            html += '<div class="mb-3"><label class="form-label fw-bold d-block">' + L.certified + '</label>' +
                radioHtml(idx, 'certified', entry.field_certified, 'Yes', L.yes) +
                radioHtml(idx, 'certified', entry.field_certified, 'No', L.no) +
                '</div>';

            html += '<div class="osp-conditional" data-conditional-field="f19_certified_' + idx + '" data-conditional-value="Yes">' +
                '<div class="form-check mb-2 small text-muted">' +
                '<input class="form-check-input f19-check" type="checkbox" data-idx="' + idx + '" data-field="certification_attachment_needed" id="18_' + idx + '_certification_attachment_needed" ' + (entry.certification_attachment_needed === 'X' ? 'checked' : '') + (READONLY ? ' disabled' : '') + '/>' +
                '<label class="form-check-label" for="18_' + idx + '_certification_attachment_needed"><i class="fa fa-paperclip"></i> ' + L.attachCert + '</label>' +
                '</div></div>';

            html += '<div class="osp-conditional" data-conditional-field="f19_certified_' + idx + '" data-conditional-value="No">';
            html += '<div class="row"><div class="col-md-6 mb-3">' +
                '<label class="form-label fw-bold">' + L.lastSubstance + '</label>' +
                '<input type="text" class="form-control f19-input" data-idx="' + idx + '" data-field="last_substance_brand" value="' + esc(entry.last_substance_brand) + '" ' + (READONLY ? 'disabled' : '') + '/>' +
                '</div><div class="col-md-4 mb-3">' +
                '<label class="form-label fw-bold">' + L.lastDate + '</label>' +
                '<input type="date" class="form-control f19-input" data-idx="' + idx + '" data-field="last_substance_date" value="' + esc(entry.last_substance_date) + '" ' + (READONLY ? 'disabled' : '') + '/>' +
                '</div></div>';
            html += '<p class="mt-3">' + L.rowInstruction + '</p>';
            html += '<div class="table-responsive border rounded mb-3"><table class="table table-borderless table-hover mb-0">' +
                '<thead class="bg-light text-muted small"><tr><th>' + L.year + '</th><th>' + L.crops + '</th><th>' + L.inputsUsed + '</th><th class="text-center">' + L.action + '</th></tr></thead>' +
                '<tbody>' + historyRowsHtml(idx, history) + '</tbody>' +
                '</table></div>';
            if (!READONLY) {
                html += '<button type="button" class="btn btn-sm btn-outline-success mb-2 f19-add-year" data-idx="' + idx + '"><i class="fa fa-plus"></i> ' + L.addYear + '</button>';
            }
            html += '</div>'; // cierre osp-conditional certified=No

            return html;
        }

        function bindEvents() {
            container.querySelectorAll('.f19-input').forEach(function (el) {
                el.addEventListener('change', function () {
                    data[this.getAttribute('data-idx')][this.getAttribute('data-field')] = this.value;
                    sync();
                });
            });
            container.querySelectorAll('.f19-check').forEach(function (el) {
                el.addEventListener('change', function () {
                    data[this.getAttribute('data-idx')][this.getAttribute('data-field')] = this.checked ? 'X' : '';
                    sync();
                });
            });
            container.querySelectorAll('input[type="radio"][name^="f19_"]').forEach(function (el) {
                el.addEventListener('change', function () {
                    // name = "f19_<field>_<idx>" (el idx siempre es el último tramo).
                    const parts = this.name.split('_');
                    const idx = parts[parts.length - 1];
                    const fld = parts.slice(1, -1).join('_');
                    const fieldMap = { managed3: 'managed_3years', statements: 'statements_attached', certified: 'field_certified' };
                    data[idx][fieldMap[fld]] = this.value;
                    sync();
                    applyConditionals();
                });
            });
            container.querySelectorAll('.f19-hist-input').forEach(function (el) {
                el.addEventListener('change', function () {
                    const idx = this.getAttribute('data-idx');
                    const hIdx = this.getAttribute('data-hidx');
                    data[idx].history[hIdx][this.getAttribute('data-field')] = this.value;
                    sync();
                });
            });
            container.querySelectorAll('.f19-hist-del').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    const idx = btn.getAttribute('data-idx');
                    const hIdx = btn.getAttribute('data-hidx');
                    data[idx].history.splice(hIdx, 1);
                    if (!data[idx].history.length) data[idx].history.push({ year: '', crops: '', inputs_used: '' });
                    sync();
                    render();
                });
            });
            container.querySelectorAll('.f19-add-year').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    const idx = btn.getAttribute('data-idx');
                    data[idx].history.push({ year: '', crops: '', inputs_used: '' });
                    sync();
                    render();
                });
            });
            container.querySelectorAll('.f19-del-entry').forEach(function (btn) {
                btn.addEventListener('click', function () {
                    data.splice(btn.getAttribute('data-idx'), 1);
                    if (!data.length) data.push(emptyEntry());
                    sync();
                    render();
                });
            });
        }

        function render() {
            container.innerHTML = '';
            data.forEach(function (entry, idx) {
                const card = document.createElement('div');
                card.className = 'border rounded p-3 mb-3';
                card.innerHTML = entryHtml(entry, idx);
                container.appendChild(card);
            });
            sync();
            bindEvents();
            applyConditionals();
        }

        render();

        if (addBtn) {
            if (READONLY) {
                addBtn.disabled = true;
            } else {
                addBtn.addEventListener('click', function () {
                    data.push(emptyEntry());
                    sync();
                    render();
                });
            }
        }
    }

    initFieldHistoryBlock();

    // ============================================================
    // "NO APLICA ESTA SECCIÓN A MI OPERACIÓN" — retro de usuario piloto:
    // al marcar esta casilla, el resto de las preguntas de esa sección
    // debería minimizarse/ocultarse, para que el cliente no llene
    // información que no le corresponde. 100% genérico: cualquier
    // checkbox cuyo "name" sea EXACTAMENTE "<número>_na" (ej. "2_na",
    // "11_na") se trata como marcador de sección completa — a propósito
    // NO aplica a los demás checkboxes "_na" del módulo (ej.
    // "9_manure_na", "13_buffer_na"), que son de una subsección, no de
    // toda la sección, y sí deben seguir mostrando sus vecinos. El
    // checkbox y todo lo que esté ANTES de él en el tab-pane (encabezado,
    // cita regulatoria, nota de "solo primera vez", etc.) nunca se oculta
    // — solo lo que viene DESPUÉS.
    // ============================================================
    function initSectionNAHiding() {
        document.querySelectorAll('input[type="checkbox"].osp-input').forEach(function (cb) {
            if (!/^\d+_na$/.test(cb.name)) return;
            const wrapDiv = cb.closest('.form-check');
            const tabPane = cb.closest('.tab-pane');
            if (!wrapDiv || !tabPane) return;

            function applyHide() {
                let hide = false;
                Array.from(tabPane.children).forEach(function (child) {
                    if (child === wrapDiv) {
                        hide = cb.checked;
                        return;
                    }
                    child.classList.toggle('d-none', hide);
                });
            }
            cb.addEventListener('change', applyHide);
            applyHide();
        });
    }

    initSectionNAHiding();

    // ============================================================
    // FIRMA A MANO (modal con canvas) — retro de usuario piloto: el campo
    // de firma solo aceptaba texto libre; se pidió un modal donde el
    // usuario pueda "dibujar" su firma con mouse/dedo (como el módulo
    // Sign de Odoo), guardada como imagen PNG (base64) en el mismo
    // hidden input de siempre (#req_sign — la validación de Submit y
    // gatherFormData() ya lo leen genéricamente por .value, sin saber que
    // ahora es una imagen en vez de texto, así que no necesitan cambios).
    // Aplica en los 3 contextos (portal, público, Administrador de OSP) —
    // en READONLY solo se muestra la imagen ya guardada, sin editor.
    // ============================================================
    function initSignaturePad() {
        const hiddenInput = document.getElementById('req_sign');
        const wrap = document.getElementById('signature_pad_wrap');
        if (!hiddenInput || !wrap) return;

        const isSpanish = ['form_manejo_proceso', 'form_comercializador', 'form_cultivo'].indexOf(TECHNICAL_CODE) !== -1;
        const L = isSpanish ? {
            sign: 'Firmar', change: 'Cambiar firma', title: 'Firme aquí',
            instructions: 'Dibuje su firma dentro del recuadro con el mouse o el dedo.',
            clear: 'Limpiar', save: 'Guardar', cancel: 'Cancelar',
        } : {
            sign: 'Sign', change: 'Change signature', title: 'Sign here',
            instructions: 'Draw your signature inside the box below with your mouse or finger.',
            clear: 'Clear', save: 'Save', cancel: 'Cancel',
        };

        function renderTrigger() {
            wrap.innerHTML = '';
            if (hiddenInput.value) {
                const img = document.createElement('img');
                img.src = hiddenInput.value;
                img.style.maxHeight = '80px';
                img.style.border = '1px solid #dee2e6';
                img.style.borderRadius = '4px';
                img.style.display = 'block';
                img.style.marginBottom = '6px';
                img.style.background = '#fff';
                wrap.appendChild(img);
            }
            if (READONLY) return;
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline-success btn-sm';
            btn.innerHTML = '<i class="fa fa-pencil"></i> ' + (hiddenInput.value ? L.change : L.sign);
            btn.addEventListener('click', openModal);
            wrap.appendChild(btn);
        }

        function openModal() {
            const existing = document.getElementById('signature_modal');
            if (existing) existing.remove();
            const existingBackdrop = document.getElementById('signature_modal_backdrop');
            if (existingBackdrop) existingBackdrop.remove();

            const modalEl = document.createElement('div');
            modalEl.className = 'modal fade';
            modalEl.id = 'signature_modal';
            modalEl.tabIndex = -1;
            modalEl.innerHTML =
                '<div class="modal-dialog modal-dialog-centered">' +
                    '<div class="modal-content">' +
                        '<div class="modal-header">' +
                            '<h5 class="modal-title">' + L.title + '</h5>' +
                            '<button type="button" class="btn-close" id="btn_sign_close"></button>' +
                        '</div>' +
                        '<div class="modal-body">' +
                            '<p class="text-muted small">' + L.instructions + '</p>' +
                            '<canvas id="signature_canvas" style="border: 1px dashed #adb5bd; border-radius: 4px; width: 100%; height: 200px; touch-action: none; cursor: crosshair; background: #fff;"></canvas>' +
                        '</div>' +
                        '<div class="modal-footer">' +
                            '<button type="button" class="btn btn-outline-secondary btn-sm me-auto" id="btn_sign_clear">' + L.clear + '</button>' +
                            '<button type="button" class="btn btn-secondary" id="btn_sign_cancel">' + L.cancel + '</button>' +
                            '<button type="button" class="btn btn-success" id="btn_sign_save" disabled="disabled">' + L.save + '</button>' +
                        '</div>' +
                    '</div>' +
                '</div>';
            document.body.appendChild(modalEl);

            // Odoo no expone window.bootstrap como global en este bundle del
            // frontend (aunque el CSS de Bootstrap sí está disponible) — el
            // JS del componente Modal (new bootstrap.Modal(...)) rompía con
            // "bootstrap is not defined". Se maneja el show/hide a mano con
            // las mismas clases que usa Bootstrap (.modal.show, backdrop,
            // modal-open en <body>), sin depender de su JS.
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            backdrop.id = 'signature_modal_backdrop';
            document.body.appendChild(backdrop);
            document.body.classList.add('modal-open');
            modalEl.style.display = 'block';
            modalEl.classList.add('show');

            function closeModal() {
                document.body.classList.remove('modal-open');
                backdrop.remove();
                modalEl.remove();
            }
            modalEl.querySelector('#btn_sign_close').addEventListener('click', closeModal);
            modalEl.querySelector('#btn_sign_cancel').addEventListener('click', closeModal);
            backdrop.addEventListener('click', closeModal);

            const canvas = modalEl.querySelector('#signature_canvas');
            const ctx = canvas.getContext('2d');
            const saveBtn = modalEl.querySelector('#btn_sign_save');
            const clearBtn = modalEl.querySelector('#btn_sign_clear');
            let drawing = false;
            let hasDrawn = false;

            function resizeCanvas() {
                const ratio = window.devicePixelRatio || 1;
                const rect = canvas.getBoundingClientRect();
                canvas.width = rect.width * ratio;
                canvas.height = rect.height * ratio;
                ctx.scale(ratio, ratio);
                ctx.lineWidth = 2.5;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                ctx.strokeStyle = '#000000';
            }

            function pointerPos(evt) {
                const rect = canvas.getBoundingClientRect();
                const point = evt.touches && evt.touches.length ? evt.touches[0] : evt;
                return { x: point.clientX - rect.left, y: point.clientY - rect.top };
            }

            function startDraw(evt) {
                evt.preventDefault();
                drawing = true;
                const p = pointerPos(evt);
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
            }

            function moveDraw(evt) {
                if (!drawing) return;
                evt.preventDefault();
                const p = pointerPos(evt);
                ctx.lineTo(p.x, p.y);
                ctx.stroke();
                if (!hasDrawn) {
                    hasDrawn = true;
                    saveBtn.disabled = false;
                }
            }

            function endDraw() {
                drawing = false;
            }

            canvas.addEventListener('mousedown', startDraw);
            canvas.addEventListener('mousemove', moveDraw);
            window.addEventListener('mouseup', endDraw);
            canvas.addEventListener('touchstart', startDraw);
            canvas.addEventListener('touchmove', moveDraw);
            canvas.addEventListener('touchend', endDraw);

            clearBtn.addEventListener('click', function () {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                hasDrawn = false;
                saveBtn.disabled = true;
            });

            saveBtn.addEventListener('click', function () {
                hiddenInput.value = canvas.toDataURL('image/png');
                renderTrigger();
                closeModal();
            });

            // requestAnimationFrame en vez de un evento "shown" de Bootstrap
            // (que no existe sin su JS) — asegura que el modal ya esté
            // pintado en pantalla (display:block aplicado) antes de medir
            // su ancho real con getBoundingClientRect() en resizeCanvas().
            requestAnimationFrame(resizeCanvas);
        }

        renderTrigger();
    }

    initSignaturePad();

    // ============================================================
    // Caso especial: 1h "Same as Physical address" oculta los
    // campos de billing en vez de mostrarlos (lógica inversa).
    // ============================================================
    const sameAsBillingCk = document.querySelector('input[name="1h_same_as_billing"]');
    const billingFieldsWrap = document.getElementById('billing_fields_wrap');
    function toggleBillingFields() {
        if (!sameAsBillingCk || !billingFieldsWrap) return;
        billingFieldsWrap.style.display = sameAsBillingCk.checked ? 'none' : '';
    }
    if (sameAsBillingCk) {
        sameAsBillingCk.addEventListener('change', toggleBillingFields);
        toggleBillingFields();
    }

    // --- Filtro en cascada País -> Estado — genérico, soporta varios pares
    // en la misma página (1g/1e para la dirección física, y el mismo
    // patrón para 1h_billing_country/1h_billing_state en Facturación —
    // retro de usuario piloto: 1h no desglosaba estado/país como 1e/1g). ---
    function initCountryStateFilter(countryId, stateId) {
        const countrySelect = document.getElementById(countryId);
        const stateSelect = document.getElementById(stateId);
        if (!countrySelect || !stateSelect) return;

        function filterStatesByCountry() {
            const selectedCountry = countrySelect.value;
            let currentStateStillValid = false;

            Array.from(stateSelect.options).forEach(opt => {
                if (!opt.value) return; // deja siempre visible la opción "-- Select --"
                const belongsToCountry = opt.getAttribute('data-country') === selectedCountry;
                opt.hidden = selectedCountry !== '' && !belongsToCountry;
                if (opt.selected && belongsToCountry) currentStateStillValid = true;
            });

            if (selectedCountry !== '' && !currentStateStillValid) {
                stateSelect.value = '';
            }
        }

        countrySelect.addEventListener('change', filterStatesByCountry);
        filterStatesByCountry();
    }

    initCountryStateFilter('1g_country', '1e_state');
    initCountryStateFilter('1h_billing_country', '1h_billing_state');

    // ============================================================
    // MODO SOLO LECTURA: deshabilita todos los campos normales
    // (las tablas dinámicas ya se deshabilitan solas al renderizar)
    // ============================================================
    if (READONLY) {
        document.querySelectorAll('.osp-input').forEach(el => { el.disabled = true; });
    }

    // ============================================================
    // GUARDADO GENERAL
    // ============================================================
    function gatherFormData() {
        let data = {};
        document.querySelectorAll('.osp-input').forEach(el => {
            if (el.type === 'checkbox' && el.dataset.group) {
                const groupKey = el.dataset.group;
                if (!data[groupKey]) data[groupKey] = [];
                if (el.checked) data[groupKey].push(el.value);
            } else if (el.type === 'radio' || el.type === 'checkbox') {
                if (el.checked) data[el.name] = el.value;
            } else {
                data[el.name] = el.value;
            }
        });
        return data;
    }

    // ============================================================
    // Habilita la subida de adjuntos justo después del primer guardado
    // de un formulario nuevo (antes no existía osp_id real, así que no
    // se podía subir nada — se mostraba un aviso explicándolo en vez de
    // solo ocultar el botón sin decir por qué). No hace falta recargar
    // la página: si el formulario de subida ya existía en el DOM (caso
    // normal, formulario ya guardado antes), solo se actualiza su URL;
    // si no existía (caso nuevo), se construye aquí.
    // ============================================================
    function enableAttachmentsUpload(realOspId) {
        const notice = document.getElementById('attachments_save_first_notice');
        if (notice) notice.style.display = 'none';

        const existingForm = document.getElementById('attachments_upload_form');
        if (existingForm) {
            existingForm.action = `/my/osp/upload/${realOspId}`;
            return;
        }

        const section = document.getElementById('sec21');
        if (!section) return;

        const wrap = document.createElement('div');
        wrap.id = 'attachments_upload_wrap';
        wrap.className = 'mb-4';
        wrap.innerHTML = `
            <form id="attachments_upload_form" action="/my/osp/upload/${realOspId}" method="POST" enctype="multipart/form-data" class="d-flex align-items-center gap-2 flex-wrap">
                <input type="hidden" name="csrf_token" value="${window.OSP_CSRF_TOKEN || ''}"/>
                <input type="file" name="osp_files" multiple="multiple" class="form-control" style="max-width: 400px;"/>
                <button type="submit" class="btn btn-outline-success"><i class="fa fa-upload"></i> Upload</button>
            </form>
        `;

        if (notice && notice.parentNode) {
            notice.insertAdjacentElement('afterend', wrap);
        } else {
            section.appendChild(wrap);
        }
    }

    // ============================================================
    // CLOUDFLARE TURNSTILE — verificación de que quien envía el formulario
    // público es humano. Carga el script oficial de Cloudflare una sola
    // vez, e inserta el contenedor del widget justo antes del botón de
    // Submit (#btn_submit_osp) — Cloudflare detecta ese <div class="cf-
    // turnstile"> automáticamente y lo renderiza solo, sin más código
    // nuestro. La verificación real (contra el token que esto genera)
    // ocurre server-side en controllers/portal.py (_verify_turnstile).
    // ============================================================
    function initTurnstileWidget(siteKey) {
        if (!document.getElementById('cf-turnstile-script')) {
            const script = document.createElement('script');
            script.id = 'cf-turnstile-script';
            script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
            script.async = true;
            script.defer = true;
            document.head.appendChild(script);
        }

        const submitBtn = document.getElementById('btn_submit_osp');
        if (submitBtn && !document.getElementById('osp_turnstile_widget')) {
            const wrap = document.createElement('div');
            wrap.id = 'osp_turnstile_widget';
            wrap.className = 'cf-turnstile mb-3';
            wrap.setAttribute('data-sitekey', siteKey);
            submitBtn.parentNode.insertBefore(wrap, submitBtn);
        }
    }

    // ============================================================
    // GUARDADO DEL NAVEGANTE PÚBLICO: "Save progress" nunca pega al
    // servidor — se guarda solo en localStorage. El único momento en que
    // se habla con Odoo es en el Submit final (POST a /osp/public/submit,
    // que crea el registro directo en submitted). Al tener éxito, se
    // limpia el localStorage (ya no hace falta) y se manda al navegante a
    // la pantalla de agradecimiento, donde todavía puede adjuntar
    // archivos mientras el registro no tenga cliente asignado.
    // ============================================================
    function savePublicForm(isSubmit) {
        const statusText = document.getElementById('save_status');
        const finalData = gatherFormData();

        // El widget de Turnstile solo importa en el Submit final — el
        // "Save progress" nunca toca el servidor (ver comentario arriba),
        // así que no tiene sentido bloquearlo por esto.
        if (isSubmit && TURNSTILE_SITE_KEY) {
            const token = window.turnstile ? window.turnstile.getResponse() : '';
            if (!token) {
                const msg = 'Please wait a moment for the security check to finish, then try again.';
                if (statusText) {
                    statusText.style.display = 'inline';
                    statusText.innerText = msg;
                    statusText.classList.replace('text-muted', 'text-danger');
                } else {
                    alert(msg);
                }
                return;
            }
        }

        if (!isSubmit) {
            try {
                localStorage.setItem(PUBLIC_STORAGE_KEY, JSON.stringify(finalData));
                if (statusText) {
                    statusText.style.display = 'inline';
                    statusText.innerText = 'Saved!';
                    setTimeout(() => statusText.style.display = 'none', 2000);
                }
            } catch (e) {
                console.error('🔴 [OSP] No se pudo guardar el avance localmente:', e);
                if (statusText) {
                    statusText.style.display = 'inline';
                    statusText.innerText = 'Error al guardar';
                    statusText.classList.replace('text-muted', 'text-danger');
                }
            }
            return;
        }

        if (statusText) {
            statusText.style.display = 'inline';
            statusText.innerText = 'Saving...';
        }

        fetch('/osp/public/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    form_data: finalData,
                    technical_code: TECHNICAL_CODE,
                    turnstile_token: (TURNSTILE_SITE_KEY && window.turnstile) ? window.turnstile.getResponse() : ''
                }
            })
        }).then(res => res.json())
          .then(data => {
              if (data.result && data.result.success) {
                  try { localStorage.removeItem(PUBLIC_STORAGE_KEY); } catch (e) { /* no-op */ }
                  const ospId = data.result.osp_id;
                  const goToThankYou = () => { window.location.href = `/osp/public/thankyou/${ospId}`; };

                  // Sube en un solo paso, automáticamente, todo lo que el
                  // navegante fue seleccionando por sección durante el
                  // llenado (ver initPublicFileUploads() más arriba) —
                  // reutiliza el MISMO endpoint que ya usa la subida manual
                  // de la pantalla "Thank you" (controllers/portal.py,
                  // public_osp_upload), así que ningún cambio de servidor
                  // es indispensable para el flujo normal de esa pantalla.
                  const checkboxIds = Object.keys(pendingPublicFiles);
                  if (!checkboxIds.length) {
                      goToThankYou();
                      return;
                  }

                  if (statusText) statusText.innerText = 'Uploading attachments...';
                  const uploadData = new FormData();
                  uploadData.append('csrf_token', window.OSP_CSRF_TOKEN || '');
                  checkboxIds.forEach(function (checkboxId) {
                      const file = pendingPublicFiles[checkboxId];
                      // Código de pregunta (ej. "2b") tomado del id del
                      // checkbox — mismo criterio que initAttachmentChecklist(),
                      // para que ir.attachment quede etiquetado con a qué
                      // pregunta corresponde cada archivo.
                      uploadData.append('osp_files', file, file.name);
                      uploadData.append('osp_labels', checkboxId.split('_')[0]);
                  });
                  fetch(`/osp/public/upload/${ospId}`, { method: 'POST', body: uploadData })
                      .catch(err => console.error('🔴 [OSP] No se pudieron subir los adjuntos seleccionados por sección:', err))
                      .then(goToThankYou);
              } else {
                  console.error('🔴 [OSP] Error al enviar el formulario:', data.error || data);
                  if (statusText) {
                      statusText.innerText = 'Error al guardar';
                      statusText.classList.replace('text-muted', 'text-danger');
                  }
              }
          })
          .catch(err => {
              console.error('🔴 [OSP] Fallo de red al enviar:', err);
              if (statusText) {
                  statusText.innerText = 'Error al guardar';
                  statusText.classList.replace('text-muted', 'text-danger');
              }
          });
    }

    function saveForm(isSubmit) {
        if (PUBLIC_MODE) {
            savePublicForm(isSubmit);
            return;
        }

        const statusText = document.getElementById('save_status');
        if (statusText) {
            statusText.style.display = 'inline';
            statusText.innerText = 'Saving...';
        }

        const finalData = gatherFormData();

        // Mientras ospId siga en 0 (formulario nuevo, sin registro creado
        // todavía), el primer guardado pega a /my/osp/save_new, que SÍ crea
        // el registro. De ahí en adelante (ospId ya real) se usa la ruta
        // normal — así nunca se genera un draft "basura" con solo entrar a
        // ver el formulario sin guardar nada.
        const isNewRecord = ospId === 0;
        const url = isNewRecord ? '/my/osp/save_new' : `/my/osp/save/${ospId}`;
        const params = isNewRecord
            ? { service_id: newServiceId, template_id: newTemplateId, form_data: finalData, is_submit: isSubmit }
            : { form_data: finalData, is_submit: isSubmit };

        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: params
            })
        }).then(res => res.json())
          .then(data => {
              if (data.result && data.result.success) {
                  if (isNewRecord && data.result.osp_id) {
                      // El registro ya existe: de aquí en adelante los
                      // guardados van por la ruta normal con este id real,
                      // y se actualiza la URL sin recargar la página para
                      // que un refresh no intente crear un segundo registro.
                      ospId = data.result.osp_id;
                      ospIdInput.value = ospId;
                      if (window.history && window.history.replaceState) {
                          window.history.replaceState(null, '', `/my/osp/form/${ospId}`);
                      }
                      enableAttachmentsUpload(ospId);
                  }
                  if (statusText) {
                      statusText.innerText = 'Saved!';
                      setTimeout(() => statusText.style.display = 'none', 2000);
                  }
                  if (isSubmit) window.location.href = '/my/osp';
              } else {
                  // Antes esto se quedaba en silencio: si Odoo devuelve un
                  // error JSON-RPC (excepción del servidor) en vez de
                  // {success:false}, no había forma de verlo en consola.
                  // Ahora se imprime completo (incluye el traceback en
                  // data.error.data.debug cuando el server está en modo dev).
                  console.error('🔴 [OSP] Error al guardar el formulario:', data.error || data);
                  if (statusText) {
                      statusText.innerText = 'Error al guardar';
                      statusText.classList.replace('text-muted', 'text-danger');
                  }
              }
          })
          .catch(err => {
              // Fallo de red (fetch nunca llegó a completarse) — esto sí
              // antes tampoco se mostraba en consola de forma clara.
              console.error('🔴 [OSP] Fallo de red al guardar:', err);
              if (statusText) {
                  statusText.innerText = 'Error al guardar';
                  statusText.classList.replace('text-muted', 'text-danger');
              }
          });
    }

    const saveBtn = document.getElementById('btn_save_progress');
    if (saveBtn) {
        saveBtn.addEventListener('click', function () {
            saveForm(false);
        });
    }

    const submitBtn = document.getElementById('btn_submit_osp');
    if (submitBtn) {
        submitBtn.addEventListener('click', function () {
            const nameEl = document.getElementById('req_name');
            const signEl = document.getElementById('req_sign');
            const dateEl = document.getElementById('req_date');
            if (!nameEl.value || !signEl.value || !dateEl.value) {
                alert("Please complete the electronic signature fields before submitting.");
                return;
            }
            // Antes había un confirm() aquí advirtiendo "no podrás editar
            // después de enviar" — esa regla ya no aplica (el cliente
            // siempre puede seguir editando, incluso después de Submit; ver
            // CONTEXT.md punto 6), así que el aviso quedaba engañoso. Se
            // quitó: Submit ya no pide confirmación, va directo a la lista.
            saveForm(true);
        });
    }

    initAttachmentChecklist(TECHNICAL_CODE);

    // ============================================================
    // SELECCIÓN DE ADJUNTOS POR SECCIÓN (solo navegante público) — retro
    // de usuario piloto: "que no se le olvide adjuntar algo". El registro
    // sigue sin crearse hasta el Submit (no se reabre el problema de
    // registros basura) — lo único que cambia es que el archivo se ELIGE
    // en el navegador justo al lado de cada casilla "Attach .../Adjunte
    // ..." desde que se llena esa sección, en vez de tener que recordar
    // todo hasta el final. La subida real a Odoo sigue pasando toda junta,
    // automáticamente, justo después de que el Submit cree el registro
    // (ver el bloque de éxito dentro de savePublicForm() más abajo).
    // ============================================================
    if (PUBLIC_MODE) {
        initPublicFileUploads();
    }

    function initPublicFileUploads() {
        document.querySelectorAll('input[id$="_attachment_needed"]').forEach(function (cb) {
            // La Sección 19 (Crop/Cultivo) es un bloque repetible que se
            // reconstruye por completo (innerHTML) en cada cambio — un
            // picker inyectado aquí se perdería en el primer re-render (ver
            // initFieldHistoryBlock() más arriba). Se deja fuera a
            // propósito: esa casilla en particular sigue funcionando con la
            // subida al final (pantalla "Thank you"), solo sin el atajo por
            // sección.
            if (cb.closest('#fields19_container')) return;

            const wrapDiv = cb.closest('.form-check');
            if (!wrapDiv) return;

            const picker = document.createElement('div');
            picker.className = 'mb-2';
            picker.style.marginLeft = '1.5rem';
            picker.style.display = cb.checked ? '' : 'none';

            const input = document.createElement('input');
            input.type = 'file';
            input.className = 'form-control form-control-sm';
            input.style.maxWidth = '350px';
            picker.appendChild(input);
            wrapDiv.insertAdjacentElement('afterend', picker);

            cb.addEventListener('change', function () {
                picker.style.display = cb.checked ? '' : 'none';
                if (!cb.checked) {
                    input.value = '';
                    delete pendingPublicFiles[cb.id];
                }
            });

            input.addEventListener('change', function () {
                if (input.files && input.files[0]) {
                    pendingPublicFiles[cb.id] = input.files[0];
                } else {
                    delete pendingPublicFiles[cb.id];
                }
            });
        });
    }
}

// ============================================================
// CHECKLIST DE ADJUNTOS PENDIENTES (retro de usuario piloto) — recordatorio
// de qué casillas "Attach .../Adjunte ..." (sufijo de id "_attachment_needed",
// ícono de clip 📎) están marcadas en cualquier parte del formulario,
// mostrado justo en la pestaña de Adjuntos para que el cliente no tenga que
// recordar de memoria qué dijo que iba a subir. 100% genérico: lee directo
// del DOM (no depende de qué formulario sea), así que funciona igual en los
// 6 sin necesitar ningún dato extra por formulario — ver también el
// equivalente server-side para la pantalla pública de "Thank you"
// (osp_attachment_markers.py + osp_request.py, get_pending_attachment_checklist()).
// Cada item es un link que salta a su sección — funciona tanto en el
// formulario de portal como en el público antes de enviar (en ambos casos
// sigue siendo el mismo formulario "vivo" de una sola página).
// ============================================================
function initAttachmentChecklist(technicalCode) {
    // Localiza la pestaña de Adjuntos por su link de navegación lateral —
    // es el único que trae el ícono de clip, mismo criterio en los 6
    // formularios (no hace falta saber si es "#sec21", "#sec16", etc.).
    const navIcon = document.querySelector('a[data-bs-toggle="list"] i.fa-paperclip');
    if (!navIcon) return;
    const tabLink = navIcon.closest('a');
    const tabId = tabLink ? tabLink.getAttribute('href') : null;
    const tabPane = tabId ? document.querySelector(tabId) : null;
    const heading = tabPane ? tabPane.querySelector('h4') : null;
    if (!heading) return;

    let container = document.getElementById('osp_attachment_checklist');
    if (!container) {
        container = document.createElement('div');
        container.id = 'osp_attachment_checklist';
        container.className = 'mb-4';
        heading.insertAdjacentElement('afterend', container);
    }

    // Los 6 formularios comparten el mismo motor; solo estos 3 son
    // nativos en español (ver CONTEXT.md) — no depende de detectar el
    // idioma del navegador ni de una variable nueva por formulario.
    const SPANISH_FORMS = ['form_manejo_proceso', 'form_comercializador', 'form_cultivo'];
    const checklistTitle = SPANISH_FORMS.indexOf(technicalCode) !== -1
        ? 'Indicó que adjuntaría los siguientes documentos:'
        : 'You indicated you would attach the following documents:';

    function render() {
        const checked = document.querySelectorAll('input[id$="_attachment_needed"]:checked');
        container.innerHTML = '';
        if (!checked.length) return;

        const box = document.createElement('div');
        box.className = 'alert alert-info';

        const title = document.createElement('div');
        title.className = 'fw-bold mb-2';
        title.innerHTML = '<i class="fa fa-list-check"></i> ';
        title.appendChild(document.createTextNode(checklistTitle));
        box.appendChild(title);

        const ul = document.createElement('ul');
        ul.className = 'mb-0';
        checked.forEach(function (input) {
            const label = document.querySelector('label[for="' + input.id + '"]');
            if (!label) return;
            // El id del checkbox siempre empieza con el código de la
            // pregunta a la que pertenece (ej. "2b_certificate_attachment_
            // needed" -> "2b") — se antepone al texto para que el usuario
            // identifique de inmediato a cuál pregunta se refiere (retro
            // de usuario piloto).
            const questionCode = input.id.split('_')[0];
            const text = questionCode + '. ' + label.textContent.trim();
            const pane = input.closest('.tab-pane');
            const li = document.createElement('li');
            if (pane && pane.id) {
                const a = document.createElement('a');
                a.href = '#' + pane.id;
                a.setAttribute('data-bs-toggle', 'list');
                a.className = 'text-decoration-none';
                a.textContent = text;
                li.appendChild(a);
            } else {
                li.textContent = text;
            }
            ul.appendChild(li);
        });
        box.appendChild(ul);
        container.appendChild(box);
    }

    render();
    // Se recalcula cada vez que el visitante marca/desmarca cualquier
    // casilla de adjunto pendiente, sin importar en qué sección esté.
    document.addEventListener('change', function (e) {
        if (e.target && e.target.id && e.target.id.endsWith('_attachment_needed')) {
            render();
        }
    });
}

// Disparador defensivo: si el DOM ya está listo cuando este script se ejecuta
// (común con bundles de assets que cargan de forma diferida/"lazy" en Odoo),
// corremos de inmediato. Si no, esperamos el evento normalmente.
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initOspForm);
} else {
    initOspForm();
}

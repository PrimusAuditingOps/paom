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
    // Con el código técnico en la llave, cada tipo de formulario público
    // (Crop, y a futuro Handler, Cultivo, etc.) guarda su propio avance
    // en localStorage sin pisar el de otro si el navegante llena más de
    // uno en el mismo navegador.
    const PUBLIC_STORAGE_KEY = 'osp_public_draft_' + TECHNICAL_CODE;

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
        fields: { // 4h
            jsonInputId: '4h_fields_json', tbodyId: 'fields_tbody', addBtnId: 'btn_add_field',
            columns: [
                { key: 'field_id', type: 'text', placeholder: 'Field ID (Name/Code)...' },
                { key: 'parcel_address', type: 'text', placeholder: 'Parcel Address / Legal Description...' },
                { key: 'area_type', type: 'select', options: ['Organic', 'Transitional', 'Non-Organic'] },
                { key: 'units', type: 'select', options: ['Acre', 'Hectare'] },
                { key: 'rented_or_owned', type: 'select', options: ['Rented', 'Owned'] },
            ],
        },
        crops: { // 4j
            jsonInputId: '4j_crops_json', tbodyId: 'crops_tbody', addBtnId: 'btn_add_crop',
            columns: [
                { key: 'crop_requested', type: 'text', placeholder: 'Crop requested for certification...' },
                { key: 'field_id', type: 'text', placeholder: 'Field ID where planted this year...' },
                { key: 'total_planted_area', type: 'text', placeholder: 'Total planted area...' },
                { key: 'area_units', type: 'select', options: ['Acre', 'Hectare'] },
                { key: 'projected_yield', type: 'text', placeholder: 'Projected yield...' },
                { key: 'yield_units', type: 'select', options: ['Acre', 'Hectare'] },
            ],
        },
        products: { // 5d
            jsonInputId: '5d_products_json', tbodyId: 'products_tbody', addBtnId: 'btn_add_product',
            columns: [
                { key: 'product', type: 'text', placeholder: 'Product requested for certification...' },
                { key: 'id_mark', type: 'text', placeholder: 'ID Mark (Labels)...' },
                { key: 'label_type', type: 'text', placeholder: 'Retail / Non-Retail / Private Label...' },
                { key: 'packing_with_id', type: 'select', options: ['Y', 'N'] },
                { key: 'organic_or_100', type: 'select', options: ['Organic', '100% Organic'] },
                { key: 'international_market', type: 'text', placeholder: 'International market / equivalency request...' },
            ],
        },
        seeds: { // 8a
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
        planting_stock: { // 8g
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
        rotation: { // 10
            jsonInputId: '10_rotation_json', tbodyId: 'rotation_tbody', addBtnId: 'btn_add_rotation',
            columns: [
                { key: 'rotation_plan', type: 'text', placeholder: 'Crop rotation plan (sequence of crops)...' },
                { key: 'objectives', type: 'text', placeholder: 'Objectives (Increase Organic Matter, Nutrient Mgmt, Pest/Disease, Erosion, Other)...' },
            ],
        },
        inputs: { // 12a
            jsonInputId: '12a_inputs_json', tbodyId: 'inputs_tbody', addBtnId: 'btn_add_input',
            columns: [
                { key: 'input_used_for', type: 'select', options: ['Fertility', 'Pest', 'Disease', 'Post-Harvest', 'Seed Treatment', 'Perennial Treatment'] },
                { key: 'brand_name', type: 'text', placeholder: 'Brand Name...' },
                { key: 'ingredients', type: 'text', placeholder: 'Ingredients...' },
                { key: 'compliance_approval_by', type: 'text', placeholder: 'Compliance approval by...' },
                { key: 'label_compliance_docs_attached', type: 'select', options: ['Y', 'N'] },
                { key: 'restrictions_compliance_description', type: 'text', placeholder: 'How you comply with NOP annotation...' },
            ],
        },
        equipment: { // 14a
            jsonInputId: '14a_equipment_json', tbodyId: 'equipment_tbody', addBtnId: 'btn_add_equipment',
            columns: [
                { key: 'equipment_name_model_code', type: 'text', placeholder: 'Equipment Name / Model / Code...' },
                { key: 'owned_rented_custom', type: 'select', options: ['Owned', 'Rented', 'Custom'] },
                { key: 'used_for', type: 'select', options: ['Organic', 'Non-Organic', 'Both Organic and Non-Organic'] },
                { key: 'cleaning_method', type: 'text', placeholder: 'How is equipment cleaned before use...' },
            ],
        },
        history: { // 19
            jsonInputId: '19_history_json', tbodyId: 'history_tbody', addBtnId: 'btn_add_history',
            columns: [
                { key: 'year', type: 'text', placeholder: 'Year...' },
                { key: 'crops', type: 'text', placeholder: 'Crop(s) planted...' },
                { key: 'inputs_used', type: 'text', placeholder: 'Inputs used (brand, formulation)...' },
            ],
        },
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
                { key: 'label_type', type: 'text', placeholder: 'Retail / Non-Retail / Private Label...' },
                { key: 'packing_with_id', type: 'select', options: ['Y', 'N'] },
                { key: 'organic_or_100', type: 'text', placeholder: 'Organic or 100% Organic?...' },
                { key: 'international_market', type: 'text', placeholder: 'International market...' },
            ],
        },
        handler_inputs: { // 9a
            jsonInputId: '9a_inputs_json', tbodyId: 'handler_inputs_tbody', addBtnId: 'btn_add_handler_input',
            columns: [
                { key: 'input_used_for', type: 'select', options: ['Pest', 'Disease', 'Post-Harvest', 'Sanitizer', 'Other'] },
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
                { key: 'label_type', type: 'text', placeholder: 'Retail / Non-Retail / Private Label...' },
                { key: 'organic_or_100', type: 'text', placeholder: 'Organic or 100% Organic?...' },
                { key: 'international_market', type: 'text', placeholder: 'International market...' },
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
                config._data[idx][fld] = this.value;
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

    // --- Filtro en cascada País -> Estado (1g -> 1e) ---
    const countrySelect = document.getElementById('1g_country');
    const stateSelect = document.getElementById('1e_state');

    function filterStatesByCountry() {
        if (!countrySelect || !stateSelect) return;
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

    if (countrySelect) {
        countrySelect.addEventListener('change', filterStatesByCountry);
        filterStatesByCountry();
    }

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
                params: { form_data: finalData, technical_code: TECHNICAL_CODE }
            })
        }).then(res => res.json())
          .then(data => {
              if (data.result && data.result.success) {
                  try { localStorage.removeItem(PUBLIC_STORAGE_KEY); } catch (e) { /* no-op */ }
                  window.location.href = `/osp/public/thankyou/${data.result.osp_id}`;
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
}

// Disparador defensivo: si el DOM ya está listo cuando este script se ejecuta
// (común con bundles de assets que cargan de forma diferida/"lazy" en Odoo),
// corremos de inmediato. Si no, esperamos el evento normalmente.
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initOspForm);
} else {
    initOspForm();
}

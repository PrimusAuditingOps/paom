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

    const ospIdInput = document.querySelector('input[name="osp_id"]');
    if (!ospIdInput) return;
    const ospId = parseInt(ospIdInput.value);

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

    function saveForm(isSubmit) {
        const statusText = document.getElementById('save_status');
        if (statusText) {
            statusText.style.display = 'inline';
            statusText.innerText = 'Saving...';
        }

        const finalData = gatherFormData();

        fetch(`/my/osp/save/${ospId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    form_data: finalData,
                    is_submit: isSubmit
                }
            })
        }).then(res => res.json())
          .then(data => {
              if (data.result && data.result.success) {
                  if (statusText) {
                      statusText.innerText = 'Saved!';
                      setTimeout(() => statusText.style.display = 'none', 2000);
                  }
                  if (isSubmit) window.location.href = '/my/osp';
              } else {
                  if (statusText) {
                      statusText.innerText = 'Error al guardar';
                      statusText.classList.replace('text-muted', 'text-danger');
                  }
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
            if (confirm("Are you sure you want to submit your Organic System Plan? You will not be able to edit it after submission.")) {
                saveForm(true);
            }
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

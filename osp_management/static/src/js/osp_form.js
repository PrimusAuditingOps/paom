// Este mensaje saldrá en la consola en TODAS las páginas del portal 
// y nos confirmará que Odoo ya enlazó el archivo.
console.log("🟢 [OSP] Archivo Javascript cargado exitosamente por Odoo 17.");

function initOspForm() {
    // Solo ejecutamos el código si estamos en la página del formulario
    const formContent = document.getElementById('form-content');
    if (!formContent) return; 

    console.log("🟢 [OSP] Formulario detectado. Arrancando motor de tabla dinámica...");

    const ospIdInput = document.querySelector('input[name="osp_id"]');
    if (!ospIdInput) return;
    
    const ospId = parseInt(ospIdInput.value);
    const sitesTbody = document.getElementById('sites_tbody');
    const sitesJsonInput = document.getElementById('4g_sites_json');
    let sitesData = [];
    
    try {
        sitesData = JSON.parse(sitesJsonInput.value || '[]');
    } catch(e) { 
        sitesData = []; 
    }

    // Definición única de las columnas de la tabla Sites (4g).
    // Si el header del HTML cambia, solo hay que actualizar esta lista.
    const SITE_FIELDS = [
        { key: 'site_id', placeholder: 'Site ID / Name...' },
        { key: 'site_address', placeholder: 'Site Address...' },
        { key: 'city_state', placeholder: 'City, State...' },
        { key: 'zip', placeholder: 'Zip...' },
        { key: 'contact', placeholder: 'Contact Name and Phone Number...' },
        { key: 'description', placeholder: 'Description of Site activities and responsibilities...' },
    ];

    function emptySiteRow() {
        const row = {};
        SITE_FIELDS.forEach(f => { row[f.key] = ''; });
        return row;
    }

    function renderSitesTable() {
        sitesTbody.innerHTML = '';
        if (sitesData.length === 0) {
            sitesData.push(emptySiteRow());
        }

        sitesData.forEach((site, index) => {
            const tr = document.createElement('tr');
            const cells = SITE_FIELDS.map(f => `
                <td><input type="text" class="form-control border-0 bg-transparent site-input"
                    data-index="${index}" data-field="${f.key}"
                    value="${(site[f.key] || '').replace(/"/g, '&quot;')}"
                    placeholder="${f.placeholder}"/></td>
            `).join('');
            tr.innerHTML = `
                ${cells}
                <td class="text-center">
                    <button type="button" class="btn btn-sm text-danger btn-delete-site" data-index="${index}">
                        <i class="fa fa-trash"></i>
                    </button>
                </td>
            `;
            sitesTbody.appendChild(tr);
        });
        sitesJsonInput.value = JSON.stringify(sitesData);
        bindTableEvents();
    }

    function bindTableEvents() {
        document.querySelectorAll('.site-input').forEach(input => {
            input.addEventListener('change', function() {
                const idx = this.getAttribute('data-index');
                const fld = this.getAttribute('data-field');
                sitesData[idx][fld] = this.value;
                sitesJsonInput.value = JSON.stringify(sitesData);
            });
        });
        document.querySelectorAll('.btn-delete-site').forEach(btn => {
            btn.addEventListener('click', function() {
                const idx = this.getAttribute('data-index');
                sitesData.splice(idx, 1);
                renderSitesTable();
            });
        });
    }

    // Botón Add Site
    document.getElementById('btn_add_site').addEventListener('click', function() {
        console.log("🟢 [OSP] Agregando nueva fila...");
        sitesData.push(emptySiteRow());
        renderSitesTable();
    });

    // --- GUARDADO GENERAL ---
    function gatherFormData() {
        let data = {};
        document.querySelectorAll('.osp-input').forEach(el => {
            if(el.type === 'radio' || el.type === 'checkbox') {
                if(el.checked) data[el.name] = el.value;
            } else {
                data[el.name] = el.value;
            }
        });
        return data;
    }

    function saveForm(isSubmit) {
        const statusText = document.getElementById('save_status');
        if(statusText) {
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
              if(data.result && data.result.success) {
                  if(statusText) {
                      statusText.innerText = 'Saved!';
                      setTimeout(() => statusText.style.display = 'none', 2000);
                  }
                  if(isSubmit) window.location.href = '/my/osp';
              } else {
                  if(statusText) {
                      statusText.innerText = 'Error al guardar';
                      statusText.classList.replace('text-muted', 'text-danger');
                  }
              }
          });
    }

    document.getElementById('btn_save_progress').addEventListener('click', function() {
        saveForm(false);
    });

    document.getElementById('btn_submit_osp').addEventListener('click', function() {
        if(!document.getElementById('req_name').value || !document.getElementById('req_sign').value || !document.getElementById('req_date').value) {
            alert("Please complete the electronic signature fields before submitting.");
            return;
        }
        if(confirm("Are you sure you want to submit your Organic System Plan? You will not be able to edit it after submission.")) {
            saveForm(true);
        }
    });

    // Arrancar la tabla
    renderSitesTable();
}

// Disparador defensivo: si el DOM ya está listo cuando este script se ejecuta
// (común con bundles de assets que cargan de forma diferida/"lazy" en Odoo),
// corremos de inmediato. Si no, esperamos el evento normalmente.
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initOspForm);
} else {
    initOspForm();
}
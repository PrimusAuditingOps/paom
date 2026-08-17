# -*- coding: utf-8 -*-
"""
Migración de datos (17/ago): corrige retroactivamente los registros de
osp.request que quedaron con name = 'Nuevo' (el default de Odoo), ahora que
el modelo genera el nombre como "<Servicio> - <Tipo de Formulario>" al crear
(ver override de create() en models/osp_request.py). Se ejecuta una sola vez,
automáticamente, la próxima vez que se actualice el módulo (-u osp_management)
porque el número de versión en __manifest__.py subió.
"""


def migrate(cr, version):
    cr.execute("""
        SELECT r.id, s.name, t.name
        FROM osp_request r
        LEFT JOIN osp_service s ON s.id = r.service_id
        LEFT JOIN osp_form_template t ON t.id = r.form_template_id
        WHERE r.name IS NULL OR r.name = 'Nuevo'
    """)
    rows = cr.fetchall()

    for req_id, service_name, template_name in rows:
        parts = [p for p in (service_name, template_name) if p]
        if not parts:
            continue
        new_name = ' - '.join(parts)
        cr.execute("UPDATE osp_request SET name = %s WHERE id = %s", (new_name, req_id))

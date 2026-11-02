# -*- coding: utf-8 -*-
"""
Migración de datos (17/ago) — intento #3 para el backend en inglés.

Causa real del bug de 17.0.1.0.7 (confirmado por el usuario con capturas):
los campos traducibles de Odoo 17 se guardan como JSONB por idioma
(`{'en_US': '...', 'es_MX': '...', ...}`). Mientras un campo NUNCA tuvo
una traducción explícita por idioma (nuestro caso: los campos del módulo
solo tenían el texto fuente en español, igual para cualquier idioma por
simple fallback), el PRIMER write bajo un `lang=` específico no "separa"
el valor — lo reemplaza de forma UNIFORME para todos los idiomas, porque
Odoo no tenía nada con qué "dividir". Por eso 17.0.1.0.7 dejó "DBA Name"
en inglés Y en las 3 variantes de español a la vez.

Esta base tiene 4 idiomas activos (confirmado por el diálogo "Translate"
de la captura): English (US), Spanish (CL), Spanish (CR), Spanish (MX) —
no solo los 2 que se habían mencionado antes. El fix: escribir CADA
idioma explícitamente (español para todos los `es_*` instalados, inglés
solo para `en_US`), detectando los idiomas instalados dinámicamente en
vez de asumir cuáles son, para no dejar ningún idioma huérfano.
"""

from odoo import api, SUPERUSER_ID


def _write_all_langs(env, langs, record, field, es_value, en_value):
    if not record:
        return
    for lang in langs:
        value = en_value if lang == 'en_US' else es_value
        record.with_context(lang=lang).write({field: value})


def _field(env, model, field_name):
    return env['ir.model.fields'].search(
        [('model', '=', model), ('name', '=', field_name)], limit=1
    )


def _selection(env, model, field_name, value_key):
    return env['ir.model.fields.selection'].search([
        ('field_id.model', '=', model),
        ('field_id.name', '=', field_name),
        ('value', '=', value_key),
    ], limit=1)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Idiomas realmente instalados en esta base (no asumir cuáles son).
    langs = env['res.lang'].search([]).mapped('code')
    if 'en_US' not in langs:
        langs = list(langs) + ['en_US']

    def w(record, field, es_value, en_value):
        _write_all_langs(env, langs, record, field, es_value, en_value)

    # --- Nombre del módulo / app, categoría, grupo de seguridad ---
    w(env.ref('base.module_osp_management', raise_if_not_found=False), 'shortdesc',
      'PAO Administración de OSP', 'OSP Management')
    w(env.ref('osp_management.module_category_osp', raise_if_not_found=False), 'name',
      'Administración de OSP', 'OSP Management')
    w(env.ref('osp_management.module_category_osp', raise_if_not_found=False), 'description',
      'Gestión de accesos para los formularios OSP.', 'Access management for the OSP forms.')
    w(env.ref('osp_management.group_osp_administrator', raise_if_not_found=False), 'name',
      'Administrador de OSP', 'OSP Administrator')

    # --- Menús ---
    w(env.ref('osp_management.menu_osp_root', raise_if_not_found=False), 'name',
      'Administración de OSP', 'OSP Management')
    w(env.ref('osp_management.menu_osp_requests', raise_if_not_found=False), 'name',
      'Planes de manejo orgánico', 'Organic System Plans')
    w(env.ref('osp_management.menu_osp_configuration', raise_if_not_found=False), 'name',
      'Configuración', 'Configuration')
    w(env.ref('osp_management.menu_osp_service', raise_if_not_found=False), 'name',
      'Catálogo de Servicios', 'Services Catalog')
    w(env.ref('osp_management.menu_osp_form_template', raise_if_not_found=False), 'name',
      'Catálogo de Formularios (OSP)', 'OSP Form Templates Catalog')

    # --- Acciones ---
    w(env.ref('osp_management.action_osp_request', raise_if_not_found=False), 'name',
      'Planes de manejo orgánico', 'Organic System Plans')
    w(env.ref('osp_management.action_osp_service', raise_if_not_found=False), 'name',
      'Catálogo de Servicios', 'Services Catalog')
    w(env.ref('osp_management.action_osp_form_template', raise_if_not_found=False), 'name',
      'Catálogo de Formularios (OSP)', 'OSP Form Templates Catalog')
    w(env.ref('osp_management.action_osp_request', raise_if_not_found=False), 'help',
      '<p class="o_view_nocontent_smiling_face">\n    No hay planes de manejo orgánico enviados.\n</p>',
      '<p class="o_view_nocontent_smiling_face">\n    No submitted Organic System Plans yet.\n</p>')

    # --- Etiquetas de campo: osp.request ---
    field_labels_request = {
        'active': ('Activo', 'Active'),
        'name': ('Referencia', 'Reference'),
        'service_id': ('Servicio requerido', 'Required Service'),
        'form_template_id': ('Tipo (Formulario)', 'Type (Form)'),
        'form_version': ('Versión', 'Version'),
        'partner_id': ('Cliente', 'Customer'),
        'organization_name': ('Organización', 'Organization'),
        'dba_name': ('Sitio', 'DBA name'),
        'street': ('Dirección', 'Address'),
        'city': ('Ciudad', 'City'),
        'state_id': ('Estado', 'State'),
        'zip_code': ('Código Postal', 'Zip Code'),
        'country_id': ('País', 'Country'),
        'review_status': ('Estatus de revisión', 'Review Status'),
        'form_data': ('Respuestas del Formulario', 'Form Responses'),
        'notes': ('Notas Internas', 'Internal Notes'),
        'attachment_count': ('Archivos Adjuntos', 'Attachments'),
    }
    for fname, (es_value, en_value) in field_labels_request.items():
        w(_field(env, 'osp.request', fname), 'field_description', es_value, en_value)

    # --- Etiquetas de campo: osp.service / osp.form.template ---
    w(_field(env, 'osp.service', 'name'), 'field_description', 'Servicio', 'Service')
    w(_field(env, 'osp.form.template', 'service_id'), 'field_description', 'Servicio', 'Service')
    w(_field(env, 'osp.form.template', 'name'), 'field_description', 'Nombre del Formulario OSP', 'OSP Form Name')
    w(_field(env, 'osp.form.template', 'version'), 'field_description', 'Versión', 'Version')
    w(_field(env, 'osp.form.template', 'technical_code'), 'field_description',
      'Código Técnico (Plantilla Web)', 'Technical Code (Web Template)')

    # --- Opciones (Selection) ---
    w(_selection(env, 'osp.request', 'review_status', 'pending'), 'name', 'Pendiente', 'Pending')
    w(_selection(env, 'osp.request', 'review_status', 'done'), 'name', 'Completo (Hecho)', 'Complete (Done)')
    w(_selection(env, 'osp.request', 'state', 'draft'), 'name', 'Borrador (En Portal)', 'Draft (In Portal)')
    w(_selection(env, 'osp.request', 'state', 'submitted'), 'name', 'Enviado', 'Submitted')

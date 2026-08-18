# -*- coding: utf-8 -*-
"""
Migración de datos (17/ago) — intento #2 para el backend en inglés.

El intento anterior (17.0.1.0.6, `_update_translations(overwrite=True)`)
no funcionó: los registros "model:X,Y" (menús, acciones, nombre de módulo,
nombre de grupo, y sobre todo las etiquetas de campo — la fuente de casi
todas las columnas de lista sin `string=` explícito en la vista) seguían
en español pese al overwrite.

En vez de seguir dependiendo de que el importador de .po resuelva
correctamente esos registros, este script escribe la traducción
DIRECTO en cada registro vía el ORM, usando `with_context(lang='en_US')`
— exactamente el mismo mecanismo que usa la UI de Odoo cuando un humano
traduce un campo a mano con el ícono de "globo". Es la ruta más confiable
posible: no depende de xmlids auto-generados para ir.model.fields (que no
se pudieron verificar contra una instancia real) porque para las
etiquetas de campo se busca el registro de ir.model.fields por
(model, name) en vez de por external id.
"""

from odoo import api, SUPERUSER_ID

EN = 'en_US'


def _set_field_label(env, model, field_name, value):
    field = env['ir.model.fields'].search(
        [('model', '=', model), ('name', '=', field_name)], limit=1
    )
    if field:
        field.with_context(lang=EN).write({'field_description': value})


def _set_selection_label(env, model, field_name, value_key, value):
    selection = env['ir.model.fields.selection'].search([
        ('field_id.model', '=', model),
        ('field_id.name', '=', field_name),
        ('value', '=', value_key),
    ], limit=1)
    if selection:
        selection.with_context(lang=EN).write({'name': value})


def _set_by_xmlid(env, xmlid, field, value):
    record = env.ref(xmlid, raise_if_not_found=False)
    if record:
        record.with_context(lang=EN).write({field: value})


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # --- Nombre del módulo / app, categoría, grupo de seguridad ---
    _set_by_xmlid(env, 'base.module_osp_management', 'shortdesc', 'OSP Management')
    _set_by_xmlid(env, 'osp_management.module_category_osp', 'name', 'OSP Management')
    _set_by_xmlid(env, 'osp_management.module_category_osp', 'description', 'Access management for the OSP forms.')
    _set_by_xmlid(env, 'osp_management.group_osp_administrator', 'name', 'OSP Administrator')

    # --- Menús ---
    _set_by_xmlid(env, 'osp_management.menu_osp_root', 'name', 'OSP Management')
    _set_by_xmlid(env, 'osp_management.menu_osp_requests', 'name', 'Organic System Plans')
    _set_by_xmlid(env, 'osp_management.menu_osp_configuration', 'name', 'Configuration')
    _set_by_xmlid(env, 'osp_management.menu_osp_service', 'name', 'Services Catalog')
    _set_by_xmlid(env, 'osp_management.menu_osp_form_template', 'name', 'OSP Form Templates Catalog')

    # --- Acciones ---
    _set_by_xmlid(env, 'osp_management.action_osp_request', 'name', 'Organic System Plans')
    _set_by_xmlid(env, 'osp_management.action_osp_service', 'name', 'Services Catalog')
    _set_by_xmlid(env, 'osp_management.action_osp_form_template', 'name', 'OSP Form Templates Catalog')
    _set_by_xmlid(
        env, 'osp_management.action_osp_request', 'help',
        '<p class="o_view_nocontent_smiling_face">\n    No submitted Organic System Plans yet.\n</p>',
    )

    # --- Etiquetas de campo: osp.request ---
    field_labels_request = {
        'active': 'Active',
        'name': 'Reference',
        'service_id': 'Required Service',
        'form_template_id': 'Type (Form)',
        'form_version': 'Version',
        'partner_id': 'Customer',
        'organization_name': 'Organization',
        'dba_name': 'DBA name',
        'street': 'Address',
        'city': 'City',
        'state_id': 'State',
        'zip_code': 'Zip Code',
        'country_id': 'Country',
        'review_status': 'Review Status',
        'form_data': 'Form Responses',
        'notes': 'Internal Notes',
        'attachment_count': 'Attachments',
    }
    for fname, value in field_labels_request.items():
        _set_field_label(env, 'osp.request', fname, value)

    # --- Etiquetas de campo: osp.service / osp.form.template ---
    _set_field_label(env, 'osp.service', 'name', 'Service')
    _set_field_label(env, 'osp.form.template', 'service_id', 'Service')
    _set_field_label(env, 'osp.form.template', 'name', 'OSP Form Name')
    _set_field_label(env, 'osp.form.template', 'version', 'Version')
    _set_field_label(env, 'osp.form.template', 'technical_code', 'Technical Code (Web Template)')

    # --- Opciones (Selection) ---
    _set_selection_label(env, 'osp.request', 'review_status', 'pending', 'Pending')
    _set_selection_label(env, 'osp.request', 'review_status', 'done', 'Complete (Done)')
    _set_selection_label(env, 'osp.request', 'state', 'draft', 'Draft (In Portal)')
    _set_selection_label(env, 'osp.request', 'state', 'submitted', 'Submitted')

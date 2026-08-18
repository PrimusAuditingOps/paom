# -*- coding: utf-8 -*-
"""
Migración de datos (18/ago): el backend pasa a ser SIEMPRE en inglés, sin
importar el idioma del usuario (decisión del usuario — antes era bilingüe
en_US/es_MX).

Ya se reescribió el texto fuente (Python/XML) de español a inglés en esta
misma versión. Eso alcanza por sí solo para los términos `model_terms`
(contenido dentro del arch de una `ir.ui.view` — se resincroniza solo en
cada `-u`, como ya vimos). Pero los campos `model:X,Y` planos —nombre del
módulo, categoría, grupo, menús, acciones, y sobre todo las etiquetas de
campo (`ir.model.fields.field_description`)— ya tenían una traducción en
español "pegada" por idioma desde `migrations/17.0.1.0.8` (cuando el
objetivo era mostrar español a usuarios con ese idioma). Esas traducciones
por idioma NO se limpian solas cuando cambia el texto fuente — hay que
sobreescribirlas explícitamente. Este script escribe el MISMO texto en
inglés en TODOS los idiomas instalados, así el resultado es uniforme sin
importar qué idioma tenga seleccionado el usuario.

Reutiliza el mismo patrón ya probado en 17.0.1.0.7/17.0.1.0.8 (escritura
directa por ORM con `with_context(lang=...)`, sin depender del
importador de `.po`).
"""

from odoo import api, SUPERUSER_ID


def _write_all_langs(env, langs, record, field, value):
    if not record:
        return
    for lang in langs:
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

    langs = env['res.lang'].search([]).mapped('code')
    if not langs:
        return

    def w(record, field, value):
        _write_all_langs(env, langs, record, field, value)

    # --- Nombre del módulo / app, categoría, grupo de seguridad ---
    w(env.ref('base.module_osp_management', raise_if_not_found=False), 'shortdesc', 'OSP Management')
    w(env.ref('osp_management.module_category_osp', raise_if_not_found=False), 'name', 'OSP Management')
    w(env.ref('osp_management.module_category_osp', raise_if_not_found=False), 'description', 'Access management for the OSP forms.')
    w(env.ref('osp_management.group_osp_administrator', raise_if_not_found=False), 'name', 'OSP Administrator')

    # --- Menús ---
    w(env.ref('osp_management.menu_osp_root', raise_if_not_found=False), 'name', 'OSP Management')
    w(env.ref('osp_management.menu_osp_requests', raise_if_not_found=False), 'name', 'Organic System Plans')
    w(env.ref('osp_management.menu_osp_configuration', raise_if_not_found=False), 'name', 'Configuration')
    w(env.ref('osp_management.menu_osp_service', raise_if_not_found=False), 'name', 'Services Catalog')
    w(env.ref('osp_management.menu_osp_form_template', raise_if_not_found=False), 'name', 'OSP Form Templates Catalog')

    # --- Acciones ---
    w(env.ref('osp_management.action_osp_request', raise_if_not_found=False), 'name', 'Organic System Plans')
    w(env.ref('osp_management.action_osp_service', raise_if_not_found=False), 'name', 'Services Catalog')
    w(env.ref('osp_management.action_osp_form_template', raise_if_not_found=False), 'name', 'OSP Form Templates Catalog')
    w(env.ref('osp_management.action_osp_request', raise_if_not_found=False), 'help',
      '<p class="o_view_nocontent_smiling_face">\n    No submitted Organic System Plans yet.\n</p>')

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
        w(_field(env, 'osp.request', fname), 'field_description', value)

    # --- Etiquetas de campo: osp.service / osp.form.template ---
    w(_field(env, 'osp.service', 'name'), 'field_description', 'Service')
    w(_field(env, 'osp.form.template', 'service_id'), 'field_description', 'Service')
    w(_field(env, 'osp.form.template', 'name'), 'field_description', 'OSP Form Name')
    w(_field(env, 'osp.form.template', 'version'), 'field_description', 'Version')
    w(_field(env, 'osp.form.template', 'technical_code'), 'field_description', 'Technical Code (Web Template)')

    # --- Opciones (Selection) ---
    w(_selection(env, 'osp.request', 'review_status', 'pending'), 'name', 'Pending')
    w(_selection(env, 'osp.request', 'review_status', 'done'), 'name', 'Complete (Done)')
    w(_selection(env, 'osp.request', 'state', 'draft'), 'name', 'Draft (In Portal)')
    w(_selection(env, 'osp.request', 'state', 'submitted'), 'name', 'Submitted')

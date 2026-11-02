# -*- coding: utf-8 -*-
from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    # Perfil de portal restringido a OSP. Ver views/osp_portal_templates.xml
    # (portal_my_home_osp_raw) para el ocultamiento genérico del resto de
    # secciones de /my — este campo es solo la bandera, la lógica de
    # ocultamiento vive del lado de la plantilla. NO es una restricción de
    # seguridad (no cambia permisos reales, solo navegación/visibilidad) —
    # decisión confirmada con el usuario, ver CONTEXT.md.
    osp_portal_only = fields.Boolean(
        string='Limited to Organic System Plans',
        help="If enabled, this portal user's homepage (/my) will only show "
             "the 'Organic System Plans' section — every other section "
             "(Orders, Invoices, custom portal apps, etc.) stays hidden, "
             "regardless of whether the module that added it is native to "
             "Odoo or a custom one. This only hides navigation; it does not "
             "remove the user's underlying access to those records."
    )

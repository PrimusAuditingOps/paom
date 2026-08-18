from odoo import models, fields

# ==========================================
# CATÁLOGO DE SERVICIOS
# ==========================================
class OSPService(models.Model):
    _name = 'osp.service'
    _description = 'Organic Services Catalog'

    name = fields.Char(string='Service', required=True)
    active = fields.Boolean(default=True)

# ==========================================
# CATÁLOGO DE FORMULARIOS (PLANTILLAS)
# ==========================================
class OSPFormTemplate(models.Model):
    _name = 'osp.form.template'
    _description = 'Form Templates Catalog'

    service_id = fields.Many2one('osp.service', string='Service', required=True)
    name = fields.Char(string='OSP Form Name', required=True)
    version = fields.Char(string='Version', required=True, default='1.0')
    technical_code = fields.Char(
        string='Technical Code (Web Template)',
        required=True,
        help="Unique code (e.g. form_crop, form_handler) that tells the portal which web page to load."
    )
    active = fields.Boolean(default=True)

from odoo import models, fields

# ==========================================
# CATÁLOGO DE SERVICIOS
# ==========================================
class OSPService(models.Model):
    _name = 'osp.service'
    _description = 'Catálogo de Servicios Orgánicos'
    
    name = fields.Char(string='Servicio', required=True)
    active = fields.Boolean(default=True)

# ==========================================
# CATÁLOGO DE FORMULARIOS (PLANTILLAS)
# ==========================================
class OSPFormTemplate(models.Model):
    _name = 'osp.form.template'
    _description = 'Catálogo de Formularios'
    
    service_id = fields.Many2one('osp.service', string='Servicio', required=True)
    name = fields.Char(string='Nombre del Formulario OSP', required=True)
    version = fields.Char(string='Versión', required=True, default='1.0')
    technical_code = fields.Char(
        string='Código Técnico (Plantilla Web)', 
        required=True,
        help="Código único (ej. form_crop, form_handler) que le dice al portal qué página web cargar."
    )
    active = fields.Boolean(default=True)
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoAzzAuditTemplate(models.Model):
    _name = "pao.azz.audit.template"
    _description = "PAO Azz Audit Template"

    
    name = fields.Char(
        required=True,
        string= "Name",
        translate=True,
    )
    active = fields.Boolean(string="Active", default=True)
    template_version_ids = fields.One2many(
        comodel_name='pao.azz.template.version',
        inverse_name='pao_audit_template_id',
        string='Template Version',
    )
    
    product_ids = fields.One2many(
        comodel_name='product.product',
        inverse_name='pao_audit_template_id',
        string='Products',
    )


    

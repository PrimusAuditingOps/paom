from datetime import datetime, timedelta
from odoo import fields, models, api
import dateutil.parser



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    pao_platform_audit_ids = fields.Many2many(
        string='Audit ID', 
        comodel_name='pao.azz.platform.audits'
    
    )
from datetime import datetime, timedelta
from odoo import fields, models, api
import dateutil.parser



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    pao_platform_audit_ids = fields.One2many(
        'pao.azz.platform.audits',
        'sale_order_line_id',
        string='Audit ID'
    )

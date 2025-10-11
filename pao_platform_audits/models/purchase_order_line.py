from datetime import datetime, timedelta
from odoo import fields, models, api
import dateutil.parser



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    pao_platform_audit_ids = fields.One2many(
        'pao.azz.platform.audits',
        'purchase_order_line_id',
        string='Platform Audits'
    )

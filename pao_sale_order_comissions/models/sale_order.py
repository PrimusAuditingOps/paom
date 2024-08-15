from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    
    commission_ids = fields.One2many(
        'pao.sale.order.commissions',
        string='Sale Order Commissions',
        inverse_name='sale_order_id'
    )
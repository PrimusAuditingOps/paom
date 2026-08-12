from datetime import datetime, timedelta
from odoo import fields, models, api, _



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    pao_ena_ids = fields.One2many(
        'ena.solicitud', 
        inverse_name='purchase_order_id',                                
        string='Auditorias no anunciadas'
    )
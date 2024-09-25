from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartnerInherit(models.Model):

    _inherit="res.partner"
    
    pao_agreements_ids = fields.One2many(
        comodel_name='pao.sign.sa.agreements.sent',
        inverse_name='sale_order_id.partner_id',
        string='Agrements',
    )
    
    
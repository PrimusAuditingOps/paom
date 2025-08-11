from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class SaleOrder(models.Model):
    _inherit='sale.order'

    
    pao_promotor_id = fields.Many2one(
        comodel_name='comisionpromotores.promotor',
        string='Consultant',
        ondelete='set null',
        tracking=True,
    )

    @api.onchange("partner_id")
    def _change_partner_pao_consultant(self):
        for rec in self:
            if rec.partner_id.promotor_id:
                rec.pao_promotor_id = rec.partner_id.promotor_id.id
            else:
                 rec.pao_promotor_id = None
        
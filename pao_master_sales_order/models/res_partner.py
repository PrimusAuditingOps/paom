from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class ResPartner(models.Model):

    _inherit='res.partner'
    

    pao_sc_price_list = fields.Many2one(
        string="Shared Cost Price List",
        comodel_name='product.pricelist',
        ondelete='set null',
        index=True,
    )

    pao_master_order_country_code = fields.Text(
        compute='_pmso_get_country_code', 
        string='Country Code For Master Order',
        readonly=True,
    )

    @api.depends('company_id')
    def _pmso_get_country_code(self):
        for rec in self:
            rec.pao_master_order_country_code = rec.company_id.country_code if rec.company_id.country_code else ""


    
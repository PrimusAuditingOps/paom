# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    pao_quote_rate_id = fields.Many2one(
        comodel_name='pao.quote.rate',
        string='Rate Sheet',
        help="Chile quotation format: rate sheet loaded in the quotations using this template.",
    )

# -*- coding: utf-8 -*-
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pao_quote_combine = fields.Boolean(
        string='Combine',
        help="Chile quotation format: when generating the format, print this line in the same row as the "
             "previous line, with the summed price (e.g. 'GLOBALG.A.P. + Nurture Add-On').",
    )

    def _pao_quote_currency(self):
        """Currency printed for this line: the product base currency (see pao_chile_invoices)."""
        self.ensure_one()
        return self.product_id.base_currency_id or self.order_id.currency_id

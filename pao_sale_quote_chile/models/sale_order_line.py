# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    pao_quote_combine = fields.Boolean(
        string='Combine',
        compute='_compute_pao_quote_fields',
        store=True,
        readonly=False,
        help="Chile quotation: print this line in the same row as the previous line, with the summed price.",
    )
    pao_quote_table_id = fields.Many2one(
        comodel_name='pao.quote.table',
        string='Table Format',
        compute='_compute_pao_quote_fields',
        store=True,
        readonly=False,
        help="Chile quotation: format of the table when this line is its first product line.",
    )

    @api.depends('product_id')
    def _compute_pao_quote_fields(self):
        for line in self:
            template = line.product_id.product_tmpl_id
            line.pao_quote_combine = template.pao_quote_combine
            line.pao_quote_table_id = template.pao_quote_table_id

    def _get_sale_order_line_multiline_description_sale(self):
        quote_name = self.product_id.pao_quote_name
        if quote_name and self.order_id.pao_use_chile_format:
            return quote_name + self._get_sale_order_line_multiline_description_variants()
        return super()._get_sale_order_line_multiline_description_sale()

    def _pao_quote_currency(self):
        """Currency printed for this line: the product base currency (see pao_chile_invoices)."""
        self.ensure_one()
        return self.product_id.base_currency_id or self.order_id.currency_id

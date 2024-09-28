from datetime import datetime, timedelta
from odoo import fields, models, api
from odoo.tools.float_utils import  float_round
import dateutil.parser
from logging import getLogger


_logger = getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
   
    pao_price_in_house_auditor = fields.Float(string="Price For In House Auditor",compute="_get_price_in_house_auditor", store=True)

    @api.depends('product_id')
    def _get_price_in_house_auditor(self):
        for rec in self:
            rec.pao_price_in_house_auditor = 0.00
            if not rec.product_id:
                rec.pao_price_in_house_auditor = 0.00
                return
            else:
                params = rec._get_select_sellers_params()
                seller = rec.product_id._select_seller(
                    partner_id=rec.partner_id,
                    quantity=rec.product_qty,
                    date=rec.order_id.date_order and rec.order_id.date_order.date() or fields.Date.context_today(rec),
                    uom_id=rec.product_uom,
                    params=params)
                if seller:
                    price_unit = rec.env['account.tax']._fix_tax_included_price_company(seller.pao_price_in_house_auditor, rec.product_id.supplier_taxes_id, rec.taxes_id, rec.company_id) if seller else 0.0
                    price_unit = seller.currency_id._convert(price_unit, rec.currency_id, rec.company_id, rec.date_order or fields.Date.context_today(rec), False)
                    price_unit = float_round(price_unit, precision_digits=max(rec.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
                    rec.pao_price_in_house_auditor = seller.product_uom._compute_price(price_unit, rec.product_uom)

   
from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare, float_round, format_date, groupby

class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    
    def _get_sale_order_line_multiline_description_sale(self):
            """ Compute a default multiline description for this sales order line.

            In most cases the product description is enough but sometimes we need to append information that only
            exists on the sale order line itself.
            e.g:
            - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
            - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
            the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
            """
            self.ensure_one()
            if self.product_id.product_tmpl_id.company_id.country_code == 'US':
                return self.product_id.product_tmpl_id.name + self._get_sale_order_line_multiline_description_variants()
            else:
                return self.product_id.get_product_multiline_description_sale() + self._get_sale_order_line_multiline_description_variants()
from odoo import fields, models, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)

class PurchaseOrderLineInherit(models.Model):
    _inherit= 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id_suppler_taxes(self):
        if not self.product_id:
            return
        if self.order_id.partner_id.st_supplier_taxes_id:
            self.taxes_id = self.order_id.partner_id.st_supplier_taxes_id.taxes_id
        
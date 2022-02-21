from odoo import fields, models, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)

class PurchaseOrderInherit(models.Model):
    _inherit= 'purchase.order'

    @api.onchange('order_line')
    def _change_supplier_taxes(self):
        for recpurchase in self:
            if recpurchase.partner_id.st_supplier_taxes_id:
                for rec in recpurchase.order_line:
                    if rec.product_id:
                        rec.write({"taxes_id": recpurchase.partner_id.st_supplier_taxes_id.taxes_id})
                
    @api.onchange('partner_id')
    def _change_partner_id_supplier_taxes(self):
        for recpurchase in self:
            if recpurchase.partner_id and recpurchase.partner_id.st_supplier_taxes_id:
                for rec in recpurchase.order_line:
                    if rec.product_id:
                       rec.write({"taxes_id": recpurchase.partner_id.st_supplier_taxes_id.taxes_id})
            else:
                recpurchase.order_line._compute_tax_id()   

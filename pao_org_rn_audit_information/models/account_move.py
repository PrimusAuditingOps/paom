from odoo import api, models, fields
from odoo.tools.translate import _


class ResPartner(models.Model):
    _inherit = 'account.move'

    audit_date = fields.Date(string="Audit Date", compute="_compute_audit_information_fields", store=True)
    organization = fields.Char(string="Organization", compute="_compute_audit_information_fields", store=True)
    registry_number = fields.Char(string="Registry Number", compute="_compute_audit_information_fields", store=True)
                
    @api.depends('line_ids.sale_line_ids.order_id')
    def _compute_audit_information_fields(self):
        for move in self:
            # Fetch the related sale order if available
            sale_orders = move.line_ids.mapped('sale_line_ids.order_id')
            if sale_orders:
                # Use the first sale order found, or adjust if you expect multiple orders
                sale_order = sale_orders[0]
                move.audit_date = sale_order.audit_date
                move.organization = sale_order.organization
                move.registry_number = sale_order.registry_number
            else:
                move.audit_date = False
                move.organization = False
                move.registry_number = False
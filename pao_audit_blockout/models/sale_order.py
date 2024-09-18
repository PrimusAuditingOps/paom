from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.constrains('order_line', 'audit_type')
    def _check_service_dates_for_unannounced_audit(self):
        for order in self:
            if order.audit_type == 'unannounced':
                for line in order.order_line:
                    if line.service_start_date and line.service_end_date:
                        blockout_dates = order.partner_id.blockout_dates_ids
                        for blockout in blockout_dates:
                            if line.service_start_date <= blockout.end_date and line.end_start_date >= blockout.start_date:
                                raise UserError(_("You cannot schedule unannounced audits within a range of blockout dates set by the customer. (Blockout Range: %(start_date)s - %(end_date)s)") % {'start_date': blockout.start_date, 'end_date': blockout.end_date})
                            
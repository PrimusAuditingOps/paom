from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger
from odoo.exceptions import ValidationError

_logger = getLogger(__name__)
class PurchaseOrderInherit(models.Model):

    _inherit='purchase.order'

    @api.constrains('order_line')
    def _validate_Approved_product_auditor(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.ado_is_auditor:
                for line in rec.order_line:
                    msg = _("The auditor is not approved to perform")
                    if line.product_id not in rec.partner_id.aa_product_ids:
                        raise ValidationError(_('{0} "{1}".'.format(msg,line.product_id.name)))



        
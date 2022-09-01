from odoo import fields, models, api, _
from logging import getLogger
from math import acos, cos, sin, radians
import datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


_logger = getLogger(__name__)

class PurchaseOrderInherit(models.Model):
    _inherit='purchase.order'

    assigned_auditor_id = fields.Integer(
        string = "ID Reference",
        default = 0,
    ) 
    assigned_auditor_position = fields.Integer(
        string = "Pos Reference",
        default = 0,
    ) 
    assigned_auditor_qualification = fields.Float(
        default = 0.00,
        string = "Qual Reference",
    ) 
    @api.onchange('assigned_auditor_id')
    def onchange_assigned_auditor_id(self):
        for rec in self:
            if rec.assigned_auditor_id and rec.assigned_auditor_id > 0:
                rec.partner_id = rec.assigned_auditor_id

    @api.constrains('partner_id','sale_order_id','order_line')
    def _validate_blocked_auditor(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.ado_is_auditor:
                if rec.sale_order_id:
                    customer_list = [r.id for r in rec.partner_id.paa_blocked_company_ids]
                    if rec.sale_order_id.partner_id.id in customer_list:
                        raise ValidationError(_("The auditor is blocked for the sales order customer."))
                organization_list = [r.id for r in rec.partner_id.paa_blocked_organizations_ids]
                for line in rec.order_line:
                    if line.organization_id.id in organization_list:
                        msg = _("The auditor is blocked for")
                        raise ValidationError(_('{0} "{1}".'.format(msg,line.organization_id.name)))


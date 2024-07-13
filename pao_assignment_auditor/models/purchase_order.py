from odoo import fields, models, api, _
from math import acos, cos, sin, radians
import datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from logging import getLogger

_logger = getLogger(__name__)



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    assigned_auditor_id = fields.Integer(string="ID Reference", default=0) 
    assigned_auditor_position = fields.Integer(string="Pos Reference", default=0) 
    assigned_auditor_qualification = fields.Float(default=0.00,
                                                  string="Qual Reference") 
    paa_is_auditor = fields.Boolean(related='partner_id.ado_is_auditor', string="Is Auditor")
    language_ids = fields.Many2many('res.lang', string="Audit language requested")
    pao_auditor_top_ids = fields.One2many(
        comodel_name='paoassignmentauditor.auditor.qualification.top',
        inverse_name='order_id',
        string='Top 10 Auditor qualification',
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

    @api.model_create_multi
    def create(self, values):
        purchase_order = super(PurchaseOrder, self).create(values)
        
        domain = [("ref_user_id","=", self.env.user.id)]
        rec = self.env["paoassignmentauditor.auditor.qualification"].search(domain, limit=10, order='qualification desc')
        if rec:
            ranking_list = []
            ranking_list = [{"order_id": purchase_order.id, "position": len(ranking_list) + 1, "auditor_id": r.auditor_id.id, "qualification": r.qualification} for r in rec]
            self.env["paoassignmentauditor.auditor.qualification.top"].create(ranking_list)
            self.env['paoassignmentauditor.auditor.qualification'].sudo().search(domain).unlink()

        return purchase_order
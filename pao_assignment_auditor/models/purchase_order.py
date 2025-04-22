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
    language_ids = fields.Many2many('res.lang', string="Audit Language Requested")
    pao_auditor_top_ids = fields.One2many(
        comodel_name='paoassignmentauditor.auditor.qualification.top',
        inverse_name='order_id',
        string='Top 10 Auditor Qualification',
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
    
    @api.onchange('partner_id', 'audit_state_id', 'order_line')
    def _onchange_partner_id_warning_logistics(self):
        if not self.partner_id or not self.audit_state_id:
            return
        
        domain = [
            ('order_id.partner_id', '=', self.partner_id.id),
            ('order_id.state', 'not in', ['cancel']),
            ('order_id.audit_state_id', '!=', self.audit_state_id.id),
            ('order_id.audit_state_id', '!=', False),
            ('service_start_date', '!=', False),
        ]

        if self.id:
            domain.append(('order_id.id', '!=', self.id))

        nearby_po_lines = self.env['purchase.order.line'].search(domain)

        for line in nearby_po_lines:
            start_date = line.service_start_date
            end_date = line.service_end_date or line.service_start_date
            current_dates = [l.service_start_date for l in self.order_line if l.service_start_date]

            for cur_date in current_dates:
                if abs((start_date - cur_date).days) <= 1 or abs((end_date - cur_date).days) <= 1:
                    return {
                        'warning': {
                            'title': _('Logistics Warning'),
                            'message': _(
                                "Please review logistics: The auditor is already assigned to an audit (%s) in another state "
                                "(%s) on a nearby date (%s)."
                            ) % (line.order_id.name, line.order_id.audit_state_id.name, start_date.strftime('%Y-%m-%d')),
                        }
                    }
    

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    def write(self, vals):
        for record in self:
            if any(field in vals for field in ['service_start_date', 'service_end_date']):
                self._send_auditor_notification()
        return super(PurchaseOrderLine, self).write(vals)
    
    def _send_auditor_notification(self):
        for rec in self.mapped('order_id'):
            if rec.state != 'draft':
                line_details = ''
                for line in rec.order_line:
                    line_details = "*{}, {}, {}, {} - {}<br>".format(
                        line.name,
                        line.organization_id.name,
                        line.registrynumber_id.name,
                        line.service_start_date.strftime("%Y-%m-%d"),
                        line.service_end_date.strftime("%Y-%m-%d")
                    )
                message = _("The service dates for the audit with reference %s have been updated: <br>%s") % (rec.partner_ref or rec.name, line_details)
                rec.message_post(body=message, body_is_html=True, partner_ids=[rec.partner_id.id])
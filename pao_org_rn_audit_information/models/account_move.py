from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)

class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    audit_start_date = fields.Date(string="Audit Start Date", compute="_compute_audit_information_fields", store=True)
    audit_end_date = fields.Date(string="Audit End Date", compute="_compute_audit_information_fields", store=True)
    organization = fields.Char(string="Organization", compute="_compute_audit_information_fields", store=True)
    registry_number = fields.Char(string="Registry Number", compute="_compute_audit_information_fields", store=True)

    @api.depends('invoice_origin')
    def _compute_audit_information_fields(self):
        for move in self:
            sale_order = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
            if sale_order:
                move.audit_start_date = sale_order.service_start_date
                move.audit_end_date = sale_order.service_end_date
                move.organization = sale_order.organization_id.name
                move.registry_number = sale_order.registrynumber_id.name
            else:
                move.audit_start_date = False
                move.audit_end_date = False
                move.organization = False
                move.registry_number = False
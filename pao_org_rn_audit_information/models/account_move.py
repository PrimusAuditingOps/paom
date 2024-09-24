from odoo import api, models, fields
from odoo.tools.translate import _


class ResPartner(models.Model):
    _inherit = 'account.move'

    audit_date = fields.Date(string="Audit Date", compute="_compute_audit_information_fields", store=True)
    organization = fields.Char(string="Organization", compute="_compute_audit_information_fields", store=True)
    registry_number = fields.Char(string="Registry Number", compute="_compute_audit_information_fields", store=True)

    @api.depends('invoice_line_ids')
    def _compute_audit_information_fields(self):
        for record in self:
            # Assuming 'invoice_origin' links to the sale order name
            sale_order = self.env['sale.order'].search([('invoice_ids', 'in', record.id)], limit=1)
            if sale_order:
                record.audit_date = sale_order.serive_start_date
                record.organization = sale_order.organization_id.name
                record.registry_number = sale_order.registrynumber_id.name
            else:
                record.audit_date = False
                record.organization = False
                record.registry_number = False
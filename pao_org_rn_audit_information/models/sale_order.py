from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class SaleOrder(models.Model):
    _inherit='sale.order'

    organization_id = fields.Many2one(
        comodel_name='servicereferralagreement.organization',
        string='Organization',
        ondelete='restrict'
    )
    registrynumber_id = fields.Many2one(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registration number',
        ondelete='restrict',
    )
    service_start_date = fields.Date(
        string="Service start date"
    )
    service_end_date = fields.Date(
        string="Service end date"
    )

    audit_type = fields.Selection(
        selection=[
            ('announced', "Announced"),
            ('unannounced', "Unannounced"),
            ('pre-assessment', "Pre-Assessment"),
        ],
        default='announced',
        string="Audit type", 
        copy=False,
    )

    @api.onchange('service_start_date')
    def _change_so_start_date(self):
        for rec in self:
            for l in rec.order_line:
                l.write({"service_start_date": rec.service_start_date})

    @api.onchange('service_end_date')
    def _change_so_end_date(self):
        for rec in self:
            for l in rec.order_line:
                l.write({"service_end_date": rec.service_end_date})

    @api.onchange('organization_id')
    def _change_so_organization_id(self):
        for rec in self:
            for l in rec.order_line:
                l.write({"organization_id": rec.organization_id.id})

    @api.onchange('registrynumber_id')
    def _change_so_registrynumber_id(self):
        for rec in self:
            for l in rec.order_line:
                l.write({"registrynumber_id": rec.registrynumber_id.id})

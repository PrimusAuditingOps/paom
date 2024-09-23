from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class SaleOrder(models.Model):

    _inherit='sale.order'
    
    
    pao_agreements_ids = fields.One2many(
        comodel_name='pao.sign.sa.agreements.sent',
        inverse_name='sale_order_id',
        string='Agrements',
    )

    pao_agrements_count = fields.Integer(
        compute='_get_agreements'
    )

    pao_registration_numbers_ids = fields.Many2many(
        comodel_name='servicereferralagreement.registrynumber',
        compute='_get_registration_numbers', 
        string='Registration numbers',
        readonly=True,
    )   

    sa_status = fields.Selection(string="SA Status", selection=[
        ('no_sa_request', "SA Signature Not Requested"),
        ('pending_sa', "SA Signature Pending"),
        ('all_sign', "SA Fully Signed"),
            ],
        default = 'no_sa_request',
        compute='_get_sa_status'
    )           

    @api.depends('pao_agreements_ids')
    def _get_agreements(self):
        for order in self:
            order.pao_agrements_count = len(order.pao_agreements_ids)

    @api.depends('pao_agreements_ids.document_status')
    def _get_sa_status(self):
        for order in self:
            agreements = order.pao_agreements_ids
            if not agreements:
                # No agreements, so set the status to 'no_sa_request'
                order.sa_status = 'no_sa_request'
            else:
                # Ignore 'cancel' status agreements
                valid_agreements = agreements.filtered(lambda a: a.document_status != 'cancel')

                if not valid_agreements:
                    # All agreements are canceled
                    order.sa_status = 'no_sa_request'
                elif any(a.document_status in ('sent', 'partially_sign') for a in valid_agreements):
                    # At least one agreement is pending signature
                    order.sa_status = 'pending_sa'
                elif all(a.document_status == 'sign' for a in valid_agreements):
                    # All valid agreements are signed
                    order.sa_status = 'all_sign'
                else:
                    # Default to 'no_sa_request' if none of the conditions match
                    order.sa_status = 'no_sa_request'

    @api.depends('order_line')
    def _get_registration_numbers(self):
        for rec in self:
            listnumbers = []

            for line in rec.order_line:
                if line.registrynumber_id:
                    if line.registrynumber_id.id not in listnumbers:
                            listnumbers.append(line.registrynumber_id.id) 
            rec.pao_registration_numbers_ids = listnumbers
    
    def action_view_service_agreements(self):
        self.ensure_one()     
        action = {
            'res_model': 'pao.sign.sa.agreements.sent',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'name': _("Service Agreements - %s", self.name),
            'domain': [('sale_order_id', '=', self.id)],
        }
        return action
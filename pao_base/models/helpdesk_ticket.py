from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.constrains('company_id', 'partner_id')
    def _check_partner_id_has_the_same_company(self):
        for rec in self:
            return True

# -*- coding: utf-8 -*-
# © <2021> <otorresmx (otorres@proogeeks.com)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)

class AccountMoveInh(models.Model):
    _inherit = 'account.move'
    
    partner_id = fields.Many2one(comodel_name='res.partner', domain="[('company_id', '=', company_id)]")


    prm_partner_id = fields.Many2one(
        string='Customer No',
        comodel_name='res.partner',
        domain="[('company_id', '=', company_id), ('prm_customer_number', '!=', False)]",
    )

    @api.onchange('prm_partner_id')
    def change_prm_partner_id(self):
        self.partner_id = self.prm_partner_id.id
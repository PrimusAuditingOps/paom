# -*- coding: utf-8 -*-
# ©  <Omar Torres (otorres@proogeeks.com)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    _sql_constraints = [
        ('res_partner_unique_customer_num',
        'unique(prm_company_id, prm_customer_number)',
        'Customer number is already registered')]

    @api.model
    def default_get(self, fields):
        res = super(ResPartner, self).default_get(fields)
        res['prm_company_id'] = self.env.user.company_id.id
        return res

    prm_registration_number = fields.Char(string='Registration number')
    prm_type_ids = fields.One2many(
        string='Operation Types', comodel_name='prm.contact.type.line', inverse_name='partner_id')
    commodity_ids = fields.Many2many(string='Commodities', comodel_name='prm.contact.commodity')
    prm_shipper_ids = fields.Many2many(string='Shippers', comodel_name='prm.contact.shipper')
    prm_customer_number = fields.Char(string='Customer No')
    prm_company_id = fields.Many2one(string='Company', comodel_name='res.company')

    @api.model
    def name_get(self):
        if not self.env.context.get('display_prm_customer_number', False):
            return super(ResPartner, self).name_get()
        
        result = []
        
        for rec in self:
            name = rec.prm_customer_number if rec.prm_customer_number and self.env.context.get('display_prm_customer_number', False) else rec.name
            result.append((rec.id, name))
        
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not self.env.context.get('display_prm_customer_number', False):
            return super(ResPartner, self).name_search(name, args, operator, limit)

        args = args or []
        domain = args + []
        if name:
            domain += ['|', '|', ('prm_customer_number', operator, name), ('email', operator, name), ('name', operator, name)]
        
        partners = self.search(domain, limit=limit)
        return partners.name_get()

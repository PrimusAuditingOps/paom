# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo import api, models, fields
from odoo.tools.translate import _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    city_id = fields.Many2one('res.city', string='City of Address')
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id:
            self.city = self.city_id.name
            if self.city_id.zipcode:
                self.zip = self.city_id.zipcode
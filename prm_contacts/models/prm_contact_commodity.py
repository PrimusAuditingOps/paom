# -*- coding: utf-8 -*-
# © <2020> <Omar Torres (otorres@proogeeks.com)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api

class prm_contact_commodity(models.Model):
    _name = 'prm.contact.commodity'
    _description = 'PRM CONTACT COMMODITY'

    name = fields.Char(
        string='Name',
        required=True
    )

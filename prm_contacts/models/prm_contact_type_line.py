# -*- coding: utf-8 -*-
# © <2020> <Omar Torres (otorres@proogeeks.com)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api

class prm_contact_type_line(models.Model):
    _name = 'prm.contact.type.line'
    _description = 'PRM CONTACT TYPE LINE'
    _rec_name = 'type_id'

    partner_id = fields.Many2one(
        string='Contact',
        comodel_name='res.partner',
        ondelete='cascade'
    )
    type_count = fields.Integer(
        string='Number',
        default=1
    )
    type_id = fields.Many2one(
        string='Operation Type',
        comodel_name='prm.contact.type',
        ondelete='cascade'
    )


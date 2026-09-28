# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ComisionpromotoresPromotor(models.Model):
    _inherit = 'comisionpromotores.promotor'

    promotor_type = fields.Selection(
        selection=[
            ('external', 'External'),
            ('sales', 'Sales'),
            ('coordination', 'Coordination'),
        ],
        string='Promotor Type',
        required=True,
        default='external',
        help='Determine the business rule used to calculate and '
             'release commission payments:\n'
             '- External / Internal Salesperson: paid once the '
             'quote is fully invoiced and paid.\n'
             '- Coordinator: in addition to the above, it must be '
             'verified that the contracted service has been '
             'performed (related purchase order).',
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Internal User',
        help='Odoo user corresponding to this commission agent. '
             'Mandatory for Internal Salesperson and Coordinator, since '
             'previously they were identified only by a name match. '
             'It is optional for external commission agents '
             '(who do not have an Odoo user).',
    )

    commission_rate = fields.Float(
        string='Commission % (decimal)',
        digits=(5, 2),
        help='Same commission percentage as "Commission Percentage" but '
             'allowing decimals (e.g. 1.5%). Sales Commission Management '
             'uses this field instead of the integer "Commission '
             'Percentage" one to calculate the commission to pay. It '
             'defaults to the integer value but can be edited '
             'independently afterwards.',
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Vendor (Purchase Orders)',
        help='Vendor used as the supplier when generating a purchase '
             "order to pay this agent's approved commissions. Required "
             'for External commission agents before a purchase order can '
             'be generated for them.',
    )

    @api.onchange('promotor_type')
    def _onchange_promotor_type_porcentaje(self):
        for rec in self:
            if rec.promotor_type in ('external', 'sales'):
                rec.porcentaje = 5
                rec.commission_rate = 5
            elif rec.promotor_type == 'coordination':
                rec.porcentaje = 2
                rec.commission_rate = 2

    @api.onchange('porcentaje')
    def _onchange_porcentaje_commission_rate(self):
        for rec in self:
            if not rec.commission_rate:
                rec.commission_rate = rec.porcentaje

# -*- coding: utf-8 -*-
from odoo import fields, models


class PaoSaCert008Line(models.Model):
    """Quotation line copied when a Chilean GLOBALG.A.P. SA is sent, so the signed document does not change
    if the quotation or the product catalog is edited afterwards."""
    _name = 'pao.sa.cert008.line'
    _description = 'CERT-008 SA Line'
    _order = 'sequence, id'

    registration_number_to_sign_id = fields.Many2one(
        comodel_name='pao.registration.number.to.sign',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer()
    name = fields.Text(string='Description')
    line_type = fields.Selection(
        selection=[
            ('audit', 'Audit Service'),
            ('addon', 'Add-On'),
            ('fee', 'Fee'),
            ('travel', 'Travel Expense'),
        ],
        required=True,
    )
    addon_id = fields.Many2one(comodel_name='pao.sa.addon', string='Add-On', ondelete='set null')
    currency_id = fields.Many2one(comodel_name='res.currency', required=True)
    amount = fields.Monetary(currency_field='currency_id')

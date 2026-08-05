# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PaoSalesCommissionPayWizard(models.TransientModel):
    """Wizard usado por Finanzas para confirmar el pago de una o varias
    comisiones (permite selección múltiple desde la vista de lista)."""
    _name = 'pao.sales.commission.pay.wizard'
    _description = 'Confirm Commission Payment(s)'

    comision_ids = fields.Many2many(
        comodel_name='pao.sales.commission', string='Commissions Payable',
    )
    payment_date = fields.Date(
        string='Payment Date', required=True, default=fields.Date.context_today,
    )
    payment_reference = fields.Char(
        string='Payment Reference',
        help='Transfer folio, check, or internal Finance reference '
             'used to make the payment.',
    )
    notes = fields.Text(string='Notes')
    total_amount_mxn = fields.Monetary(
        string='Total Amount Payable (MXN)', compute='_compute_total_amount_mxn',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency', compute='_compute_total_amount_mxn',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'comision_ids' in fields_list and not res.get('comision_ids'):
            active_ids = self.env.context.get('active_ids') or (
                [self.env.context['active_id']]
                if self.env.context.get('active_id') else []
            )
            if active_ids:
                res['comision_ids'] = [(6, 0, active_ids)]
        return res

    @api.depends('comision_ids')
    def _compute_total_amount_mxn(self):
        mxn = self.env['res.currency'].search([('name', '=', 'MXN')], limit=1)
        for wiz in self:
            wiz.currency_id = mxn
            wiz.total_amount_mxn = sum(
                wiz.comision_ids.mapped('commission_amount_mxn')
            )

    def action_confirm_payment(self):
        self.ensure_one()
        if not self.comision_ids:
            raise UserError('No commissions have been selected.')
        no_pagables = self.comision_ids.filtered(
            lambda c: c.state != 'outstanding_payable'
        )
        if no_pagables:
            raise UserError(   
                'The following commissions are not in "To Be Paid" status and '
                'cannot be marked as paid: %s'
                % ', '.join(no_pagables.mapped('name'))
            )
        self.comision_ids.write({
            'state': 'paid',
            'payment_date': self.payment_date,
            'paid_by': self.env.uid,
            'finance_payment_reference': self.payment_reference,
            'finance_notes': self.notes,
        })
        for comision in self.comision_ids:
            comision.message_post(
                body=('Commission marked as Paid. Reference: %s'
                      % (self.payment_reference or '-'))
            )
        return {'type': 'ir.actions.act_window_close'}

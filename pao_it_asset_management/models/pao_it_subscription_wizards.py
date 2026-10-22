from odoo import models, fields, _
from odoo.exceptions import UserError


# ==========================================
# CAMBIO DE PRECIO A MITAD DE UN PERIODO
# ==========================================
# Parte el periodo en la fecha efectiva: el tramo anterior conserva el precio
# y el nuevo tramo toma el nuevo precio. Así los totales reflejan lo que
# realmente se pagó y la variación aparece en la fecha del cambio.
class PaoItSubscriptionPriceWizard(models.TransientModel):
    _name = 'pao.it.subscription.price.wizard'
    _description = 'Subscription Price Change'

    period_id = fields.Many2one('pao.it.subscription.period', string='Period', required=True)
    license_type = fields.Selection(related='period_id.license_type')
    currency_id = fields.Many2one(related='period_id.currency_id')
    effective_date = fields.Date(string='Effective Date', required=True, default=fields.Date.context_today)
    new_unit_cost = fields.Monetary(string='New Unit Cost', currency_field='currency_id')
    new_billing_amount = fields.Monetary(string='New Amount per Billing', currency_field='currency_id')

    def action_confirm(self):
        self.ensure_one()
        new_period = self.period_id._split_at(self.effective_date, self.new_unit_cost, self.new_billing_amount)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pao.it.subscription',
            'res_id': new_period.subscription_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


# ==========================================
# CANCELACIÓN DE UNA SUSCRIPCIÓN
# ==========================================
# Marca la suscripción como cancelada y cierra sus asignaciones abiertas con
# la fecha de cancelación. Los periodos se conservan (historial de gasto).
class PaoItSubscriptionCancelWizard(models.TransientModel):
    _name = 'pao.it.subscription.cancel.wizard'
    _description = 'Cancel Software Subscription'

    subscription_id = fields.Many2one('pao.it.subscription', string='Subscription', required=True)
    cancel_date = fields.Date(string='Cancellation Date', required=True, default=fields.Date.context_today)
    reason = fields.Text(string='Reason', required=True)

    def action_confirm(self):
        self.ensure_one()
        if not (self.reason or '').strip():
            raise UserError(_("Please indicate the reason for the cancellation."))
        subscription = self.subscription_id
        subscription.write({
            'cancelled': True,
            'cancel_date': self.cancel_date,
            'cancel_reason': self.reason,
        })
        for assignment in subscription.assignment_ids.filtered(lambda a: a.state == 'active'):
            assignment.date_end = max(self.cancel_date, assignment.date_start)
        return {'type': 'ir.actions.act_window_close'}

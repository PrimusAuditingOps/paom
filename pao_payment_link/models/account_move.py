from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit='account.move'

    pao_payment_link = fields.Char(string="Payment Link", compute='_pao_compute_payment_link',store=True)
    
    @api.depends("amount_residual")
    def _pao_compute_payment_link(self):
        for rec in self:
            rec.pao_payment_link = ""
            if rec.amount_residual > 0:
                payment = self.env['payment.link.wizard'].create(
                        {
                            'res_model': "account.move",
                            'res_id': self.id,
                            'amount': self.amount_residual,
                            'amount_max': self.amount_residual,
                            'currency_id': self.currency_id.id,
                            'partner_id': self.partner_id.id,

                        }
                    )
                rec.pao_payment_link = payment.link
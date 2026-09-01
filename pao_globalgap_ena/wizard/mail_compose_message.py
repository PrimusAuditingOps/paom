from odoo import models

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        res = super().action_send_mail()

        model = self.env.context.get('default_model')
        res_ids = self.env.context.get('default_res_ids')

        if model == 'ena.solicitud' and res_ids:
            records = self.env[model].browse(res_ids)

            for rec in records:
                if rec.stage not in ('programada','realizada'): 
                    rec.write({
                        'stage': "notificada"
                    })

        return res
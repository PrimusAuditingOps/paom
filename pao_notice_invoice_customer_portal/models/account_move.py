from odoo import fields, models, _

class AccountMove(models.Model):
    _inherit = "account.move"

    def action_post(self):
        res = super().action_post()

        activity_type = self.env.ref("mail.mail_activity_data_todo")

        for move in self:

            if ( move.move_type == "out_invoice" and move.partner_id.pao_upload_invoice_portal and move.country_code == "MX"):

                existing_activity = self.env["mail.activity"].search([
                    ("res_model", "=", "account.move"),
                    ("res_id", "=", move.id),
                    ("summary", "=", "Subir factura a portal"),
                ], limit=1)
                user = self.env['res.users'].browse(16)
                if not existing_activity and user:
                    move.activity_schedule(
                        activity_type_id=activity_type.id,
                        summary="Subir factura a portal",
                        note=_(
                            "Favor de subir esta factura al portal del cliente."
                        ),
                        user_id=user.id,
                    )

        return res
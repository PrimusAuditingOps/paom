from odoo import models

class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    def send_email(self, message, mail_server_id=None, smtp_session=None):
        # Detectar si es Amazon SES
        if self.smtp_host and 'amazonaws.com' in self.smtp_host:
            
            message['Return-Path'] = 'notifications@pao-usa.com'
            message['Sender'] = 'notifications@pao-usa.com'

        return super().send_email(
            message,
            mail_server_id=mail_server_id,
            smtp_session=smtp_session
        )



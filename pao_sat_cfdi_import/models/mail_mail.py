from odoo import models

class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _send(self, auto_commit=False, raise_exception=False):
        IrMailServer = self.env['ir.mail_server']

        for mail in self:
            # Obtener servidor SMTP que se usará
            mail_server = IrMailServer._get_mail_server(mail)

            if mail_server and mail_server.smtp_host:
                # Detectar si es Amazon SES
                if mail_server.name == 'Amazon SES Hector':
                    mail.email_from = 'notifications@pao-usa.com'
                    mail.reply_to = 'notifications@pao-usa.com'
                    mail.bounce_address = 'notifications@pao-usa.com'

        return super()._send(auto_commit=auto_commit, raise_exception=raise_exception)
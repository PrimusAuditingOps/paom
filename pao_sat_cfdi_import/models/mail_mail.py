from odoo import models

class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _send(self, *args, **kwargs):
        for mail in self:
            mail_server = mail.mail_server_id

            if mail_server and mail_server.smtp_host:
                if 'amazonaws.com' in mail_server.smtp_host:
                    mail.email_from = 'notifications@pao-usa.com'
                    mail.reply_to = 'notifications@pao-usa.com'
                    mail.bounce_address = 'notifications@pao-usa.com'

        return super()._send(*args, **kwargs)



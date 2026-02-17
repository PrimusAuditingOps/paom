from odoo import models, fields, api

class SendMassReminderWizard(models.TransientModel):
    _name = 'send.mass.reminder.wizard'
    _description = 'Send Mass Reminder Wizard'
    
    mail_template_id = fields.Many2one(
        string='Mail Template',
        comodel_name='mail.template',
        domain = [('model','=','send.anniversary.reminder')],
        required=True
        # default = None
    )
    
    preview_subject = fields.Char(
        string="Subject Preview",
        readonly=True
    )

    preview_body = fields.Html(
        string="Body Preview",
        readonly=True
    )

    @api.onchange('mail_template_id')
    def _onchange_mail_template(self):
        if self.mail_template_id:
            self.preview_subject = self.mail_template_id.subject
            self.preview_body = self.mail_template_id.body_html
        else:
            self.preview_subject = False
            self.preview_body = False

    def action_send(self):
        active_ids = self.env.context.get('active_ids', [])
        records = self.env['pao.anniversary.reminder'].browse(active_ids)

        for rec in records:
            rec.send_mass_reminders(self.mail_template_id)

        return {'type': 'ir.actions.act_window_close'}

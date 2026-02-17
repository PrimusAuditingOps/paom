from odoo import models, fields

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

    def action_send(self):
        active_ids = self.env.context.get('active_ids', [])
        records = self.env['pao.anniversary.reminder'].browse(active_ids)

        for rec in records:
            rec.send_mass_reminders(self.mail_template_id)

        return {'type': 'ir.actions.act_window_close'}

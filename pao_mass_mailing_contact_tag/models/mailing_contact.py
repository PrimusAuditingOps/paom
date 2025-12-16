from odoo import fields, models, _

class MailingContact(models.Model):
    _inherit='mailing.contact'

    pao_tag_ids = fields.Many2many(
        'pao.mailing.contact.tag', 
        column1='contact_id',
        column2='tag_id', 
        string='Tags'
    )
from odoo import fields, models, _
from random import randint

class PaoMailingContactTag(models.Model):
    _description = 'Pao Mailing Contact Tag'
    _name = 'pao.mailing.contact.tag'
    _order = 'name'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color', default=_get_default_color)
    active = fields.Boolean(default=True, help="The active field allows you to hide the tag without removing it.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

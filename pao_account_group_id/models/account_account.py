from odoo import fields, models, _

class AccountAccount(models.Model):
    _inherit='account.account'

    group_id = fields.Many2one('account.group', string="Group", help="", readonly=False)
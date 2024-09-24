from odoo import api, models, fields
from odoo.tools.translate import _


class AccountMove(models.Model):
    _inherit = 'account.move'

    billing_user_id = fields.Many2one('res.users', string="Billing Person", default = lambda self: self.create_uid.id)
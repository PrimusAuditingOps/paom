from odoo import fields, models

class Partner(models.Model):
    _inherit='res.partner'

    cgg_group_id = fields.Many2one(
        comodel_name='customergroups.group',
        string='Group',
        ondelete='set null',
    )
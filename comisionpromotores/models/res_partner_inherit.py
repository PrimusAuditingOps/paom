from odoo import fields, models

class Partner(models.Model):
    _inherit='res.partner'

    promotor_id = fields.Many2one(
        comodel_name='comisionpromotores.promotor',
        string='Promoter',
        ondelete='set null',
    )
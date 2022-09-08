from odoo import fields, models

class Partner(models.Model):
    _inherit='res.partner'

    pao_shipper_id = fields.Many2one(
        comodel_name='pao.shippers',
        string='Shipper',
        ondelete='set null',
    )
from odoo import fields, models

class ResPartner(models.Model):
    _inherit='res.partner'

    pao_office_id = fields.Many2one(
        comodel_name='pao.offices',
        string='Office',
        ondelete='set null',
    )
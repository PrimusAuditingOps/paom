from odoo import fields, models



class ResPartner(models.Model):
    _inherit='res.partner'

    pao_shipper_id = fields.Many2one('pao.shippers', string='Shipper',
                                     ondelete='set null')
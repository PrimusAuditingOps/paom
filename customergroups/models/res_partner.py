from odoo import fields, models



class ResPartner(models.Model):
    _inherit = 'res.partner'

    cgg_group_id = fields.Many2one('customergroups.group', string='Group',
                                   ondelete='set null')
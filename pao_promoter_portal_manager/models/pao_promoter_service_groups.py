from odoo import fields, models


class PaoPromoterServiceGroups(models.Model):
    _name = 'pao.promoter.service.groups'
    _description = 'Promoter Service Groups'

    name = fields.Char(string="Name", required=True)
    image = fields.Image(string="Group image", max_width=1024,
                         max_height=1024, required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company) 

from odoo import fields, models



class PaoPromoterService(models.Model):
    _name = 'pao.promoter.service'
    _description = 'Promoter Service'

    name = fields.Char(string="Name", required=True, translate=True)
    service_group_id = fields.Many2one('pao.promoter.service.groups',
                                       string="Group",
                                       ondelete='cascade',
                                       required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company) 
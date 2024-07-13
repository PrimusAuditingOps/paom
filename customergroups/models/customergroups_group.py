from odoo import fields, models



class CustomerGroupsGroup(models.Model):
    _name = 'customergroups.group'
    _description = 'Modelo para los grupos que puede pertenecer un cliente'

    name = fields.Char(required=True, string="Group")
    customer_ids = fields.One2many('res.partner', inverse_name='cgg_group_id',
                                   string='Customers')

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company) 
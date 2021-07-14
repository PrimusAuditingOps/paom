from odoo import fields, models

class CustomerGroupsGroup(models.Model):
    
    _name = 'customergroups.group'
    _description = 'Modelo para los grupos que puede pertenecer un cliente'

    name = fields.Char(
        required=True,
        string= "Group",
    )
    customer_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='cgg_group_id',
        string='Customers',
    )
    
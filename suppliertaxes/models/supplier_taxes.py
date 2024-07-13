from dataclasses import field
from odoo import fields, models, api
from odoo.tools.translate import _




class SupplierTaxes(models.Model):
    _name = 'suppliertaxes.supplier.taxes'
    _description = 'Supplier taxes'

    name = fields.Char(required=True)
    taxes_id = fields.Many2many('account.tax', string='Taxes', required = True,
                                domain=[('type_tax_use', '=', 'purchase')])   

    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company) 
    

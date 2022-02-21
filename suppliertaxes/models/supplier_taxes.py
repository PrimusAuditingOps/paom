from dataclasses import field
from odoo import fields, models, api
from odoo.tools.translate import _
from logging import getLogger


_logger = getLogger(__name__)

class SupplierTaxes(models.Model):
    _name = 'suppliertaxes.supplier.taxes'
    _description = 'Supplier taxes'


    name = fields.Char(
        required = True,
        string= "Name",
    )
    taxes_id = fields.Many2many(
        comodel_name = 'account.tax', 
        string='Taxes',
        required = True,
        domain=[('type_tax_use', '=', 'purchase')]
    )    
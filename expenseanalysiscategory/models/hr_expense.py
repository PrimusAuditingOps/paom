from odoo import fields, models, api
from logging import getLogger

_logger = getLogger(__name__)
class HrExpense(models.Model):

    _inherit='hr.expense'
    
    eac_product_category_id = fields.Many2one(
        related='product_id.product_tmpl_id.categ_id', 
        readonly=True,
        store=True,
        string="Product Category",
    )
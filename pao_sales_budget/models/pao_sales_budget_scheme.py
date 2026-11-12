from odoo import models, fields
from logging import getLogger

_logger = getLogger(__name__)

class PAOSalesBudgetScheme(models.Model):
    _name = 'pao.sales.budget.scheme'
    _description = 'PAO Sales Budget Scheme'
    _order = 'sequence, name'
    _sql_constraints = [
        ('uc_pao_sales_budget_scheme',
         'UNIQUE(name)',
         "There is already a scheme with this name"),
    ]
    
    sequence = fields.Integer(
        string="Sequence", default=10,
        help="Orden en que aparecen los esquemas en los reportes. Se cambia arrastrando en la lista.")
    name = fields.Char(
        string = "Name", 
        required= True
    )
    product_template_ids = fields.One2many('product.template',
                                         inverse_name='pao_sales_budget_scheme_id',
                                         string='Products')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
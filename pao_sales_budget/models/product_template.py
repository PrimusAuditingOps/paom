from odoo import fields, models, api



class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    pao_sales_budget_scheme_id = fields.Many2one(
        'pao.sales.budget.scheme',
        string='Sales Budget Scheme'
        ondelete='restrict'
    )
class PAOSalesBudgetScheme(models.Model):
    _name = 'pao.sales.budget.scheme'
    _description = 'PAO Sales Budget Scheme'
    _sql_constraints = [
        ('uc_pao_sales_budget_scheme',
         'UNIQUE(name)',
         "There is already a scheme with this name"),
    ]
    name = fields.Char(string="Sales Budget Scheme", required= True)
    product_template_ids = fields.One2many('product.template',
                                         inverse_name='pao_sales_budget_scheme_id',
                                         string='Products')
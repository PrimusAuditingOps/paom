from odoo import api, models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    
    internal_search_code = fields.Char('Internal Search Code')
    country_code = fields.Char(related='company_id.country_code')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        # if not self.env.context.get('display_prm_customer_number', False):
        #     return super(ProductTemplate, self).name_search(name, args, operator, limit)

        args = args or []
        domain = args + []
        if name:
            domain += ['|', '|', ('internal_search_code', operator, name), ('default_code', operator, name), ('name', operator, name)]
        
        partners = self.search(domain, limit=limit)
        return partners.name_get()
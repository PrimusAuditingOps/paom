from odoo import fields, models, api



class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    paa_schem_id = fields.Many2one('paa.assignment.auditor.scheme',
                                   string='Scheme',
                                   ondelete='set null')
    paa_is_an_audit = fields.Boolean(string='Is a category of audits',
                                     default=False)
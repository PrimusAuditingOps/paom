from odoo import fields, models, api



class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    paa_is_an_audit = fields.Boolean(string='Is an audit', default=False)
    paa_schem_id = fields.Many2one('paa.assignment.auditor.scheme',
                                   string='Scheme',
                                   ondelete='set null')
from odoo import fields, models, api



class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    pao_agreement_reviewer = fields.Boolean(
        string='Agreement for Reviewer',
        default=False
    )
    pao_agreement_certifier = fields.Boolean(
        string='Agreement for Certifier',
        default=False
    )

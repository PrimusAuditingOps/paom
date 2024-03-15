from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProposalTermsSchemes(models.Model):

    _name = "proposal.terms.schemes"
    _description="Proposal terms by scheme"
    
    name = fields.Char("Name")
    # scheme_id =  fields.Many2one('pao.pricelist.proposal', string="Pricelist Proposal", required=True)
    terms_and_conditions = fields.Text(string="Terms & Conditions", required=True, translate=True)
    
    
    
    
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductProposalItem(models.Model):

    _name = "product.proposal.item"
    _inherit="product.pricelist.item"
    
    pricelist_id =  fields.Many2one('pao.pricelist.proposal', string="Pricelist Proposal")
    
    
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProposalTermsSchemes(models.Model):

    _name = "proposal.terms.schemes"
    _description="Proposal terms by scheme"
    
    name = fields.Char("Name")
    # scheme_id =  fields.Many2one('pao.pricelist.proposal', string="Pricelist Proposal", required=True)
    terms_and_conditions = fields.Html(string="Terms & Conditions", required=True, translate=True)
    
class ProposalTemplates(models.Model):

    _name = "proposal.templates"
    _description="Proposal Templates"
    
    name = fields.Char("Name")
    template = fields.Html(string="Template", required=True, translate=True)
    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        string='Attachments',
        domain=[('res_model', '=', 'proposal.templates')]
    )
    # attachment_ids = fields.Many2many(
    #     'ir.attachment', 
    #     'pao_sign_sa_agreements_sent_ir_attachments_rel',
    #     'agreements_sent_id', 
    #     'attachment_id', 
    #     'Attachments'
    # )
    
    
    
    
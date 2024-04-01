from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductProposalItem(models.Model):

    _inherit="hr.employee"
    
    pricelist_proposal_manager =  fields.Boolean(string="Pricelist Proposal Manager", default=False)
    
    @api.constrains('pricelist_proposal_manager')
    def _check_unique_pricelist_proposal_manager(self):
        for record in self:
            if record.pricelist_proposal_manager:
                other_records = self.env['hr.employee'].search([('pricelist_proposal_manager', '=', True)])
                if len(other_records) > 1 or (len(other_records) == 1 and other_records.id != record.id):
                    raise ValidationError(_("Only one employee can be pricelist proposal manager."))
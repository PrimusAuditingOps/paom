from odoo import fields, models, api
from logging import getLogger

_logger = getLogger(__name__)
class Partner(models.Model):
    _inherit='res.partner'

    
    """organization_id = fields.One2many(
        comodel_name='servicereferralagreement.organization',
        inverse_name='customer_id',
        string='Organizations',
    )"""

    organization_ids = fields.Many2many(
        'servicereferralagreement.organization',
        'servicereferralagreement_organization_res_partner_rel',
        'res_partner_id', 'servicereferralagreement_organization_id',
        string='Organizations',
    )

    vendor_service_percentage = fields.Float(
        default = 0.00,
        required = True,
        string= "Vendor service percentage",
    )

    audit_fee_percentages_ids = fields.Many2many(
        'servicereferralagreement.percentageofauditfee',
        'servicereferralagreement_percentageofauditfee_res_partner_rel',
        'res_partner_id', 'servicereferralagreement_percentageofauditfee_id',
        string='audit fee percentages',
        required = True,
    )
    @api.onchange('audit_fee_percentages_ids')
    def _change_audit_fee(self):
        for rec in self:
            list_remove_elements = []
            list_exist_fees = []
            for fees in rec.audit_fee_percentages_ids:        
                if fees.audit_fees_id.name not in list_exist_fees:
                    list_exist_fees.append(fees.audit_fees_id.name)
                else:
                    list_remove_elements.append(fees._origin.id)
                    rec.audit_fee_percentages_ids = [(2, fees._origin.id, 0)]


    
    

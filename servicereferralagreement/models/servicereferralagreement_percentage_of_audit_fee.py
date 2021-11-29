from odoo import fields, models
class ServicereferralagreementPercentageOfAuditFee(models.Model):
    _name = 'servicereferralagreement.percentageofauditfee'
    _description = 'percentageofauditfee'
    _rec_name = 'audit_fees_id'

    _sql_constraints = [
        ('uc_percentage_audit_fee',
         'UNIQUE(audit_fees_id,audit_percentage)',
         "There is already a audit type with this percentage"),
    ]
    
    audit_fees_id = fields.Many2one(
        comodel_name = 'servicereferralagreement.auditfees', 
        string='Audit type', 
        help='Select Audit type', 
        ondelete='restrict',
        required=True,
    )
    audit_percentage  = fields.Float(
        default = 0.00,
        digits=(12,3),
        required = True,
        string= "Audit percentage",
    )

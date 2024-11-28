from odoo import fields, models
from datetime import datetime

class ServiceReferralAgreementAuditFees(models.Model):
    _inherit='servicereferralagreement.auditfees'

    default = fields.Boolean(
        string= "Default Rate For Assignment",
        default= False,
    )
    
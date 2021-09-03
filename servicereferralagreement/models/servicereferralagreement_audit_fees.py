
from odoo import fields, models, api, _
from logging import getLogger
from odoo.exceptions import ValidationError

_logger = getLogger(__name__)
class ServicereferralagreementAuditFees(models.Model):
    _name = 'servicereferralagreement.auditfees'
    _description = 'auditfees'
    _sql_constraints = [
        ('uc_audit_fee_name',
         'UNIQUE(name)',
         "There is already a audit type with this name"),
    ]
    name = fields.Char(
        string="Audit type",
        required= True,
    )
    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.env['servicereferralagreement.auditfees'].search([('name', '=ilike', self.name), ('id','!=',self.id)])
        for n in names:
            raise ValidationError("There is already a audit type with this name") 

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError



class PaoServicereFerralAgreementAuditFees(models.Model):
    _name = 'servicereferralagreement.auditfees'
    _description = 'auditfees'
    _sql_constraints = [
        ('uc_audit_fee_name',
         'UNIQUE(name)',
         "There is already a audit type with this name"),
    ]
    name = fields.Char(string="Audit type", required= True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)

    @api.constrains('name')
    def _check_duplicate_name(self):
        auditfees = self.env['servicereferralagreement.auditfees'].search(
            [('name', '=ilike', self.name), ('id', '!=', self.id)])
        if auditfees:
            raise ValidationError("There is already a audit type with this name: %s"
                                  %(auditfees.mapped('name'))) 
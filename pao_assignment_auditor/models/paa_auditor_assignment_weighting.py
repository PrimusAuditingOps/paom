from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
class PaaAuditorAssignmentWeighting(models.Model):
    _name = 'paoassignmentauditor.weighting'
    _description = 'Auditor assignment weighting'

    name = fields.Char(
        string = 'Weighting',
        default = 'Ponderacíon',
        translate=True,
    )
    scheme_ranking = fields.Integer(
        default = 0,
        required = True,
        string= "Scheme ranking",
    )
    location = fields.Integer(
        default = 0,
        required = True,
        string= "Location",
    )
    audit_quantity_target = fields.Integer(
        default = 0,
        required = True,
        string= "Audits quantity target",
    )
    audit_honorarium_target = fields.Integer(
        default = 0,
        required = True,
        string= "Audits honorarium target",
    )
    @api.constrains('scheme_ranking','location','audit_quantity_target','audit_honorarium_target')
    def _validate_weighting(self):
        for rec in self:
            sum_weighting = 0
            sum_weighting = rec.scheme_ranking + rec.location + rec.audit_quantity_target + rec.audit_honorarium_target
            if sum_weighting != 10:
                msg = _('The sum of the variables must be equal to 10')
                raise ValidationError(msg)
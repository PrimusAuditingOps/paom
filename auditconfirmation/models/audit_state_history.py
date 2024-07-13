from odoo import fields, models, api, _
from odoo.exceptions import ValidationError



class AuditStateHistoy(models.Model):
    _name = 'auditconfirmation.auditstate.history'
    _description = 'Audit State history'
    _order = 'create_date desc'

    audit_state = fields.Many2one('auditconfirmation.auditstate',
                                  string="Audit status",
                                  ondelete='set null')
    purchase_order_id = fields.Many2one('purchase.order',
                                        string="Purchase order",
                                        ondelete='cascade')
    comments = fields.Text(string="Comments")
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            res = super(AuditStateHistoy, self).create(values)
            for rec in res:
                rec.purchase_order_id.write({
                    'ac_audit_status': rec.audit_state
                })
            return res
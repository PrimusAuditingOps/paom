from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from logging import getLogger

_logger = getLogger(__name__)

class AuditStateHistoy(models.Model):
    
    _name = 'auditconfirmation.auditstate.history'
    _description = 'Audit State history'
    _order = 'create_date desc'

    audit_state = fields.Many2one(
        string="Audit status",
        comodel_name='auditconfirmation.auditstate',
        ondelete='set null',
    )
    purchase_order_id = fields.Many2one(
        string="Purchase order",
        comodel_name='purchase.order',
        ondelete='cascade',
    )
    comments = fields.Text(
        string = "Comments",

    )
    @api.model
    def create(self, values):
        res = super(AuditStateHistoy, self).create(values)
        for rec in res:
            rec.purchase_order_id.write({"ac_audit_status": rec.audit_state})
        return res
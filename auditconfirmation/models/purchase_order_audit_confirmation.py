from odoo import fields, models, api
import uuid

class PurchaseOrderAuditConfirmation(models.Model):
    
    _name='auditconfirmation.purchaseconfirmation'
    _description = "Purchase confirmation"

    ac_access_token = fields.Char(
        'Security Token', 
        default=lambda self: str(uuid.uuid4().hex),
        help="Access token to set the audit confirmation of the value",
        readonly=True,
        copy=False)
    ac_consumed = fields.Boolean(
        string = "Confirmation consumed",
        default = False,
    )
    ac_consumed_travel_expenses = fields.Boolean(
        string = "Travel expenses consumed",
        default = False,
    )
    ac_audit_confirmation_status = fields.Selection(
        selection=[
            ('0', "Not Confirmed"),
            ('1', "Confirmed"),
            ('2', "Denied"),
            ('3', "Tentatively confirmed"),
        ],
        string="Audit Availability Confirmation Status", 
        readonly=True, copy=False,
        default='0',
        help="Refers to the status of the audit confirmation.")
    ac_id_purchase = fields.Integer(
        string='Purchase ID', 
        required=True, 
        help="Identifier of the purchase", 
        index=True,
    )
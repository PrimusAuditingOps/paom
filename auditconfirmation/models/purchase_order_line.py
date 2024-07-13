from odoo import fields, models



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    ac_audit_status = fields.Many2one('auditconfirmation.auditstate',
                                      related='order_id.ac_audit_status',
                                      string='Audit Status', readonly=True,
                                      store=True)
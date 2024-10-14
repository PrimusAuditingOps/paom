from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class RADocument(models.Model):
    _name = 'ra.document'
    
    name = fields.Char('Name')
    status = fields.Selection(selection=[('sent', 'Sent'), ('sign', 'Signed'), ('cancel', 'Cancelled')], string="Status")
    attachment_ids = fields.Many2many('ir.attachments', string="Attachments")
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        ondelete='cascade',
        required=True,
    )
    
    def action_resend(self):
        return True
    
    def action_cancel(self):
        self.status = 'cancel'
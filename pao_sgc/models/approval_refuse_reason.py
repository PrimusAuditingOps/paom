from odoo import api, fields, models

class PAOUploadDocumentVersion(models.TransientModel):
    _name = 'pao.approval.refuse.reason'
    _description = 'Wizard Model to input the reason why a request is being refused'

    reason = fields.Text('Refuse reason', required=True)
    approval_id = fields.Many2one('approval.request', string="Approval Reference")
    
    def refuse_request(self):
        if self.approval_id:
            self.approval_id.set_refuse_reason(self.reason)
            
            approvers = [approver for approver in self.approval_id.approver_ids]
            
            self.approval_id.action_refuse(approvers[0])

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pytz
from datetime import datetime


class ApprovalRequestInherit(models.Model):
    _inherit = 'approval.request'
    
    pao_document_name = fields.Char('Document Name', readonly=True)
    pao_document_version = fields.Char('Current Version', readonly=True)
    pao_document_revision = fields.Char('Revision Number', readonly=True)
    pao_document_document_file = fields.Binary(string='Document File', attachment=True, readonly=True)
    pao_document_filename = fields.Char('Filename', readonly=True)
    pao_document_version_management_id = fields.Many2one('pao.documents.version.management', string="Document Version Origin", readonly=True)
    pao_document_request_closed = fields.Boolean("PAO Document has been closed", default=False)
    pao_refuse_reason = fields.Text('Refuse Reason')
    request_status = fields.Selection([
        ('new', 'To Submit'),
        ('pending', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ])
    pao_document_reviewer = fields.Many2one('res.users', string="Assigned reviewer", readonly=True)
    pao_document_reviewed = fields.Boolean("PAO Document reviewed", default=False)
    is_user_reviewer = fields.Boolean(compute="_compute_is_user_reviewer", store=False)


    def _compute_is_user_reviewer(self):
        for rec in self:
            rec.is_user_reviewer = rec.pao_document_reviewer.id == self.env.user.id
    
    @api.constrains('request_status')
    def _onchange_status_constrains(self):
        for record in self:
            if record.pao_document_version_management_id:
                
                if record.pao_document_request_closed:
                    raise UserError(_("The request has been closed and cannot be undone. To make changes to the current document, please upload a new one using the SGC module."))
                
                if record.request_status == 'approved':
                    if not record.pao_document_reviewed:
                        raise UserError(_("The request must be reviewed before approval."))
                    record.pao_document_version_management_id.update_current_version({
                        'name': record.pao_document_name,
                        'version': record.pao_document_version,
                        'revision_number': record.pao_document_revision,
                        'document_file': record.pao_document_document_file,
                        'filename': record.pao_document_filename,
                        'last_updated_by': record.request_owner_id.id,
                        'approval_id': self.id,
                        'approval_request_in_progress': False,
                    })
                    record.pao_document_request_closed = True

                elif record.request_status == 'reviewed':
                    self._notify_review_done()

                elif record.request_status in ('cancel', 'refused'):
                    record.pao_document_request_closed = True
                    self.pao_document_version_management_id.set_approval_in_progress(False)
    
    def action_refuse(self, approver=None):
    
        if self.pao_document_version_management_id and not self.pao_refuse_reason:
            return {
                'name': _('Refuse details'),
                'type': 'ir.actions.act_window',
                'res_model': 'pao.approval.refuse.reason',
                'view_mode': 'form',
                'view_id': self.env.ref('pao_sgc.view_pao_approval_refuse_reason_form').id,
                'target': 'new',
                'context': {
                    'default_approval_id': self.id,
                },
            }
        else:
            super(ApprovalRequestInherit, self).action_refuse(approver=approver)
            if self.pao_document_version_management_id: self.cancel_all_activities()
                
    def action_cancel(self):
        if self.pao_document_version_management_id and (self.create_uid.id != self.env.user.id):
            raise UserError(_("The request can only be cancelled by its owner."))
        else:
            super(ApprovalRequestInherit, self).action_cancel()
            if self.pao_document_version_management_id: self.cancel_all_activities()
        
    def set_refuse_reason(self, reason):
        self.pao_refuse_reason = reason
        
        mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{self.request_owner_id.id}">@{self.request_owner_id.name}</a>'
        approval_request_link = ('<a href="#" data-oe-model="approval.request" data-oe-id="%(approval_id)d">%(name)s</a>'
                                ) % {'name': self.name, 'approval_id': self.id}
        reasons = ('<br/><b>%(refuse_reason)s</b>') % {'refuse_reason': reason}
        
        reason_message = _('Hello %(mention_html)s, the request %(approval_request_link)s has been refused due to the following reasons: %(reasons)s'
                            ) % {'mention_html': mention_html, 'approval_request_link': approval_request_link, 'reasons': reasons}
        
        self.pao_document_version_management_id.add_request_change_log(reason_message, self.request_owner_id)
        
    def cancel_all_activities(self):
        activities = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('res_model_id', '=', self.env['ir.model']._get('approval.request').id),
            ('state', '=', 'pending'),
        ])

        for activity in activities:
            activity.action_done()
            
    def action_reviewer_refuse(self):
        if self.pao_document_version_management_id and not self.pao_refuse_reason:
            return {
                'name': _('Refuse details'),
                'type': 'ir.actions.act_window',
                'res_model': 'pao.approval.refuse.reason',
                'view_mode': 'form',
                'view_id': self.env.ref('pao_sgc.view_pao_approval_refuse_reason_form').id,
                'target': 'new',
                'context': {
                    'default_approval_id': self.id,
                },
            }
        
    def _notify_review_done(self):
        mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{self.request_owner_id.id}">@{self.request_owner_id.name}</a>'
        approval_request_link = ('<a href="#" data-oe-model="approval.request" data-oe-id="%(approval_id)d">%(name)s</a>'
                                ) % {'name': self.name, 'approval_id': self.id}
        
        message = _('Hello %(mention_html)s, the request %(approval_request_link)s has been reviewed and is ready for approval.'
                            ) % {'mention_html': mention_html, 'approval_request_link': approval_request_link}
        
        self.pao_document_version_management_id.add_request_change_log(message, self.request_owner_id)

    def notify_reviewer(self):
        if self.pao_document_version_management_id:
            
            self.request_status = 'pending'
            
            zone = self.create_uid.tz
            requested_tz = pytz.timezone(zone)
            
            activity_vals = {
                'activity_type_id': 4,
                'summary': _('Review document'),
                'note': _('Please review the document.'),
                'res_id': self.id,
                'res_model_id': self.env['ir.model']._get('approval.request').id,
                'user_id': self.pao_document_reviewer.id,
                'date_deadline': (requested_tz.fromutc(datetime.utcnow())).today(),
            }
            self.env['mail.activity'].create(activity_vals)

            
            # mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{self.pao_document_reviewer.id}">@{self.pao_document_reviewer.name}</a>'
            
            # message_body = _('Hello %(mention_html)s, you have been assigned the task of reviewing this document.'
            #             ) % {'mention_html': mention_html}
            
            # message = self.message_post(
            #     body=message_body,
            #     partner_ids=[self.pao_document_reviewer.partner_id.id],
            # )
            
            # self.message_notify(
            #     message_id=message.id,
            # )
            
                
    def document_reviewed(self):
        if not self.pao_document_reviewed:
            
            self.action_confirm()
            
            self.pao_document_reviewed = True
            self.request_status = 'reviewed'
            
            activity = self.env['mail.activity'].search([
                ('res_id', '=', self.id),
                ('res_model_id', '=', self.env['ir.model']._get('approval.request').id),
                ('user_id', '=', self.pao_document_reviewer.id),
                ('state', '=', 'pending'),
                ('summary', 'ilike', 'document'),
            ], limit=1)

            if activity:
                activity.action_done()
            
            # mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{self.request_owner_id.id}">@{self.request_owner_id.name}</a>'
                
            # message_body = _('Hello %(mention_html)s, the document has been reviewed and its ready to its approval.'
            #             ) % {'mention_html': mention_html}
            
            # approvers_partner_ids = self.approver_ids

            # approvers_partner_ids_list = [approver.user_id.partner_id.id for approver in approvers_partner_ids]

            
            # message = self.message_post(
            #     body=message_body,
            #     partner_ids=[self.request_owner_id.partner_id.id] + approvers_partner_ids_list,
            # )
                
            # self.message_notify(
            #     message_id=message.id,
            # )
        
        
                    

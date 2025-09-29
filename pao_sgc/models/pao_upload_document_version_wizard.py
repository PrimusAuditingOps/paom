from odoo import api, fields, models, _
import os

from logging import getLogger
_logger = getLogger(__name__)

class PAOUploadDocumentVersion(models.TransientModel):
    _name = 'pao.upload.document.version'
    _description = 'Wizard Model to request the approval of a new version of a document'

    name = fields.Char('Document Name', required=True)
    version = fields.Char('Version (Odoo)', required=True)
    revision_number = fields.Char("Revision Number", required=True)
    document_file = fields.Binary(string='Document File', required=True)
    filename = fields.Char('Filename', readonly=True)
    version_management_id = fields.Many2one('pao.documents.version.management', string="Document Version Origin")
    
    selected_approvers = fields.Many2many('res.users', string='Approvers', required=True)
    selected_reviewer = fields.Many2one('res.users', string="Reviewer", required=True)
    approval_reason = fields.Text(string="Description of the change")
    
    @api.model
    def create(self, vals):
        # Ensure filename is preserved if missing
        if vals.get('document_file') and not vals.get('filename'):
            vals['filename'] = 'unknown_file'
        return super().create(vals)

    def write(self, vals):
        # Preserve filename on update
        if vals.get('document_file') and not vals.get('filename'):
            vals['filename'] = self.filename or 'unknown_file'
        return super().write(vals)
    
    @api.constrains("name", "version", "document_file")
    def _format_filename(self):
            for record in self:
                if record.id and record.name and record.revision_number and record.document_file and record.filename:
                    ext = os.path.splitext(record.filename)[1] 
                    record.filename = record.filename = record.name + '_r' + record.revision_number.replace('.', '_') + ext
                else:
                    record.filename = ""
                _logger.warning(record.filename + "    ***********")
    
    def request_document_approval_action(self):
        
        if self.version_management_id.is_version_available(self.version):
        
            approver_ids = [(0, 0, {'user_id': user.id, 'status': 'new'}) for user in self.selected_approvers]
            
            xml_id = 'approval_category_documents_sgc'

            ir_model_data = self.env['ir.model.data'].sudo().search([('model', '=', 'approval.category'),('name', '=', xml_id),], limit=1)

            category_id = ir_model_data.res_id
            
            request_name = _('REQ: %(document_name)s - Version: %(version)s - Revision: %(revision)s'
                            ) % {'document_name': self.name, 'version': self.version, 'revision': self.revision_number}
        
            approval_data = {
                'request_owner_id': self.create_uid.id,
                'category_id': category_id,
                'name': request_name,
                'approver_ids': approver_ids,
                'pao_document_reviewer': self.selected_reviewer.id,
                'reason': self.approval_reason,
                'pao_document_name': self.name,
                'pao_document_version': self.version,
                'pao_document_revision': self.revision_number,
                'pao_document_document_file': self.document_file,
                'pao_document_filename': self.filename,
                'pao_document_version_management_id': self.version_management_id.id,
            }
            approval = self.env['approval.request'].create(approval_data)
            
            if self.document_file:
                attachment_values = {
                    'name': self.filename,
                    'datas': self.document_file,
                    'res_model': 'approval.request',
                    'res_id': approval.id,
                }
                attachment = self.env['ir.attachment'].create(attachment_values)
            
            approval.notify_reviewer()
            
            self.version_management_id.set_approval_in_progress(True)
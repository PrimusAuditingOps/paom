from odoo import models, fields, tools, api
import os

class PaoDocumentsVersionHistory(models.Model):

    _name="pao.documents.version.history"
    _description = "PAO Documents Version History"
    _order = 'create_date desc'
    
    name = fields.Char('Document Name', compute="_compute_document_name")
    version = fields.Char('Document Version (Odoo)')
    revision_number = fields.Char("Revision Number", required=True)
    document_file = fields.Binary(string='Document File', required=True)
    validity_start_date = fields.Date("Validity Start Date", required=True)
    validity_end_date = fields.Date("Validity End Date", required=True)
    filename = fields.Char('Filename')
    version_by = fields.Many2one('res.users', string="Version uploaded by", compute="_compute_version_by")
    version_management_id = fields.Many2one('pao.documents.version.management', string="Current document version", 
                                            # inverse_name='history_version_ids'
                                            )
    approval_id = fields.Many2one('approval.request', string="Approval Reference")
    
    # @api.model
    # def create(self, vals):
    #     # Ensure filename is preserved if missing
    #     if vals.get('document_file') and not vals.get('filename'):
    #         vals['filename'] = 'unknown_file'
    #     return super().create(vals)

    # def write(self, vals):
    #     # Preserve filename on update
    #     if vals.get('document_file') and not vals.get('filename'):
    #         vals['filename'] = self.filename or 'unknown_file'
    #     return super().write(vals)

    # @api.constrains("name", "revision_number", "document_file")
    # def _format_filename(self):
    #         for record in self:
    #             if record.id and record.name and record.revision_number and record.document_file and record.filename:
    #                 ext = os.path.splitext(record.filename)[1] 
    #                 record.filename = record.name + '_r' + record.revision_number.replace('.', '_') + ext
    #             else:
    #                 record.filename = ""
                    
    @api.depends("version_management_id")
    def _compute_document_name(self):
            for record in self:
                if not record.name:
                    record.name = record.version_management_id.name
                    
    def _compute_version_by(self):
            for record in self:
                if not record.version_by:
                    record.version_by = record.create_uid
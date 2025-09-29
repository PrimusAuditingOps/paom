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
    
    @api.depends("version_management_id")
    def _compute_document_name(self):
            for record in self:
                if not record.name:
                    record.name = record.version_management_id.name
                    
    def _compute_version_by(self):
            for record in self:
                if not record.version_by:
                    record.version_by = record.create_uid
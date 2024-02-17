from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
import pytz
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class PaoDocumentsVersionManagement(models.Model):

    _name="pao.documents.version.management"
    _description = "PAO Documents Version Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    code = fields.Char('Document Code', required=True)
    name = fields.Char('Document Name', required=True)
    version = fields.Char('Current Version (Odoo)')
    revision_number = fields.Char("Revision Number")
    document_file = fields.Binary(string='Document File', attachment=True)
    approval_date = fields.Date('Valid Since', readonly=True)
    expiration_date = fields.Date('Expiration Date')
    filename = fields.Char('Filename', readonly=True, compute="_compute_filename")
    history_version_ids = fields.One2many('pao.documents.version.history', string="Version History", inverse_name='version_management_id')
    last_updated_by = fields.Many2one('res.users', string="Last Updated By")
    approval_request_in_progress = fields.Boolean('Has an active request', default=False)
    approval_id = fields.Many2one('approval.request', string="Approval Reference", readonly=True)
    scheme_id = fields.Many2one('pao.sgc.scheme', string="Scheme", required=True)
    department_id = fields.Many2one('pao.sgc.department', string="Department", required=True)
    language_id = fields.Many2many('res.lang', string="Document Language", required=True)
    
    is_document_expired = fields.Boolean(compute="_compute_is_document_expired", store=False)
    is_document_near_expiration = fields.Boolean(compute="_compute_is_document_near_expiration", store=False)
    
    # current_time = fields.Datetime(compute="_get_now", store=False) 
    
    # def _get_now(self):
    #     self.current_time = fields.Datetime.now()
    
    def _get_today_date(self):
        for rec in self:
            zone = rec.create_uid.tz
            requested_tz = pytz.timezone(zone)
            today = requested_tz.fromutc(datetime.utcnow())
            return today.date()

    def _compute_is_document_expired(self):
        for rec in self:
            if not rec.expiration_date:
                rec.is_document_expired = False
            else:
                today = self._get_today_date()
                
                rec.is_document_expired = rec.expiration_date < today
    
    def _compute_is_document_near_expiration(self):
        for rec in self:
            if not rec.expiration_date:
                rec.is_document_near_expiration = False
            else:
                today = self._get_today_date()
                
                date_range = today + timedelta(days=15)
                rec.is_document_near_expiration = rec.expiration_date <= date_range
            
    @api.depends("name", "revision_number")
    def _compute_filename(self):
            for record in self:
                if record.id and record.name and record.revision_number and record.document_file:
                    record.filename = record.name + '_r' + record.revision_number.replace('.', '_')
                else:
                    record.filename = ""

    def upload_new_version_action(self):
        if self.approval_request_in_progress:
            raise ValidationError(_("This document has already an approval request in progress."))
        return {
            'name': _('Upload new version'),
            'type': 'ir.actions.act_window',
            'res_model': 'pao.upload.document.version',
            'view_mode': 'form',
            'view_id': self.env.ref('pao_sgc.view_pao_upload_document_version_form').id,
            'target': 'new',
            'context': {
                'default_name': self.name,
                'default_version_management_id': self.id,
            },
        }
    
    def action_view_active_approval_request(self):
        self.ensure_one()     
        action = {
            'res_model': 'approval.request',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': self.env.ref('approvals.approval_request_view_form').id,
            'name': _("Active approval request"),
            'res_id': self.env['approval.request'].search([
                ('pao_document_version_management_id', '=', self.id),
                ('pao_document_request_closed', '=', False)
            ], limit=1).id,
            # 'domain': [('pao_document_version_management_id', '=', self.id), ('pao_document_request_closed', '=', False)],
        }
        return action
    
    @api.model 
    def create(self, values):
        
        if any(values.get(field) for field in ['version', 'document_file', 'revision_number', 'approval_date']):
            if not all(values.get(field) for field in ['version', 'document_file', 'revision_number', 'approval_date']):
                raise ValidationError(_("It's necessary to fill in the fields: Current Version, Document File, Revision Number and Valid Since to proceed."))
            else:
                approval_date = fields.Date.from_string(values.get('approval_date'))
                values['expiration_date'] = approval_date + relativedelta(years=1)
        
        record = super(PaoDocumentsVersionManagement, self).create(values)
        
        if record.version and record.document_file and record.revision_number:
            record.last_updated_by = record.create_uid
            
        return record
    
    def update_current_version(self, data):
        previous_data ={
            'name': self.name,
            'version': self.version,
            'revision_number': self.revision_number,
            'document_file': self.document_file,
            'updated_by': self.last_updated_by.id,
            'approval_date': self.approval_date,
            'approval_id': self.approval_id.id,
        }
        
        self.name = data['name']
        self.version = data['version']
        self.revision_number = data['revision_number']
        self.document_file = data['document_file']
        self.approval_date = self._get_today_date()
        self.expiration_date = self._get_today_date() + relativedelta(years=1)
        self.filename = data['filename']
        self.last_updated_by = data['last_updated_by']
        self.approval_id = data['approval_id']
        self.approval_request_in_progress = data['approval_request_in_progress']
        
        mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{self.approval_id.request_owner_id.id}">@{self.approval_id.request_owner_id.name}</a>'
        
        approval_request_link = ('<a href="#" data-oe-model="approval.request" data-oe-id="%(approval_id)d">%(name)s</a>'
                                ) % {'name': self.approval_id.name, 'approval_id': self.approval_id.id}
        
        message = _('Hello %(mention_html)s, the request %(approval_request_link)s has been approved.'
                    ) % {'approval_request_link': approval_request_link, 'mention_html': mention_html}


        
        self.add_request_change_log(message, self.approval_id.request_owner_id)
        
        if previous_data['document_file'] and previous_data['version'] and len(previous_data['version']) > 0 and not self.approval_request_in_progress:
            self.add_previous_version_to_history(previous_data)
        

    def add_previous_version_to_history(self, previous_data):
        history_data = {
            'name': previous_data['name'],
            'version': previous_data['version'],
            'revision_number': previous_data['revision_number'],
            'document_file': previous_data['document_file'],
            'version_management_id': self.id,
            'version_by': previous_data['updated_by'],
            'validity_start_date': previous_data['approval_date'],
            'validity_end_date': self._get_today_date(),
            'approval_id': previous_data['approval_id'],
        }
        self.env['pao.documents.version.history'].create(history_data)
        
    def is_version_available(self, tentative_version):
        # Check if the version already exists in history
        existing_history = self.env['pao.documents.version.history'].search(
            [('version_management_id', '=', self.id), ('version', '=', tentative_version)]
        )

        if existing_history or self.version == tentative_version:
            raise ValidationError(_("Cannot update using an existing version"))
        else:
            return True
        
    def set_approval_in_progress(self, status):
            self.approval_request_in_progress = status
    
    def add_request_change_log(self, message, user):
        message = self.message_post(
            body=message,
            partner_ids=[user.partner_id.id],
        )
        
        self.message_notify(
            message_id=message.id,
        )

    def postpone_expiration_date(self):
        self.expiration_date = self._get_today_date() + relativedelta(years=1)
    

    
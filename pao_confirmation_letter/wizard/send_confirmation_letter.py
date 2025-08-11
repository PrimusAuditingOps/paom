from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from logging import getLogger
from datetime import datetime
from werkzeug.urls import url_join
import pytz
import base64
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class ConfirmationLetterSendWizard(models.TransientModel):
    _name = 'pao.send.confirmation.letter.wizard'
    _description = 'PAO Send Confirmation Letter'


    sale_order_id = fields.Many2one('sale.order', required=True)
    
    partner_ids = fields.Many2many(
        'res.partner', 
        string='Contacts',
        required=True,
    )
    message = fields.Html(
        string="Message",
    ) 
    subject = fields.Char(
        string="Subject", 
        required=True
    )
    mail_template_id = fields.Many2one(
        string='Mail Template',
        comodel_name='mail.template',
        domain = [('model','=','pao.send.confirmation.letter.wizard')],
    )
    
    registration_number_id = fields.Many2one(
        'servicereferralagreement.registrynumber',
        string='Registration Number',
        required=True,
    )
    
    available_registration_numbers_ids = fields.Many2many(
        'servicereferralagreement.registrynumber',
        'available_registration_numbers_confirmation_letter_rel',
        string='Registration Numbers',
        readonly=True
    )
    organization_id = fields.Many2one('servicereferralagreement.organization', string="Organization",required=True,)
    operation_ids = fields.One2many('pao.confirmation.letter.operation.wizard', 'wizard_id', string='Operations')
    service_start_date = fields.Date(string="Service Start Date",required=True,)
    service_end_date = fields.Date(string="Service End Date", required=True,)
    documento_format = fields.Selection(
        selection=[
            ("gfs_letter_english", "Letter of Confirmation - GFS English"),
            ("gfs_letter_spanish", "Letter of Confirmation - GFS Spanish"),
            ("gg_letter_english", "Letter of Confirmation - GG English"),
            ("gg_letter_spanish", "Letter of Confirmation - GG Spanish"),
        ],
        string="Format", 
        required=True,
    )

    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")
    
    @api.model
    def default_get(self, fields):
        res = super(ConfirmationLetterSendWizard, self).default_get(fields)

        
        sale_order_id = self.env.context.get('default_sale_order_id')
        if sale_order_id:
            sale_order = self.env['sale.order'].browse(int(sale_order_id))
            arr_ids = []

            for line in sale_order.order_line:
                if line.registrynumber_id and line.registrynumber_id.id not in arr_ids:
                    arr_ids.append(line.registrynumber_id.id)

            res['available_registration_numbers_ids'] = [(6, 0, arr_ids)]
        
        return res


    @api.constrains('operation_ids')
    def _validate_operation_ids(self):
        for rec in self:
            if len(rec.operation_ids) <= 0:
                raise ValidationError(_("Please add an operation."))

    @api.onchange('mail_template_id')
    def _change_mail_template(self):
        self.message = self.mail_template_id.body_html
        self.subject = self.mail_template_id.subject + " - " + self.organization_id.name if self.organization_id else self.mail_template_id.subject
        self.attachment_ids = self.mail_template_id.attachment_ids

    @api.onchange('registration_number_id')
    def _change_registration_number_id(self):
        for rec in self:
            if rec.sale_order_id and rec.registration_number_id.id:
                sale_order = self.env['sale.order'].browse(int(rec.sale_order_id.id))
                for line in sale_order.order_line:
                    if line.registrynumber_id and line.registrynumber_id.id == rec.registration_number_id.id and line.organization_id:
                        rec.organization_id = line.organization_id.id
                        rec.service_start_date = line.service_start_date
                        rec.service_end_date = line.service_end_date
                        break
 
    def create_confirmation_letter(self):
        self.ensure_one()

        operation_ids = []

        for operation in self.operation_ids:
            new_operation = self.env['pao.confirmation.letter.operations'].create({
                'name': operation.name,
                'operation_type': operation.operation_type,
            })
            operation_ids.append(new_operation.id)


        confirmation_letter_id = self.env['pao.confirmation.letter'].create(
            {
                "partner_ids": self.partner_ids,
                "organization_id": self.organization_id.id,
                "pao_registration_number_id": self.registration_number_id.id,
                "sale_order_id": self.sale_order_id.id,
                "operation_ids": [(6, 0, operation_ids)],
                "service_start_date":self.service_start_date,
                "service_end_date": self.service_end_date,
                "documento_format": self.documento_format,
            }
        )


        filename = _("confirmation_letter_%s_%s.%s") % (self.organization_id.name,self.registration_number_id.name, "pdf")
        pdf = self.env['ir.actions.report'].sudo()._render_qweb_pdf('pao_confirmation_letter.pao_confirmation_letter_report', [confirmation_letter_id.id], data= {"confirmationletter": confirmation_letter_id})[0]
        #pdf = request.env.ref('pao_globalgap_fans.globalgap_application_report').sudo()._render_qweb_pdf([fan_sudo], data= {"fanrequest": fan_sudo,"print": True})[0]
        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': base64.b64encode(pdf),
            'res_model': 'pao.confirmation.letter',
            'res_id': confirmation_letter_id.id,
            'type': 'binary',  # override default_type from context, possibly meant for another model!
        })
      
        confirmation_letter_id.write({"attachment_id":attachment.id})
        attachments = []

        for a in self.attachment_ids:
            attachments.append(a.id)
        
        attachments.append(attachment.id)
        
        confirmation_letter_id.message_post(
            subject=self.subject,
            body=self.message,
            body_is_html = True,
            partner_ids=[pid.id for pid in self.partner_ids],  
            attachment_ids=attachments,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        confirmation_letter_id.message_subscribe(partner_ids=[pid.id for pid in self.partner_ids])

        return {
            'type': 'ir.actions.act_window',
            'name': confirmation_letter_id.name,
            'res_model': 'pao.confirmation.letter',
            'view_mode': 'form',
            'res_id': confirmation_letter_id.id,
            'target': 'current',  # o 'new' si quieres que se abra en una ventana modal
        }


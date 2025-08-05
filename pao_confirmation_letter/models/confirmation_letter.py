from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from logging import getLogger
import uuid
from datetime import datetime, timedelta
import dateutil.parser
from odoo.tools import format_date
import pytz
_logger = getLogger(__name__)


class PaoConfirmationLetter(models.Model):
    _name = 'pao.confirmation.letter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'PAO Confirmation Letter'

    MONTHS_ES = {
        'January': 'enero',
        'February': 'febrero',
        'March': 'marzo',
        'April': 'abril',
        'May': 'mayo',
        'June': 'junio',
        'July': 'julio',
        'August': 'agosto',
        'September': 'septiembre',
        'October': 'octubre',
        'November': 'noviembre',
        'December': 'diciembre',
    }
    
    name = fields.Char('Name', compute="_set_confirmation_letter_name")
    
    company_id = fields.Many2one(related="sale_order_id.company_id")
    
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Contacts',
    )
    
    organization_id = fields.Many2one('servicereferralagreement.organization', string="Organization")

    attachment_id = fields.Many2one('ir.attachment', string="Attachments")
    
    pao_registration_number_id = fields.Many2one('servicereferralagreement.registrynumber',string='Registration Numbers',required=True,)
    
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sales Order',
        ondelete='cascade',
        required=True,
    )
    operation_ids = fields.Many2many(
        comodel_name='pao.confirmation.letter.operations',
        string='Operations',
    )
    service_start_date = fields.Date(string="Service Start Date")
    service_end_date = fields.Date(string="Service End Date")
    create_date_text = fields.Text(
        compute= '_generate_create_date_text',
        store=True,
    )
    service_start_date_text = fields.Text(
        compute= '_generate_service_date_text',
        store=True,
    )
    service_end_date_text = fields.Text(
        compute= '_generate_service_date_text',
        store=True,
    )
    create_date_spanish_text = fields.Text(
        compute= '_generate_create_date_text',
        store=True,
    )
    service_start_date_spanish_text = fields.Text(
        compute= '_generate_service_date_text',
        store=True,
    )
    service_end_date_spanish_text = fields.Text(
        compute= '_generate_service_date_text',
        store=True,
    )
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
    
    def _set_confirmation_letter_name(self):
        for rec in self:
            rec.name = rec.sale_order_id.name + ' - ' + rec.pao_registration_number_id.name
    

    def ordinal(self,n):
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"


    @api.depends('service_start_date','service_end_date')
    def _generate_service_date_text(self):
        for rec in self:
            day = self.ordinal(rec.service_start_date.day)
            rec.service_start_date_text = rec.service_start_date.strftime(f"%B {day}, %Y")
            day = self.ordinal(rec.service_end_date.day)
            rec.service_end_date_text = rec.service_end_date.strftime(f"%B {day}, %Y")

            month_en = rec.service_start_date.strftime("%B")
            month_es = self.MONTHS_ES.get(month_en, month_en)
            rec.service_start_date_spanish_text = rec.service_start_date.strftime(f"%d de {month_es}, %Y")
            month_en = rec.service_end_date.strftime("%B")
            month_es = self.MONTHS_ES.get(month_en, month_en)
            rec.service_end_date_spanish_text = rec.service_end_date.strftime(f"%d de {month_es}, %Y")
            """
            rec.service_start_date_text = format_date(
                self.env, 
                rec.service_start_date,
                date_format='MMMM d, yyyy',  
                lang_code='en_US'   
            )

            rec.service_end_date_text = format_date(
                self.env,               
                rec.service_end_date,
                date_format='MMMM d, yyyy',  
                lang_code='en_US'    
            )

            rec.service_start_date_spanish_text = format_date(
                self.env, 
                rec.service_start_date,
                date_format='d MMMM, yyyy',  
                lang_code='es_MX'   
            )

            rec.service_end_date_spanish_text = format_date(
                self.env,               
                rec.service_end_date,
                date_format='d MMMM, yyyy',  
                lang_code='es_MX'    
            )
            """
    @api.depends('pao_registration_number_id')
    def _generate_create_date_text(self):
        user = self.env.user
        user_tz = pytz.timezone(user.tz or 'UTC')
        now_utc = datetime.utcnow()
        now_user = pytz.utc.localize(now_utc).astimezone(user_tz)

        for rec in self:
            
            day = self.ordinal(now_user.date().day)
            rec.create_date_text = now_user.date().strftime(f"%B {day}, %Y")
            month_en = now_user.date().strftime("%B")
            month_es = self.MONTHS_ES.get(month_en, month_en)
            rec.create_date_spanish_text = now_user.date().strftime(f"a %d de {month_es}, %Y")
      
   
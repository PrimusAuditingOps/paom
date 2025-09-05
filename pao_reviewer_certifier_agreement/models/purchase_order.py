from odoo import fields, models, api, _
from werkzeug.urls import url_join
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.tools import format_date
import pytz
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    pao_show_reviewer_agreement = fields.Boolean(
        string="Show Reviewer Agreement", 
        compute="_get_show_reviewer_certifier_agreement", 
        store=True, 
        default= False
    )

    pao_show_certifier_agreement = fields.Boolean(
        string="Show Certifier Agreement", 
        compute="_get_show_reviewer_certifier_agreement", 
        store=True, 
        default= False
    )

    pao_reviewer_certifier_agreement_ids = fields.One2many(
        comodel_name='pao.reviewer.certifier.agreement',
        inverse_name='purchase_order_id',
        string='Agrements',
    )

    pao_certifier_agreement_count = fields.Integer(
        compute='_get_reviewer_certifier_agreements'
    )
    pao_reviewer_agreement_count = fields.Integer(
        compute='_get_reviewer_certifier_agreements'
    )
    pao_certifier_agreement_customer_id = fields.Many2one(
        'res.partner', 
        string="Customer",
        ondelete='set null',
    )


    @api.depends('pao_reviewer_certifier_agreement_ids')
    def _get_reviewer_certifier_agreements(self):
        for order in self:
            order.pao_certifier_agreement_count = len(order.pao_reviewer_certifier_agreement_ids.filtered(lambda l: l.document_type == "certifier"))
            order.pao_reviewer_agreement_count = len(order.pao_reviewer_certifier_agreement_ids.filtered(lambda l: l.document_type == "reviewer"))
    


    @api.depends('order_line','pao_reviewer_certifier_agreement_ids','pao_reviewer_certifier_agreement_ids.document_status')
    def _get_show_reviewer_certifier_agreement(self):
        for rec in self:
            rec.pao_show_reviewer_agreement = False 
            rec.pao_show_certifier_agreement = False
            
            if len(rec.order_line.filtered(lambda line: line.product_id.pao_agreement_reviewer)) > 0:
                if len(rec.pao_reviewer_certifier_agreement_ids.filtered(lambda l: l.document_type == "reviewer" and l.document_status == "sent")) <= 0:
                    rec.pao_show_reviewer_agreement = True 
            
            if len(rec.order_line.filtered(lambda line: line.product_id.pao_agreement_certifier)) > 0:
                if len(rec.pao_reviewer_certifier_agreement_ids.filtered(lambda l: l.document_type == "certifier" and l.document_status == "sent")) <= 0:
                    rec.pao_show_certifier_agreement = True  
    
    def send_certifier_agreement_action(self):
        self.ensure_one()
        agreement = self.create_reviewer_certifier_agreement("certifier")
        if agreement:

            return {
                'type': 'ir.actions.act_window',
                'name': agreement.title,
                'res_model': 'pao.reviewer.certifier.agreement',
                'view_mode': 'form',
                'res_id': agreement.id,
                'target': 'current',  
            }

    def send_reviewer_agreement_action(self):
        self.ensure_one()
        agreement = self.create_reviewer_certifier_agreement("reviewer")
        if agreement:

            return {
                'type': 'ir.actions.act_window',
                'name': agreement.title,
                'res_model': 'pao.reviewer.certifier.agreement',
                'view_mode': 'form',
                'res_id': agreement.id,
                'target': 'current',  
            }
        
        

    

    
    def create_reviewer_certifier_agreement(self,document_type):
        self.ensure_one() 
        template = ""
        subject = ""
        scheme_manager = None
        registration_number = None
        organization = None
        user = self.env.user
        user_tz = pytz.timezone(user.tz or 'UTC')
        now_utc = fields.Datetime.now()
        now_user = now_utc.astimezone(user_tz)
        current_date = now_user.date() 
        first_day = current_date.replace(day=1)
        last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)
        decision_end_date = current_date
        decision_start_date = current_date

        if document_type == "reviewer":
            template = "pao_reviewer_certifier_agreement.reviewer_agreement_template_mail"
            subject = "Revisiones mensuales"
        else:
            template = "pao_reviewer_certifier_agreement.certifier_agreement_template_mail"
            subject = "Toma de decisión"

        for l in self.order_line:
            if l.registrynumber_id.scheme_id.scheme_manager_mx_id and not registration_number:
                scheme_manager = l.registrynumber_id.scheme_id.scheme_manager_mx_id.id
                registration_number = l.registrynumber_id.id

            if l.organization_id and not organization:
                organization = l.organization_id.id
        
        if not registration_number or not organization:
            raise ValidationError(_("Please select an Organization or Registration Number."))
        
        agreement = self.env["pao.reviewer.certifier.agreement"].create(
            {
                "purchase_order_id": self.id,
                "signer_id": self.partner_id.id,
                "document_type": document_type,
                "document_status": "sent",
                "scheme_manager": scheme_manager,
                "start_date": first_day,
                "end_date":  last_day,
                "decision_end_date": decision_end_date + timedelta(days=7),
                "decision_start_date": decision_start_date,
                "organization_id": organization,
                "registration_number_id": registration_number,
                "customer_id": self.pao_certifier_agreement_customer_id.id,
            }
        )


        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = url_join(base_url, '/reviewercertifieragreement/sign/%s/%s' % (agreement.id, agreement.access_token))


        agreement.write({'sign_url': url})

        body =  self.env['ir.ui.view']._render_template(template, 
            {
                'record': agreement,
                'link': url,
            }
        )

        agreement.message_post(
            subject=subject,
            body=body,
            body_is_html = True,
            partner_ids=[self.partner_id.id],
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        agreement.message_subscribe(partner_ids=[self.partner_id.id])

        return agreement

    def action_view_reviewer_agreements(self):
        self.ensure_one()     
        action = {
            'res_model': 'pao.reviewer.certifier.agreement',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('pao_reviewer_certifier_agreement.pao_reviewer_certifier_agreement_view_tree').id, 'tree'), (self.env.ref('pao_reviewer_certifier_agreement.pao_reviewer_certifier_agreement_view_form').id, 'form')],
            'name': _("Reviewer Agreements - %s", self.name),
            'domain': [('purchase_order_id', '=', self.id), ('document_type', '=', 'reviewer')],
        }
        return action
    

    def action_view_certifier_agreements(self):
        self.ensure_one()     
        action = {
            'res_model': 'pao.reviewer.certifier.agreement',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('pao_reviewer_certifier_agreement.pao_reviewer_certifier_agreement_view_tree').id, 'tree'), (self.env.ref('pao_reviewer_certifier_agreement.pao_reviewer_certifier_agreement_view_form').id, 'form')],
            'name': _("Certifier Agreements - %s", self.name),
            'domain': [('purchase_order_id', '=', self.id), ('document_type', '=', 'certifier')],
        }
        return action
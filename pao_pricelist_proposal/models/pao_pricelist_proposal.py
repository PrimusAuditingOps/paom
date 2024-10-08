from odoo import models, fields, api, _
import uuid
from odoo.exceptions import ValidationError
import base64
import pytz
from datetime import datetime

class PriceListProposal(models.Model):

    _name="pao.pricelist.proposal"
    _inherit="product.pricelist"
    _description="PAO Pricelist Proposal Model"
    
    
    base_pricelist = fields.Many2one('product.pricelist', string="Base pricelist", readonly=True)
    
    create_employee_id = fields.Many2one('hr.employee', default= lambda self: self.create_uid.employee_id)
    
    origin_product_pricelist_id = fields.Many2one('product.pricelist', string="Product Price List Origin", readonly=True)
    
    country_group_ids = fields.Many2many('res.country.group', 'pao_pricelist_proposal_res_country_group_rel',
                        'pao_pricelist_proposal_id', 'res_country_group_id', string='Country Groups')

    item_ids = fields.One2many('product.proposal.item', 'pricelist_id', 'Pricelist Items')
    
    customer_id = fields.Many2one('res.partner', string="Customer")
    
    proposal_terms =  fields.Many2one('proposal.terms.schemes', string="Terms & Conditions")
    
    message_proposal_template_id = fields.Many2one('proposal.templates', string="Template")
    
    reject_reasons = fields.Char("Reject reasons", readonly=True)
    
    sign_date = fields.Date("Sign Date", readonly=True)
    
    proposal_status = fields.Selection(string="Status", default="draft", 
        selection=[
            ('draft', 'Draft'),
            ('authorized', 'Authorized'),
            ('sent', 'Sent'),
            ('accept', 'Accepted'),
            ('reject', 'Rejected'),
            ('cancel', 'Canceled'),
            ('complete', 'Completed')
        ]
    )
    
    access_token = fields.Char(
        'Access Token', 
        default=lambda self: self._get_access_token(),
        copy=False,
    )
    
    signature = fields.Binary(string='Signature Image')
    
    proposal_agreement_id = fields.Many2one('ir.attachment', string='Proposal Agreement')
    
    authorized = fields.Boolean(string="Is proposal authorized", default=False)
    
    authorization_request_sent = fields.Boolean(string="Authorization request sent", default=False, readonly=True)
    
    pricelist_proposal_manager_id = fields.Many2one('hr.employee', string="Pricelist Proposal Manager", readonly=True)
    
    base_url = fields.Char("Base URL", readonly=True)
    
    @api.model
    def _get_access_token(self):
        return uuid.uuid4().hex
    
    def request_approval(self):
        if not self.authorized:
            self._compare_base_pricelist_items()
            self.authorization_request_sent = True
            self.origin_product_pricelist_id.request_proposal_approval()
            
    def reset_draft_action(self):
        self.proposal_status = 'draft'
        self.authorized = False
        
    def _generate_pdf_report(self):
        self._compare_base_pricelist_items()
        return self.env.ref('pao_pricelist_proposal.report_proposal_agreement').report_action(self)
    
    def _compare_base_pricelist_items(self):
        for record in self:
            missing_items = []
            for item in record.item_ids:
                base_item = record.base_pricelist.item_ids.filtered(lambda base_item: base_item.product_tmpl_id.id == item.product_tmpl_id.id)
                
                if not base_item:
                    missing_items.append(item.name)
                    
            if len(missing_items) > 0:
                formatted_missing_items = " • " + "\n • ".join(missing_items)
                raise ValidationError(_("The following items were not found in the base pricelist (%(base_pricelist_name)s). To continue, please add them to the base pricelist:\n%(formatted_missing_items)s") 
                                    % {'base_pricelist_name': record.base_pricelist.name, 'formatted_missing_items': formatted_missing_items})
    
    def authorize_proposal_action(self):
        
        self._compare_base_pricelist_items()
        
        mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{self.create_uid.id}">@{self.create_uid.name}</a>'
        
        proposal_link = _('<a href="#" data-oe-model="pao.pricelist.proposal" data-oe-id="%(proposal_id)d">pricelist proposal</a>'
                        ) % {'proposal_id': self.id}

        message = _('Hello %(mention_html)s, the %(proposal_link)s has been authorized.'
                ) % {'proposal_link': proposal_link, 'mention_html': mention_html}
        
        self.origin_product_pricelist_id.notify_action(message)
        
        self.proposal_status = 'authorized'
        self.authorized = True
    
    def send_proposal_action(self):
        if self.authorized:
            
            self.pricelist_proposal_manager_id = self.env['hr.employee'].sudo().search([('pricelist_proposal_manager', '=', True), ('company_id', '=', self.env.company.id)], limit=1)
            
            if not self.pricelist_proposal_manager_id:
                raise ValidationError(_("No employee in charge of pricelist proposals was found."))
            
            if not self.pricelist_proposal_manager_id.es_sign_signature or not self.create_uid.employee_id.es_sign_signature:
                raise ValidationError(_("Please ensure that all employees involved in this process have a signature assigned in the Employees section."))
            
            self.access_token = self._get_access_token()
            
            return {
                'name': _('Send proposal'),
                'type': 'ir.actions.act_window',
                'res_model': 'send.pricelist.proposal',
                'view_mode': 'form',
                'view_id': self.env.ref('pao_pricelist_proposal.send_proposal_view_form').id,
                'target': 'new',
                'context': {
                    'default_pricelist_proposal_id': self.id,
                },
            }
            
    def set_reject_reasons(self, reasons):
        if self.proposal_status == 'sent':
            self.reject_reasons = reasons
            return True
        else:
            return False
    
    def reject_proposal_action(self):
        if self.proposal_status == 'sent' and self.reject_reasons:
            self.proposal_status = 'reject'
            self.origin_product_pricelist_id.existing_proposal = False
            
            mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{self.create_uid.id}">@{self.create_uid.name}</a>'
        
            proposal_link = _('<a href="#" data-oe-model="pao.pricelist.proposal" data-oe-id="%(proposal_id)d">pricelist proposal</a>'
                            ) % {'proposal_id': self.id}
            
            reasons = ('<br/><b>%(reasons)s</b>') % {'reasons':  self.reject_reasons}

            message = _('Hello %(mention_html)s, the %(proposal_link)s has been rejected due the following reasons: %(reasons)s'
                    ) % {'proposal_link': proposal_link, 'mention_html': mention_html, 'reasons': reasons}
            
            self.origin_product_pricelist_id.notify_action(message)
            
            return True
        else:
            return False
    
    def cancel_proposal_action(self):
        self.proposal_status = 'cancel'
        self.origin_product_pricelist_id.existing_proposal = False
            
    def accept_proposal_action(self):
        if self.proposal_status == 'sent':
            self.proposal_status = 'accept'
            
            requested_tz = pytz.timezone('America/Mexico_City')
            today = requested_tz.fromutc(datetime.utcnow())
            self.sign_date = today.date()
            
            mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{self.create_uid.id}">@{self.create_uid.name}</a>'
        
            proposal_link = _('<a href="#" data-oe-model="pao.pricelist.proposal" data-oe-id="%(proposal_id)d">pricelist proposal</a>'
                            ) % {'proposal_id': self.id}

            message = _('Hello %(mention_html)s, the %(proposal_link)s of %(pricelist_name)s has been accepted'
                    ) % {'proposal_link': proposal_link, 'mention_html': mention_html, 'pricelist_name': self.origin_product_pricelist_id.name}
            
            attachment = self._generate_proposal_agreement()
            
            self.origin_product_pricelist_id.notify_action(message, attachment)
            
            return True
        else:
            return False
    
    def complete_proposal_action(self):
        if self.proposal_status == 'accept':
            self.name = _('Pricelist Agreement') + " - " + self.origin_product_pricelist_id.name
            self.proposal_status = 'complete'
            
            self.origin_product_pricelist_id.pricelist_agreement_id = self.id
            
            self.origin_product_pricelist_id.existing_proposal = False
            
            items_data = []
            for line in self.item_ids:
                one2many_vals = {}
                for line_field_name, line_field in line._fields.items():
                    if line_field_name != 'id':
                        field_value = getattr(line, line_field_name)
                        if isinstance(line_field, fields.Many2one):
                            one2many_vals[line_field_name] = field_value.id if field_value else False
                        else:
                            one2many_vals[line_field_name] = field_value
                one2many_vals['pricelist_id'] = self.origin_product_pricelist_id.id
                items_data.append((0, 0, one2many_vals))
            
            self.origin_product_pricelist_id.item_ids.unlink()
            self.origin_product_pricelist_id.item_ids = items_data
            
            self._notify_new_pricelist()
    
    def get_current_base_pricelist(self):
        return self.base_pricelist
    
    def _notify_new_pricelist(self):
        
        message=_('The pricelist %(pricelist_name)s has been updated.') % {'pricelist_name': self.origin_product_pricelist_id.name}
        channels=('Operaciones', 'Finanzas', 'Relaciones Comerciales', 'Cobranza')
        
        self.customer_id.message_post(
            body=message,
            # partner_ids=channel.channel_partner_ids.ids,
        )
        
        odoo_bot = self.env.ref('base.partner_root')
        
        for channel_name in channels:
            channel = self.env['discuss.channel'].search([('name', 'ilike', channel_name)]) 
            if channel:
                channel.sudo().message_post(body=message, message_type='comment', subtype_xmlid='mail.mt_comment', author_id=odoo_bot.id)
                # notification = ('<a href="#" data-oe-model="pao.customer.registration" class="o_redirect" data-oe-id="%s">#%s</a>') % (cr_sudo.id, cr_sudo.res_partner_id.name,)
            
    def _generate_proposal_agreement(self):
        
        customer_lang = self.customer_id.lang if self.customer_id else self.create_uid.lang
        context = {'lang': customer_lang}
        
        pdf = self.env['ir.actions.report'].sudo().with_context(context)._render_qweb_pdf(
            'pao_pricelist_proposal.report_proposal_agreement',
            self.ids,
        )[0]
        
        attachment = self.env['ir.attachment'].sudo().create({
            'name': _('Pricelist proposal agreement'),
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'res_model': 'product.pricelist',
            'res_id': self.origin_product_pricelist_id.id
        })

        self.proposal_agreement_id = attachment.id
        
        return attachment

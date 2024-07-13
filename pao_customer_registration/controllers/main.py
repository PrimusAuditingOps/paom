
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from logging import getLogger
from werkzeug.urls import url_join
import base64
import pytz
import werkzeug
import json
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
_logger = getLogger(__name__)
 
class WebsitePaoAuditorRegistration(portal.CustomerPortal):
    
    @http.route(['/pao/customer/registration/<int:cr_id>/<string:cr_token>'], type='http', auth="public", website=True)
    def customer_registration_form(self,cr_id=False, cr_token=None, **kwargs):

        try:
            cr_sudo = self._document_check_access('pao.customer.registration', cr_id, access_token=cr_token)
        except (AccessError, MissingError):
            return request.redirect('/')

        if cr_sudo.request_status in ["complet", "done"]:
            return request.render("pao_customer_registration.pao_customer_registration_completed_page_view", {})        
        elif cr_sudo.request_status == "sent":
            countries = request.env['res.country'].search([])
            states = request.env['res.country.state'].search([])
            cities = request.env['res.city'].sudo().search([])
            lang = cr_sudo.res_partner_id.lang or cr_sudo.create_uid.lang
            fiscal_regime = request.env['res.partner'].sudo().with_context(lang=lang)._fields['l10n_mx_edi_fiscal_regime'].selection
            return request.render("pao_customer_registration.pao_customer_registration", 
                {
                    "data": cr_sudo, 
                    "fiscal_regime": fiscal_regime,
                    "countries": countries, 
                    "states": states, 
                    "cities": cities,
                    "token": cr_token,
                    "id": cr_id
                }
            )
        else:
            return request.render("pao_customer_registration.pao_customer_registration_exception_page_view", {})

        
    """
    @http.route(['/pao/customer/registration/send/<string:model_name>'], type='http', auth='public', methods=['POST','GET'], sitemap=True, website=True)
    def customer_registration_send(self,model_name, cr_token, cr_id, company, rfc, phonenumber, email, street, zip, country, state, 
    city, cfdiuse,contacts=False, asesor =False, **kwargs):
    
        try:
            cr_sudo = self._document_check_access('pao.customer.registration', int(cr_id), access_token=str(cr_token))
        except (AccessError, MissingError):
            return request.redirect('/')
        contact_list = []
        if contacts:
            contact_list = json.loads(contacts)

        if cr_sudo.request_status in ["complet", "done"]:
            
            return request.redirect('/pao/customer/registration/status/3')
        
        elif cr_sudo.request_status == "sent":
            IrAttachment = request.env['ir.attachment'].sudo()
            filename = "%s-%s.%s" % ("constanciafiscal",company, "pdf")
            attachment = IrAttachment.create({
                'name': filename,
                'datas': base64.b64encode(kwargs.get("attachments[0][0]").read()),
                'res_model': 'pao.customer.registration',
                'res_id': cr_sudo.id,
            })

            filename = "%s-%s.%s" % ("ComprobanteDomicilio",company, "pdf")
            attachment_address = IrAttachment.create({
                'name': filename,
                'datas': base64.b64encode(kwargs.get("attachments_proof_of_address[1][0]").read()),
                'res_model': 'pao.customer.registration',
                'res_id': cr_sudo.id,
            })

            filename = "%s-%s.%s" % ("CuentaBancaria",company, "pdf")
            attachment_bank = IrAttachment.create({
                'name': filename,
                'datas': base64.b64encode(kwargs.get("attachments_bank_account[2][0]").read()),
                'res_model': 'pao.customer.registration',
                'res_id': cr_sudo.id,
            })

            filename = "%s-%s.%s" % ("SAT",company, "pdf")
            attachment_sat = IrAttachment.create({
                'name': filename,
                'datas': base64.b64encode(kwargs.get("attachments_sat[3][0]").read()),
                'res_model': 'pao.customer.registration',
                'res_id': cr_sudo.id,
            })
            
            
            cr_sudo.write({
                "name": company,
                "vat": rfc,
                "country_id": int(country),
                "state_id": int(state),
                "city_id": int(city),
                "street_name": street,
                "zip": zip,
                "phone": phonenumber,
                "email": email,
                "fiscal_regime": cfdiuse,
                "attachment_id": attachment.id,
                "attachment_proof_of_address_id": attachment_address.id,
                "attachment_bank_account_id": attachment_bank.id,
                "attachment_sat_compliance_opinion_id": attachment_sat.id,
                "request_status": "complet",
                "asesor": asesor,
            })
            request.env['pao.customer.registration.contact'].sudo().search([('customer_registration_id', '=', cr_sudo.id)]).unlink()
            if len(contact_list) > 0:

                contact = request.env['pao.customer.registration.contact'].sudo()
                for line in contact_list:
                    contact.create({
                        "name": line["name"],
                        "phone": line["phone"],
                        "email": line["email"],
                        "occupation": line["occupation"],
                        "customer_registration_id": cr_sudo.id,
                    })
            channel_id = request.env['discuss.channel'].sudo().search([('name', 'ilike', "Actualización Catálogos")]) 
            if channel_id:
                notification = ('<a href="#" data-oe-model="pao.customer.registration" class="o_redirect" data-oe-id="%s">#%s</a>') % (cr_sudo.id, cr_sudo.res_partner_id.name,)
                channel_id.message_post(body=_('Customer registration has been completed: ') + notification, message_type='comment', subtype_xmlid='mail.mt_comment')
            _logger.error("ahorro")
            return request.redirect('/')
        else:
            _logger.error("ahorro2")
            return request.redirect('/pao/customer/registration/status/2')
    
    
    """
    @http.route(['/pao/customer/registration/send'], type='json', auth='public', website=True)
    def customer_registration_send(self, cr_token, cr_id, company, rfc, phonenumber, email, street, zip, country, state, 
    city, cfdiuse,attachments, attachments_proof_of_address, attachments_bank_account, attachments_sat, contacts=False, asesor =False, **kwargs):
        
    
        try:
            cr_sudo = self._document_check_access('pao.customer.registration', int(cr_id), access_token=str(cr_token))
        except (AccessError, MissingError):
            return '/'
        contact_list = []
        if contacts:
            contact_list = json.loads(contacts)

        if cr_sudo.request_status in ["complet", "done"]:
            return '/pao/customer/registration/status/3'
        
        elif cr_sudo.request_status == "sent":
        
            IrAttachment = request.env['ir.attachment'].sudo()
            filename = "%s-%s.%s" % ("constanciafiscal",company, "pdf")
            attachment = IrAttachment.create({
                'name': filename,
                'datas': attachments,
                'res_model': 'pao.customer.registration',
                'res_id': cr_sudo.id,
            })

            filename = "%s-%s.%s" % ("ComprobanteDomicilio",company, "pdf")
            attachment_address = IrAttachment.create({
                'name': filename,
                'datas': attachments_proof_of_address,
                'res_model': 'pao.customer.registration',
                'res_id': cr_sudo.id,
            })

            filename = "%s-%s.%s" % ("CuentaBancaria",company, "pdf")
            attachment_bank = IrAttachment.create({
                'name': filename,
                'datas': attachments_bank_account,
                'res_model': 'pao.customer.registration',
                'res_id': cr_sudo.id,
            })

            filename = "%s-%s.%s" % ("SAT",company, "pdf")
            attachment_sat = IrAttachment.create({
                'name': filename,
                'datas': attachments_sat,
                'res_model': 'pao.customer.registration',
                'res_id': cr_sudo.id,
            })
            
            cr_sudo.write({
                "name": company,
                "vat": rfc,
                "country_id": int(country),
                "state_id": int(state),
                "city_id": int(city),
                "street_name": street,
                "zip": zip,
                "phone": phonenumber,
                "email": email,
                "fiscal_regime": cfdiuse,
                "attachment_id": attachment.id,
                "attachment_proof_of_address_id": attachment_address.id,
                "attachment_bank_account_id": attachment_bank.id,
                "attachment_sat_compliance_opinion_id": attachment_sat.id,
                "request_status": "complet",
                "asesor": asesor,
            })
            request.env['pao.customer.registration.contact'].sudo().search([('customer_registration_id', '=', cr_sudo.id)]).unlink()
            if len(contact_list) > 0:

                contact = request.env['pao.customer.registration.contact'].sudo()
                for line in contact_list:
                    contact.create({
                        "name": line["name"],
                        "phone": line["phone"],
                        "email": line["email"],
                        "occupation": line["occupation"],
                        "customer_registration_id": cr_sudo.id,
                    })
            
                
            return '/pao/customer/registration/status/1'
        else:
            return '/pao/customer/registration/status/2'
    

    @http.route('/pao/customer/registration/status/<int:status>', type='http', auth='public', website=True)
    def customer_registration_status(self, status, **kwargs):
        
        if status == 1:
            return request.render("pao_customer_registration.pao_customer_registration_finish_page_view", {})
        elif status == 2:
            return request.render("pao_customer_registration.pao_customer_registration_exception_page_view", {})
        else:
            return request.render("pao_customer_registration.pao_customer_registration_completed_page_view", {})  
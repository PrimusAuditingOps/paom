
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from logging import getLogger
from werkzeug.urls import url_join
import base64
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

_logger = getLogger(__name__)

class CustomerPortal(portal.CustomerPortal):

    
    @http.route(['/reviewercertifieragreement/sign/<int:agreement_id>/<string:agreement_token>/accept'], type='json', auth="public", website=True)
    def portal_reviewer_certifier_agreement_accept(self, agreement_id, agreement_token, name=None, signature=None):
        try:
            agreement_sudo = self._document_check_access('pao.reviewer.certifier.agreement', agreement_id, access_token=agreement_token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        
        lang = agreement_sudo.signer_id.lang or agreement_sudo.create_uid.lang
        agreement_sudo.with_context(lang=lang)
        zone = agreement_sudo.create_uid.tz
        requested_tz = pytz.timezone(zone)
        today = requested_tz.fromutc(datetime.utcnow())

        signature_date = today
        agreement_sudo.write({"signature": signature, "signature_name": name, "signature_date": signature_date})
       
        filename = "%s.%s" % (agreement_sudo.title, "pdf")
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf('pao_reviewer_certifier_agreement.report_reviewer_certifier_agreements', [agreement_id], data= {"values": agreement_sudo, "print": True})[0]
        attachment = request.env['ir.attachment'].sudo().create({
                'name': filename,
                'datas': base64.b64encode(pdf),
                'res_model': 'pao.reviewer.certifier.agreement',
                'res_id': agreement_id,
                'type': 'binary',
            })
        
        agreement_sudo.write({"attachment_id": attachment.id, "document_status": "done"})
        message=_('The agreement has been signed.')
        agreement_sudo.notify_agreement_accept(message)
       
        return {
            'force_refresh': True,
            'redirect_url': '/reviewercertifieragreement/download/%s/%s' % (agreement_id, agreement_token)
        }
      
    @http.route(['/reviewercertifieragreement/download/<int:agreement_id>/<string:agreement_token>'], type='http', auth="public", website=True)
    def portal_reviewer_certifier_agreement_download(self, report_type=None, agreement_id=False, agreement_token=None, download=False, **kw):
        
        try:
            agreement_sudo = self._document_check_access('pao.reviewer.certifier.agreement', agreement_id, access_token=agreement_token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        if agreement_sudo.document_status != "done":
            return request.render('pao_reviewer_certifier_agreement.pao_reviewer_certifier_exception_page_view', {})
       
        documents = []
        url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') 
        
        if not agreement_sudo.attachment_id.access_token:
            token = agreement_sudo.attachment_id._generate_access_token()
            agreement_sudo.attachment_id.write({"access_token": token})
            documents.append({"name": agreement_sudo.attachment_id.name, "url": url+"/web/content/"+str(agreement_sudo.attachment_id.id)+"?download=true&access_token="+str(agreement_sudo.attachment_id.access_token)})
        
            

        
        return request.render('pao_reviewer_certifier_agreement.certifier_reviewer_download_portal', {"agreement": agreement_sudo, "documents": documents})


    @http.route(['/reviewercertifieragreement/sign/<int:agreement_id>/<string:agreement_token>'], type='http', auth="public", website=True)
    def portal_reviewer_certifier_agreement_sign(self, report_type=None, agreement_id=False, agreement_token=None, download=False, **kw):
        
        try:
            agreement_sudo = self._document_check_access('pao.reviewer.certifier.agreement', agreement_id, access_token=agreement_token)
        except (AccessError, MissingError):
            return request.redirect('/')

      
        if agreement_sudo.document_status != "sent":
            return request.render('pao_reviewer_certifier_agreement.pao_reviewer_certifier_exception_page_view', {})

        url = '/reviewercertifieragreement/sign/' + str(agreement_id) + '/' + agreement_token + '/accept'
      

        
        return request.render('pao_reviewer_certifier_agreement.pao_agreement_portal_template', {"agreement": agreement_sudo, "print": False, "urlAccept": url})



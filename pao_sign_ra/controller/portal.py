import logging

from odoo import http
from odoo.http import request
import pytz
from datetime import datetime
from odoo.tools.translate import _
from odoo.tools.misc import get_lang
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal

_logger = logging.getLogger(__name__)

class SignRAPortal(CustomerPortal):

    @http.route('/ra_request/accept/<int:id>/<string:token>', type='http', auth='public', website=True)
    def ra_request_portal(self, id, token):
        try:
            ra_document = self._document_check_access('ra.document', id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        if ra_document.status != 'sent':
            # ADD MISSING PARAMETERS...DOWNLOAD, ETC
            return request.render('pao_sign_ra.process_complete_ra_request_portal_view', {'ra_status': ra_document.status})
        else:
            if ra_document.request_travel_expenses and not ra_document.travel_expenses_posted:
                return request.redirect('/ra_request/travel_expenses/'+str(id)+'/'+str(token))
            else:
                return request.redirect('/ra_request/sign/'+str(id)+'/'+str(token))
    
    @http.route('/ra_request/travel_expenses/<int:id>/<string:token>', type='http', auth='public', website=True)
    def ra_travel_expenses_view_portal(self, id, token):
        try:
            ra_document = self._document_check_access('ra.document', id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        submit_travel_expenses_link = '/ra_request/submit_travel_expenses/'+str(id)+'/'+str(token)
        return request.render('pao_sign_ra.travel_expenses_portal_view', {'submit_travel_expenses_link': submit_travel_expenses_link})
    
    
    @http.route('/ra_request/sign/<int:id>/<string:token>', type='http', auth='public', website=True)
    def ra_sign_view_portal(self, id, token):
        try:
            ra_document = self._document_check_access('ra.document', id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        accept_link = '/ra_request/submit_sign/'+str(id)+'/'+str(token)
        return request.render('pao_sign_ra.sign_ra_preview_portal_view', {'accept_link': accept_link})
    
    @http.route('/ra_request/submit_travel_expenses/<int:id>/<string:token>', type='http', methods=['POST'], auth='public', website=True)
    def ra_travel_expenses_submit_portal(self, id, token, **kwargs):
        try:
            ra_document = self._document_check_access('ra.document', id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        travel_expenses = kwargs.get('travel_expenses')
        
        _message_post_helper(
            'purchase.order', ra_document.purchase_order_id.id, _('Travel Expenses: %s') % (travel_expenses),
            attachments=[],
            **({'token': token} if token else {})).sudo()
        
        ra_document.write({'travel_expenses_posted': True})
        
        return request.redirect('/ra_request/sign/'+str(id)+'/'+str(token))
    
    @http.route('/ra_request/submit_sign/<int:id>/<string:token>', type='http', methods=['POST'], auth='public', website=True)
    def ra_sign_submit_portal(self, id, token):
        try:
            ra_document = self._document_check_access('ra.document', id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        ra_document.write({'status': 'sign'})
        return request.render('pao_sign_ra.process_complete_ra_request_portal_view', {'ra_status': ra_document.status})
        
    # @http.route('/sign_ra/<string:token>/<string:idresponse>', type='http', auth="public", website=True)
    # def action_confirm_audit(self, token, idresponse, **kwargs):
        
    #     purchaseconfirmation = request.env['auditconfirmation.purchaseconfirmation'].sudo().search(['&',('ac_access_token', '=', token),'|',('ac_consumed','=',False),('ac_audit_confirmation_status','=', '3')])
    #     if not purchaseconfirmation or idresponse not in ('1','2','3'): 
    #         return request.not_found()
    #     purchase =  request.env['purchase.order'].sudo().search([('id', '=', purchaseconfirmation.ac_id_purchase)])
        
    #     lang = purchase.partner_id.lang or get_lang(request.env).code
    #     access_token = purchase._portal_ensure_token()
    #     if idresponse == '1':
    #         if purchase.ac_request_travel_expenses and not purchaseconfirmation.ac_consumed_travel_expenses:   
    #             pageredirect = "/response/travel/expenses?access_token="+access_token+"&number="+str(purchase.id)+"&ra_verification=1"
    #             return request.redirect(pageredirect)
    #         else:
    #             return request.env['ir.ui.view'].with_context(lang=lang)._render_template('auditconfirmation.external_auditor_sign_portal_view', 
    #             {
    #                 'signer': purchase.partner_id.name,
    #                 'urlAccept': purchase.get_portal_url(suffix='/accept/audit'),
    #                 "serviceagreement": purchaseconfirmation,
    #                 "documents": documents
    #             })
    #     else:
    #         return request.env['ir.ui.view'].with_context(lang=lang)._render_template('auditconfirmation.audit_rejected_external_page_view', 
    #         {
    #             'urlrejected': purchase.get_portal_url(suffix='/decline/audit'),
    #         })
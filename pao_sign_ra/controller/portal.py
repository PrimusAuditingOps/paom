import logging

from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from werkzeug.urls import url_join
import base64

_logger = logging.getLogger(__name__)

class SignRAPortal(portal.CustomerPortal):

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
        
        # _message_post_helper(
        #     'purchase.order', ra_document.purchase_order_id.id, _('Travel Expenses: %s') % (travel_expenses),
        #     attachments=[],
        #     **({'token': token} if token else {})).sudo()
        
        ra_document.write({'travel_expenses_posted': True})
        
        return request.redirect('/ra_request/sign/'+str(id)+'/'+str(token))
    
    @http.route('/ra_request/submit_sign/<int:id>/<string:token>', type='json', auth='public', website=True)
    def ra_sign_submit_portal(self, id, token):
        try:
            ra_document = self._document_check_access('ra.document', id, access_token=token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        ra_document.write({'status': 'sign'})
        return request.render('pao_sign_ra.process_complete_ra_request_portal_view', {'ra_status': ra_document.status})
    
    # @http.route(['/pricelist_proposal/<int:id>/<string:token>/accept'], type='json', auth="public", website=True)
    # def proposal_portal_accept(self, id, token, signature):
    #     if not signature:
    #         redirect_link = '/pricelist_proposal/%s/%s' % (id, token)
    #         return request.redirect(redirect_link)
        
    #     try:
    #         proposal_sudo = self._document_check_access('pao.pricelist.proposal', id, access_token=token)
    #     except (AccessError, MissingError):
    #         return request.redirect('/')
        
    #     proposal_sudo.signature = signature
    #     accept_proposal = proposal_sudo.accept_proposal_action()
        
    #     if accept_proposal:
    #         base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #         redirect_link = url_join(base_url, '/pricelist_proposal/%s/%s' % (id, token))
    #         return {
    #             'force_refresh': True,
    #             'redirect_url':  redirect_link
    #         }
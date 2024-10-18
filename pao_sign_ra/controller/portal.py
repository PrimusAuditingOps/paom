import logging
from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.mail import _message_post_helper
from datetime import datetime
import pytz
import base64

_logger = logging.getLogger(__name__)

class SignRAPortal(portal.CustomerPortal):

    def _get_ra_document(self, model, id, token):
        """Utility method to retrieve the RA document and handle access errors."""
        try:
            return self._document_check_access(model, id, access_token=token)
        except (AccessError, MissingError):
            return None

    def _redirect_to(self, endpoint, id, token):
        """Utility method to simplify redirection with formatted URL."""
        return request.redirect(f'/ra_request/{endpoint}/{id}/{token}')
    
    
    

    '''Method to redirect to the appropriate step'''
    
    @http.route('/ra_request/accept/<int:id>/<string:token>', type='http', auth='public', website=True)
    def ra_request_portal(self, id, token):
        ra_document = self._get_ra_document('ra.document', id, token)
        if not ra_document:
            return request.redirect('/')
        
        if ra_document.status != 'sent':
            # ADD MISSING PARAMETERS...DOWNLOAD, ETC
            return request.render('pao_sign_ra.process_complete_ra_request_portal_view', {
                'ra_status': ra_document.status
            })
        
        if ra_document.request_travel_expenses and not ra_document.travel_expenses_posted:
            return self._redirect_to('travel_expenses', id, token)
        else:
            return self._redirect_to('sign', id, token)
        
        
        
        
        

    '''Methods for handling the travel expenses form'''
    
    @http.route('/ra_request/travel_expenses/<int:id>/<string:token>', type='http', auth='public', website=True)
    def ra_travel_expenses_view_portal(self, id, token):
        ra_document = self._get_ra_document('ra.document', id, token)
        if not ra_document:
            return request.redirect('/')
        
        if ra_document.request_travel_expenses and not ra_document.travel_expenses_posted:
            submit_travel_expenses_link = f'/ra_request/submit_travel_expenses/{id}/{token}'
            return request.render('pao_sign_ra.travel_expenses_portal_view', {
                'submit_travel_expenses_link': submit_travel_expenses_link
            })
        else:
            return self._redirect_to('accept', id, token)

    @http.route('/ra_request/submit_travel_expenses/<int:id>/<string:token>', type='http', methods=['POST'], auth='public', website=True)
    def ra_travel_expenses_submit_portal(self, id, token, **kwargs):
        ra_document = self._get_ra_document('ra.document', id, token)
        if not ra_document:
            return request.redirect('/')
        
        travel_expenses = kwargs.get('travel_expenses')
        po_token = ra_document.purchase_order_id._portal_ensure_token()
        
        _message_post_helper(
            'purchase.order', ra_document.purchase_order_id.id, _('Travel Expenses: %s') % travel_expenses,
            attachments=[],
            **({'token': po_token} if po_token else {})
        ).sudo()

        ra_document.write({'travel_expenses_posted': True})
        
        return self._redirect_to('sign', id, token)
    
    
    
    
    

    '''Methods for handling the RA signature form'''
    
    def _generate_ra_pdf(self, ra_document):
        """Generates the RA PDF using the existing report template."""
        pdf_content, content_type = request.env.ref('servicereferralagreement.report_rapurchaseorder')._render_qweb_pdf([ra_document.purchase_order_id])
        return base64.b64encode(pdf_content).decode('utf-8')
    
    @http.route('/ra_request/sign/<int:id>/<string:token>', type='http', auth='public', website=True)
    def ra_sign_view_portal(self, id, token):
        ra_document = self._get_ra_document('ra.document', id, token)
        if not ra_document:
            return request.redirect('/')
        
        if ra_document.request_travel_expenses and not ra_document.travel_expenses_posted:
            return self._redirect_to('accept', id, token)
        else:
            pdf_data = self._generate_ra_pdf(ra_document)
            accept_link = f'/ra_request/submit_sign/{id}/{token}'
            return request.render('pao_sign_ra.sign_ra_preview_portal_view', {
                'accept_link': accept_link,
                'pdf_preview_data': pdf_data
            })

    @http.route('/ra_request/submit_sign/<int:id>/<string:token>', type='json', methods=['POST'], auth='public', website=True)
    def ra_sign_submit_portal(self, id, token, signature, name):
        ra_document = self._get_ra_document('ra.document', id, token)
        if not ra_document:
            return request.redirect('/')
        
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        
        ra_document.write({'status': 'sign'})
        
        _logger.warning(name)
        
        if ra_document.purchase_order_id.ac_audit_confirmation_status == '0':
            ra_document.purchase_order_id.write({'ac_audit_confirmation_status': '1', 'sra_audit_signature': signature, 'sra_audit_signature_name': name, 'sra_audit_signature_date':today})

        return {
            'force_refresh': True,
            'redirect_url': f'/ra_request/accept/{id}/{token}'
        }

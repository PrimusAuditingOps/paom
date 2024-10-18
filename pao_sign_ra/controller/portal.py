import logging
from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.web.controllers.main import content_disposition
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
        
        if ra_document.status == 'sign':
            pdf_data = self._generate_ra_preview(ra_document)
            download_link = f'/sign_ra/download_ra/{ra_document.purchase_order_id.id}/{token}'
            return request.render('pao_sign_ra.sign_ra_preview_portal_view', {
                'download_link': download_link,
                'pdf_preview_data': pdf_data,
                'purchase_order': ra_document.purchase_order_id,
                'ra_status': ra_document.status
            })
        elif ra_document.status != 'sent':
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
        
        message=_('The auditor has submitted their travel expenses: %s') % travel_expenses
        ra_document.purchase_order_id.notify_ra_request_progress(message)
        ra_document.write({'travel_expenses_posted': True})
        
        return self._redirect_to('sign', id, token)
    
    
    
    
    

    '''Methods for handling the RA signature form'''
    
    def _generate_ra_preview(self, ra_document):
        """Generates the RA PDF using the existing report template."""
        pdf_content = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'servicereferralagreement.report_rapurchaseorder',
            ra_document.purchase_order_id.id,
        )[0]
        return base64.b64encode(pdf_content).decode('utf-8')
    
    @http.route('/ra_request/sign/<int:id>/<string:token>', type='http', auth='public', website=True)
    def ra_sign_view_portal(self, id, token):
        ra_document = self._get_ra_document('ra.document', id, token)
        if not ra_document:
            return request.redirect('/')
        
        if ra_document.request_travel_expenses and not ra_document.travel_expenses_posted:
            return self._redirect_to('accept', id, token)
        else:
            pdf_data = self._generate_ra_preview(ra_document)
            accept_link = f'/ra_request/submit_sign/{id}/{token}'
            return request.render('pao_sign_ra.sign_ra_preview_portal_view', {
                'accept_link': accept_link,
                'pdf_preview_data': pdf_data,
                'purchase_order': ra_document.purchase_order_id,
                'ra_status': ra_document.status
            })

    @http.route('/ra_request/submit_sign/<int:id>/<string:token>', type='json', methods=['POST'], auth='public', website=True)
    def ra_sign_submit_portal(self, id, token, signature, name):
        ra_document = self._get_ra_document('ra.document', id, token)
        if not ra_document:
            return request.redirect('/')
        
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        
        auditconfirmation = request.env['auditconfirmation.purchaseconfirmation'].sudo().search([('ac_id_purchase','=',ra_document.purchase_order_id.id)])
        
        if auditconfirmation and auditconfirmation.ac_audit_confirmation_status == '0':
            auditconfirmation.write({'ac_audit_confirmation_status': '1'})
            ra_document.purchase_order_id.write({'sra_audit_signature': signature, 'sra_audit_signature_name': name, 'sra_audit_signature_date':today})
        
        pdf_content = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'servicereferralagreement.report_rapurchaseorder',
            ra_document.purchase_order_id.id,
        )[0]

        # Create an attachment record
        attachment = request.env['ir.attachment'].sudo().create({
            'name': 'Referral Agreement - %s.pdf' % ra_document.name,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'ra.document',  # Replace with your model name
            'res_id': ra_document.id,  # The record ID to which the attachment belongs
            'mimetype': 'application/pdf',
        })

        # Update the record's attachment_ids
        ra_document.write({
            'attachment_ids': [(4, attachment.id)],
            'status': 'sign'
        })
        
        message=_('The auditor has signed and accepted the RA.')
        ra_document.purchase_order_id.notify_ra_request_progress(message)
        

        return {
            'force_refresh': True,
            'redirect_url': f'/ra_request/accept/{id}/{token}'
        }
        
        
        
        
        
    '''Method to download RA'''
    
    @http.route('/sign_ra/download_ra/<int:id>/<string:token>', type='http', auth="public", website=True)
    def download_ra(self, id, token, **kwargs):
        ra_document = self._get_ra_document('ra.document', id, token)
        if not ra_document:
            return request.redirect('/')

        order_sudo = request.env['purchase.order'].sudo().search([('id', '=', id)])
        rafilename = 'RA-'+order_sudo.name+'-'+order_sudo.partner_id.name+'.pdf'
        
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'servicereferralagreement.report_rapurchaseorder',
            id,
        )[0]
        
        return request.make_response(pdf, [('Content-Type', 'application/octet-stream'), ('Content-Disposition', content_disposition(rafilename))])

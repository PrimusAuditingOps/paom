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

class ConfirmPurchase(CustomerPortal):

    @http.route('/confirm/<string:token>/<string:idresponse>', type='http', auth="public", website=True)
    def action_confirm_audit(self, token, idresponse, **kwargs):
        #assert idresponse in ('1','2'), "Incorrect id"
        purchaseconfirmation = request.env['auditconfirmation.purchaseconfirmation'].sudo().search(['&',('ac_access_token', '=', token),'|',('ac_consumed','=',False),('ac_audit_confirmation_status','=', '3')])
        if not purchaseconfirmation or idresponse not in ('1','2','3'): 
            return request.not_found()
        purchase =  request.env['purchase.order'].sudo().search([('id', '=', purchaseconfirmation.ac_id_purchase)])
        notice = ""
        if purchase.ac_request_travel_expenses:
            notice = _("After agreeing and signing, you will be prompted to enter travel expenses.")
        #request.env.cr.commit()
        lang = purchase.partner_id.lang or get_lang(request.env).code
        if idresponse == '1':
            return request.env['ir.ui.view'].with_context(lang=lang)._render_template('auditconfirmation.audit_confirmation_external_page_view', 
            {
                'signname': purchase.partner_id.name,
                'urlconfirm': purchase.get_portal_url(suffix='/accept/audit'),
                'notice': notice
            })
        else:
            return request.env['ir.ui.view'].with_context(lang=lang)._render_template('auditconfirmation.audit_rejected_external_page_view', 
            {
                'urlrejected': purchase.get_portal_url(suffix='/decline/audit'),
            })
            
    
    @http.route('/confirm/external/audit/<string:token>/<string:idresponse>', type='http', auth="public", website=True)
    def action_confirm_external_audit(self, token, idresponse, **kwargs):
        #assert idresponse in ('1','2'), "Incorrect id"
        purchaseconfirmation = request.env['auditconfirmation.purchaseconfirmation'].sudo().search(['&',('ac_access_token', '=', token),'|',('ac_consumed','=',False),('ac_audit_confirmation_status','=', '3')])
        if not purchaseconfirmation or idresponse not in ('1','2','3'): 
            return request.not_found()
        
        purchase =  request.env['purchase.order'].sudo().search([('id', '=', purchaseconfirmation.ac_id_purchase)])
        purchaseconfirmation.write({'ac_audit_confirmation_status': '1', 'ac_consumed': True})
        purchase.write({'ac_audit_confirmation_status': '1'})
        access_token = purchase._portal_ensure_token()
        if purchase.ac_request_travel_expenses:   
            pageredirect = "/response/travel/expenses?access_token="+access_token+"&number="+str(purchase.id)
        else:
            pageredirect = "/response/message"
         
        _message_post_helper(
            'purchase.order', purchase.id, _('The auditor has accepted the audit.'),
            attachments=[],
            **({'token': access_token} if access_token else {})).sudo()
        request.env.cr.commit()
        
        return request.redirect(pageredirect)
    
    @http.route('/confirm/tentatively/audit/<string:token>/<string:idresponse>', type='http', auth="public", website=True)
    def action_confirm_tentative_audit(self, token, idresponse, **kwargs):
        #assert idresponse in ('1','2'), "Incorrect id"
        purchaseconfirmation = request.env['auditconfirmation.purchaseconfirmation'].sudo().search(['&',('ac_access_token', '=', token),'|',('ac_consumed','=',False),('ac_audit_confirmation_status','=', '3')])
        if not purchaseconfirmation or idresponse not in ('1','2','3'): 
            return request.not_found()
        
        purchase =  request.env['purchase.order'].sudo().search([('id', '=', purchaseconfirmation.ac_id_purchase)])
        purchaseconfirmation.write({'ac_audit_confirmation_status': '3', 'ac_consumed': True})
        purchase.write({'ac_audit_confirmation_status': '3'})
        access_token = purchase._portal_ensure_token()
        if purchase.ac_request_travel_expenses:   
            pageredirect = "/response/travel/expenses?access_token="+access_token+"&number="+str(purchase.id)
        else:
            pageredirect = "/response/message"
         
        _message_post_helper(
            'purchase.order', purchase.id, _('The auditor has accepted the audit.'),
            attachments=[],
            **({'token': access_token} if access_token else {})).sudo()
        request.env.cr.commit()
        
        return request.redirect(pageredirect)


    @http.route('/response/travel/expenses', type='http', auth="public", website=True)
    def action_response_travel_expenses(self, number=None, access_token=None, **kwargs):
        access_token = access_token or request.httprequest.args.get('access_token')
        order_id = number or request.httprequest.args.get('number')
        purchase =  request.env['purchase.order'].sudo().search([('id', '=', order_id)])
        lang = purchase.partner_id.lang or get_lang(request.env).code
        return request.env['ir.ui.view'].with_context(lang=lang)._render_template('auditconfirmation.audit_confirmation_travel_expenses_external_page_view', 
        {
            'accesstoken': access_token,
            'order': order_id
        })
    
    @http.route('/response/message', type='http', auth="public", website=True)
    def action_response_message(self, **kwargs):
        lang = get_lang(request.env).code
        return request.env['ir.ui.view'].with_context(lang=lang)._render_template('auditconfirmation.audit_message_external_page_view', {})
    

    @http.route(['/my/purchase/<int:id>/accept/audit'], type='json', auth="public", website=True)
    def portal_audit_accept(self, id=None, name=None,access_token=None, signature=None):

        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.utcnow())
        access_token = access_token or request.httprequest.args.get('access_token')

        pageredirect = ""
        try:
            order_sudo = self._document_check_access('purchase.order', int(id), access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}
        #purchase =  request.env['purchase.order'].sudo().search([('id', '=', id)])
        purchaseconfirmation = request.env['auditconfirmation.purchaseconfirmation'].sudo().search(['&',('ac_id_purchase', '=', order_sudo.id),'|',('ac_consumed', '=', False),('ac_audit_confirmation_status','=', '3')])
        if not purchaseconfirmation:
            return request.not_found()
        
        purchaseconfirmation.write({'ac_audit_confirmation_status': '1', 'ac_consumed': True})
        order_sudo.write({'ac_audit_confirmation_status': '1', 'sra_audit_signature': signature, 'sra_audit_signature_name': name, 'sra_audit_signature_date': today})
        if order_sudo.ac_request_travel_expenses:
            pageredirect = "/response/travel/expenses?access_token="+access_token+"&number="+str(id)
        else:
            pageredirect = "/response/message"
        
        request.env.cr.commit()
        rafilename = 'RA-'+order_sudo.name+'-'+order_sudo.partner_id.name
        #pdf = request.env.ref('servicereferralagreement.report_rapurchaseorder').sudo()._render_qweb_pdf([id])[0]
        #('%s.pdf' % rafilename, pdf)
        _message_post_helper(
            'purchase.order', id, _('%s has accepted the audit and signed the Referral Agreement') % (name,),
            attachments=[],
            **({'token': access_token} if access_token else {})).sudo()
        return {
            'force_refresh': True,
            'redirect_url': pageredirect,
        }
        
    @http.route(['/travel/expenses/audit'], type='http', methods=['POST'], auth="public", website=True)
    def portal_tralvel_expenses_audit(self, order_id=None, access_token=None, travelexpenses=None, **post):
        try:
            order_sudo = self._document_check_access('purchase.order', int(order_id), access_token=access_token)
            purchaseconfirmation = request.env['auditconfirmation.purchaseconfirmation'].sudo().search([('ac_id_purchase', '=', order_sudo.id),('ac_consumed_travel_expenses', '=', False)])
            if not purchaseconfirmation:
                return request.not_found()
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}
        
        _message_post_helper(
            'purchase.order', order_sudo.id, _('Travel Expenses: %s') % (travelexpenses),
            attachments=[],
            **({'token': access_token} if access_token else {})).sudo()
        
        purchaseconfirmation.write({'ac_consumed_travel_expenses': True})
        request.env.cr.commit()

        return request.redirect('/response/message')


    @http.route(['/my/purchase/<int:id>/decline/audit'], type='http', methods=['POST'], auth="public", website=True)
    def portal_audit_decline(self, id=None,access_token=None, reason=None):

        access_token = access_token or request.httprequest.args.get('access_token')

        try:
            order_sudo = self._document_check_access('purchase.order', int(id), access_token=access_token)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}
        #purchase =  request.env['purchase.order'].sudo().search([('id', '=', id)])
        purchaseconfirmation = request.env['auditconfirmation.purchaseconfirmation'].sudo().search(['&',('ac_id_purchase', '=', order_sudo.id),'|',('ac_consumed', '=', False),('ac_audit_confirmation_status','=', '3')])
        if not purchaseconfirmation:
            return request.not_found()
        
        purchaseconfirmation.write({'ac_audit_confirmation_status': '2', 'ac_consumed': True})
        order_sudo.write({'ac_audit_confirmation_status': '2'})

        _message_post_helper(
            'purchase.order', id, _('%s has rejected the audit. Reason: %s') % (order_sudo.partner_id.name,reason),
            attachments=[],
            **({'token': access_token} if access_token else {})).sudo()
        request.env.cr.commit()
        
        return request.redirect('/response/message')
    
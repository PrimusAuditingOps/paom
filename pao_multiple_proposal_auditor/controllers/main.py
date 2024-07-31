
from werkzeug.urls import url_encode
from math import acos, cos, sin, radians
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
from logging import getLogger
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.web.controllers.main import content_disposition
from functools import reduce

_logger = getLogger(__name__)
 
class WebMultipleProposal(portal.CustomerPortal):
    
    @http.route(['/multiple/proposal/<int:id>/<string:token>'], type='http', auth='user', website=True)
    def multiple_proposal(self, id=False, token=None, **kw):
        
        try:
            purchase_order_sudo = self._document_check_access('purchase.order', int(id), access_token=str(token))
            
            if purchase_order_sudo.audit_status_muilti_proposal != "sent":
                return request.render('pao_multiple_proposal_auditor.pao_multiple_proposal_exception_page_view', {})
            else:
                recAuditorRes = filter(lambda x: x['auditor_id'].id == request.env.user.partner_id.id, purchase_order_sudo.pao_auditior_response_ids)
                for r in recAuditorRes:
                    if r.status == "pending":
                        return request.render('pao_multiple_proposal_auditor.multiple_proposal_portal_template', {})
                    else:
                        return request.render('pao_multiple_proposal_auditor.pao_multiple_proposal_exception_page_view', {})


        except (AccessError, MissingError):
            return request.redirect('/') 
    
    @http.route(['/multiple/proposal/response'], type='http', methods=['POST'], auth="user", website=True)
    def multiple_proposal_response(self, order_id=None, access_token=None, event_accept=None, event_decline=None, comments=None, **post):
        try:
            order_sudo = self._document_check_access('purchase.order', int(order_id), access_token=access_token)
            recAuditorRes = filter(lambda x: x['auditor_id'].id == request.env.user.partner_id.id, order_sudo.pao_auditior_response_ids)
            status = ""
            if event_accept:
                status = "accepted"
            if event_decline:
                status = "declined"

            for r in recAuditorRes:
                r.write({"status":status, "comments": comments})
            
            
                #return request.not_found()
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}
        
        _message_post_helper(
            'purchase.order', order_sudo.id, _('I %s the proposal') % (status),
            attachments=[],
            **({'token': access_token} if access_token else {})).sudo()
        
        request.env.cr.commit()
   
        lang = request.env.user.partner_id.lang
        
        return request.env['ir.ui.view'].with_context(lang=lang)._render_template('pao_multiple_proposal_auditor.pao_multiple_proposal_response_page_view', {})
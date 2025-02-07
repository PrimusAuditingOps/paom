import logging
from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers import portal

_logger = logging.getLogger(__name__)

class ManageAuditCRPortal(portal.CustomerPortal):
    
    def _get_po(self, model, id, token):
        """Utility method to retrieve the PO and handle access errors."""
        try:
            return self._document_check_access(model, id, access_token=token)
        except (AccessError, MissingError):
            return None

    def _redirect_to(self, endpoint, id, token):
        """Utility method to simplify redirection with formatted URL."""
        return request.redirect(f'/ra_request/{endpoint}/{id}/{token}')
    
    @http.route([
        '/disponibilidad_cr/accept/<int:id>/<string:token>',
        '/disponibilidad_cr/decline/<int:id>/<string:token>'
    ], type='http', auth='public', website=True)
    def handle_cr_audit_portal(self, id, token):
        purchase_order_sudo = self._get_po('purchase.order', id, token)
        if not purchase_order_sudo:
            return request.redirect('/')
        
        action = 'accept' if 'accept' in request.httprequest.path else 'decline'
        if action == 'accept':
            message = "El auditor ha confirmado su disponibilidad."
        elif action == 'decline':
            message = "El auditor ha declinado su disponibilidad."
        
        purchase_order_sudo.notify_ra_request_progress(message)
        
        return request.render('pao_sign_ra.cr_portal_response')

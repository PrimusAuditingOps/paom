
from werkzeug.urls import url_encode
from math import acos, cos, sin, radians
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
from logging import getLogger
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.web.controllers.main import content_disposition
from functools import reduce

_logger = getLogger(__name__)
 
class WebMultipleProposal(portal.CustomerPortal):
    
    @http.route(['/multiple/proposal/<int:id>/<string:token>'], type='http', auth='user', website=True)
    def search_auditors(self, id=False, token=None, **kw):
        try:
            purchase_order_sudo = self._document_check_access('purchase.order', int(id), access_token=str(token))
            _logger.error("entro con user")
        except (AccessError, MissingError):
            return request.redirect('/')
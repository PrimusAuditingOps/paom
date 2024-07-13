from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request, Response
from odoo.tools import image_process
from odoo.tools.translate import _
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from logging import getLogger
_logger = getLogger(__name__)

class CustomerPortal(portal.CustomerPortal):

    def _prepare_portal_layout_values(self):
        """ Values for /my/* templates rendering.
            Does not include the record counts.
        """
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        values["isanauditor"] = request.env.user.partner_id.ado_is_auditor
        return values

    def _prepare_home_portal_values(self, counters):
        """ Values for /my & /my/home routes template rendering.
            Includes the record count for the displayed badges.
            where 'counters' is the list of the displayed badges
            and so the list to compute.
            If need to count the agenda use this method
        """
        values = super()._prepare_home_portal_values(counters)
        # if 'agenda_count' in counters:
        #     access_to = request.env.user.partner_id...
        #     values['agenda_count'] = request.env['your.model'].search_count([])
        return values
    
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class GlobalGapApplication(http.Controller):

    @http.route('/application_webform',type="http",auth="public",website=True)
    def application_webform(self, **kw):
        _logger.error("-------------------------Click on Menu Create Application----------------------")
        return http.request.render('pao_fans_automation.create_application',{})

    @http.route('/create/webapplication',type="http",auth="public",website=True)
    def create_webapplication(self, **kw):
        _logger.error("------------ Data Received : "+str(kw))
        request.env['pao.global.gap.application'].create(kw)
        return request.render("pao_fans_automation.application_thanks",{})
    
    @http.route('/application_controller/application_controller',auth='public', website=True)
    def index(self, **kw):
        try:
            applications = http.request.env['pao.global.gap.application'].sudo().search([])
        except: 
            return "<h1> Can't access API </h1>"

        return http.request.render('pao_fans_automation.index',{
            'applications': applications
        })
    
    @http.route('/application_controller/<model("pao.global.gap.application"):ap>',auth='public', website=True)
    def display_application(self,ap):
        
        return http.request.render('pao_fans_automation.applications',{
            'application':ap,
        })



    

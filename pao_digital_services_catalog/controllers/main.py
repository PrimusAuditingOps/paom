# -*- coding: utf-8 -*-
from odoo import http

class PaoDigitalServicesCatalog(http.Controller):
    
    @http.route('/services',auth='public',website=True)
    def index(self,**kw):
        return http.request.render('pao_digital_services_catalog.service_data')
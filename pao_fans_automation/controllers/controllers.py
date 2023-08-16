# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class OdooControllers(http.Controller):
    @http.route(['/get_globalgap_audit_products'],type='json', auth='public', website=True)
    def get_globalgap_audit_products(self, **kw):
        audit_products = http.request.env['servicereferralagreement.auditproducts'].sudo().search([])

        p = []

        for product in audit_products:
            n = {
                "name":product.name,
                "id":product.id
            }
            
            p.append(n)

        p.sort(key=lambda x: x["name"])

        return p
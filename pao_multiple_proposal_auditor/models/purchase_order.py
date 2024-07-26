from odoo import fields, models, api, _
from math import acos, cos, sin, radians
import datetime
import calendar
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from logging import getLogger

_logger = getLogger(__name__)



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'



    def _get_auditor_languages(self):
        auditor_ids = []
        auditors_list = []
        recPartner = self.env["res.partner"].search([("ado_is_auditor","=", True)])
        if len(self.language_ids) > 0:
            for r in recPartner:
                auditors_list.append(r.id)    
                for l in self.language_ids:
                    if l not in r.language_ids.ids:
                        auditor_ids.append(r.id)
                        break
        else:
            auditors_list = [a.id for a in recPartner]

        return [auditor for auditor in auditors_list if auditor not in auditor_ids]

    def _get_approved_auditor(self, auditor_ids):

        products_ids = []
        product_len = len(products_ids)
        params = {}
        
        
        if product_len > 0 and len(auditor_ids) > 0:
            #Get Approved Auditors
            sql = """
                SELECT res_partner_id AS res_partner_id FROM 
                audit_assignment_product_res_partner_rel 
                WHERE res_partner_id IN %(partner_ids)s AND product_product_id IN %(products_ids)s 
                GROUP BY res_partner_id HAVING COUNT(res_partner_id) = %(products_lenght)s
            """
            params = {
                'partner_ids': tuple(auditor_ids),
                'products_ids': tuple(products_ids),
                'products_lenght': product_len,
            }
            #request.env.cr.execute(sql, params)
            #result = request.env.cr.dictfetchall()

            #auditor_ids = [r['res_partner_id'] for r in result]
        return auditor_ids
    
    def _get_auditors_without_veto_organization(self,auditor_ids,organization_ids):
        

        organization_auditors = []

        if len(organization_ids) > 0 and len(auditor_ids) > 0:
            sql = """
                SELECT DISTINCT res_partner_id AS id FROM 
                servicereferralagreement_blocked_organizations_res_partner_rel 
                WHERE res_partner_id IN %(partner_ids)s AND 
                servicereferralagreement_blocked_organization_id IN %(organization_ids)s 
            """
            params = {
                'partner_ids': tuple(auditor_ids),
                'organization_ids': tuple(organization_ids),
            }
            #request.env.cr.execute(sql, params)
            #result = request.env.cr.dictfetchall()

            #organization_auditors = [r['id'] for r in result]
           
        return [auditor for auditor in auditor_ids if auditor not in organization_auditors]
    
    def _get_auditors_without_veto_customer(self,auditor_ids,sale_order_id):
        customer_auditors = []
        if sale_order_id and len(auditor_ids) > 0:
            rec_sale_order = self.env['sale.order'].browse(sale_order_id)
            if rec_sale_order.partner_id:
                sale_partner_id = [rec_sale_order.partner_id.id]
                sql = """
                    SELECT DISTINCT res_partner_id AS id FROM 
                    assignment_auditor_blocked_company_res_partner_rel 
                    WHERE res_partner_id IN %(partner_ids)s AND 
                    assignment_blocked_company_id IN %(sale_partner_id)s 
                """
                params = {
                    'partner_ids': tuple(auditor_ids),
                    'sale_partner_id': tuple(sale_partner_id),
                }
                #request.env.cr.execute(sql, params)
                #result = request.env.cr.dictfetchall()

                #customer_auditors = [r['id'] for r in result]
            
        return [auditor for auditor in auditor_ids if auditor not in customer_auditors]

    def send_multiple_proposal(self):




        return {
            'name': _('Multiple proposal auditor'),
            'domain': [],
            'res_model': 'multiple.proposal.auditor.request',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
                'default_purchase_order_id': self.id,
                'default_purchase_order_id': self.id,
                'default_purchase_order_id': self.id
            },
            'target': 'new',
        }
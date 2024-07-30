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

    audit_status_muilti_proposal = fields.Selection(
        selection=[
            ('not_sent', "Not sent"),
            ('sent', "Sent"),
            ('done', "Done"),
        ],
        default='not_sent',
        string="Audit status multiple proposal", 
        readonly=True, 
        copy=False,
    )
    pao_auditior_response_ids = fields.One2many(
        comodel_name='auditor.response.multi.proposal',
        inverse_name='purchase_id',
        string='Auditor multiple proposal responses',
    )
   

    def _get_auditor_languages(self):
        auditor_ids = []
        auditors_list = []
        recPartner = self.env["res.partner"].search([("ado_is_auditor","=", True), ("company_id","=",self.company_id.id)])
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
        products_ids = [ p.product_id.id for p in self.order_line ] 
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
            self.env.cr.execute(sql, params)
            result = self.env.cr.dictfetchall()

            auditor_ids = [r['res_partner_id'] for r in result]
        return auditor_ids
    
    def _get_auditors_without_veto_organization(self,auditor_ids):
        
        organization_ids = [ l.organization_id.id for l in self.order_line if l.organization_id ] 
    
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
            self.env.cr.execute(sql, params)
            result = self.env.cr.dictfetchall()

            organization_auditors = [r['id'] for r in result]
           
        return [auditor for auditor in auditor_ids if auditor not in organization_auditors]
    
    def _get_auditors_without_veto_customer(self,auditor_ids):
        customer_auditors = []
        if self.sale_order_id and len(auditor_ids) > 0:

            sale_partner_id = [self.sale_order_id.partner_id.id]
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
            self.env.cr.execute(sql, params)
            result = self.env.cr.dictfetchall()

            customer_auditors = [r['id'] for r in result]
            
        return [auditor for auditor in auditor_ids if auditor not in customer_auditors]

    def send_multiple_proposal(self):

        auditors = self._get_auditor_languages()
        auditors = self._get_approved_auditor(auditors)
        auditors = self._get_auditors_without_veto_organization(auditors)
        auditors = self._get_auditors_without_veto_customer(auditors)

        if len(auditors) > 0:
            return {
                'name': _('Multiple proposal auditor'),
                'domain': [],
                'res_model': 'multiple.proposal.auditor.request',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {
                    'default_purchase_order_id': self.id,
                    'default_auditor_ids': auditors,
                },
                'target': 'new',
            }
        else:
            raise ValidationError(_('No auditors were found to carry out the audits.'))

from doctest import ELLIPSIS_MARKER
from xmlrpc.client import Boolean
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PurchaseOrderInherit(models.Model):
    
    _inherit='purchase.order'

    def _get_audit_confirmation_status(self):
        for rec in self:
            domain = [('ac_id_purchase','=',rec.id)]
            status = self.env['auditconfirmation.purchaseconfirmation'].search(domain).ac_audit_confirmation_status
            if not status:
                rec.ac_audit_confirmation_status = '0'  
            else:
                rec.ac_audit_confirmation_status = status
    ac_audit_confirmation_status = fields.Selection(
        selection=[
            ('0', "Not Confirmed"),
            ('1', "Confirmed"),
            ('2', "Denied"),
            ('3', "Tentatively confirmed"),
        ],
        default='0',
        string="Audit Availability Confirmation Status", 
        readonly=True, copy=False,
        #compute=_get_audit_confirmation_status,
        help="Refers to the status of the audit confirmation.")

    def _get_default_audit_status(self):
        domain = [("default_status","=",True)]
        return self.env['auditconfirmation.auditstate'].search(domain, limit=1).id
    ac_audit_status = fields.Many2one(
        string="Audit status",
        comodel_name='auditconfirmation.auditstate',
        readonly = True,
        default = _get_default_audit_status,
    )
    


    @api.depends('partner_id')
    def _get_is_an_auditor(self):
        for rec in self:
            rec.ac_is_an_auditor = rec.partner_id.ado_is_auditor

    ac_is_an_auditor = fields.Boolean(
        string = "Is an auditor",
        compute=_get_is_an_auditor,
    )
    ac_request_travel_expenses = fields.Boolean(
        string = "Request travel expenses",
        default=False,
    )

    def get_confirmation_access_token(self):
        for rec in self:
            token = None
            domain = [('ac_id_purchase','=',rec.id)]
            confirmation = rec.env['auditconfirmation.purchaseconfirmation'].search(domain)
            if not confirmation:
                auditconfirmation = rec.env['auditconfirmation.purchaseconfirmation'].sudo().create({
                        'ac_consumed': False,
                        'ac_audit_confirmation_status': '0',
                        'ac_id_purchase': rec.id,
                })
                token = auditconfirmation.ac_access_token
            else:
                token = confirmation.ac_access_token
            #token = rec._portal_ensure_token()
        return token

    def create_audit_state(self):
        return {
            'name': _('Audit Status'),
            'domain': [],
            'res_model': 'auditconfirmation.auditstate.history',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
                'default_purchase_order_id': self.id
            },
            'target': 'new',
        }
    def show_audit_state_history(self,context=None):
        
        domain = [('purchase_order_id','=',self.id)]

        view_id_tree = self.env['ir.ui.view'].sudo().search([('name','=',"purchase.audit.state.history.view.tree")])
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'auditconfirmation.auditstate.history',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view_id_tree[0].id, 'tree'),(False,'form')],
            'view_id ref="auditconfirmation.purchase_audit_state_history_view_tree"': '',
            'target': 'new',
            'domain': domain,
        }
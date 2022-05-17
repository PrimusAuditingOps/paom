from datetime import datetime, timedelta
from xmlrpc.client import boolean
from odoo import fields, models, api, _
from logging import getLogger
from odoo.exceptions import ValidationError

_logger = getLogger(__name__)
class PurchaseOrderInherit(models.Model):

    _inherit='purchase.order'

    shadow_id = fields.Many2one(
        string="Shadow",
        comodel_name='res.partner',
        ondelete='set null',
    )
    assessment_id = fields.Many2one(
        string="Assessment",
        comodel_name='res.partner',
        ondelete='set null',
    )
    ado_is_external_audit = fields.Boolean(
        string = "Is an external audit",
        default = False,
    )

    ado_is_auditor = fields.Boolean(
        related='partner_id.ado_is_auditor',
    )

    @api.constrains('order_line')
    def _validate_days_off_auditor(self):
        for rec in self:
            msg = ''
            if rec.partner_id:
                #purchase_line = []
                for line in rec.order_line:
                    if line.service_start_date:
                        domain = [('auditor_id', '=', rec.partner_id.id),
                            '|','|','|',
                            '&',('start_date', '>=', line.service_start_date),
                            ('start_date', '<=', line.service_end_date),
                            '&',('end_date', '<=', line.service_start_date),
                            ('end_date', '>=', line.service_end_date),
                            '&',('start_date', '<=', line.service_start_date),
                            ('end_date', '>=', line.service_start_date),
                            '&',('start_date', '<=', line.service_end_date),
                            ('end_date', '>=', line.service_end_date)
                            ]
                        recorddaysoff = self.env['auditordaysoff.days'].search(domain)    
                        if recorddaysoff:
                            msg = _('{0}\n {1} {2} to {3}'.format(msg, line.product_id.name, line.service_start_date, line.service_end_date))
                if msg != '':
                    msg_title = _('The auditor contains days off on the dates of the following products:')
                    raise ValidationError('{0} {1}'.format(msg_title,msg))

    @api.onchange('shadow_id')
    def _change_shadow_id(self):
        cont = 0
        for rec in self:
            if rec.shadow_id:
                listpurchase = []
                listorderid = []
                purchaseorders = ""
                flag = False
                domain = []
                refproveedor = ""
                if rec._origin.id:
                    listorderid.append(rec._origin.id)
                
                for orderline in rec.order_line:
                    if orderline.service_end_date and orderline.service_start_date:
                        domain = [('order_id', 'not in', listorderid),
                        ('state', '<>', 'cancel'),
                        '|','|',
                        ('partner_id', '=', orderline.shadow_id.id),
                        ('assessment_id', '=', orderline.shadow_id.id),
                        ('shadow_id', '=', orderline.shadow_id.id),
                        '|','|','|',
                        '&',('service_start_date', '>=', orderline.service_start_date),
                        ('service_start_date', '<=', orderline.service_end_date),
                        '&',('service_end_date', '<=', orderline.service_start_date),
                        ('service_end_date', '>=', orderline.service_end_date),
                        '&',('service_start_date', '<=', orderline.service_start_date),
                        ('service_end_date', '>=', orderline.service_start_date),
                        '&',('service_start_date', '<=', orderline.service_end_date),
                        ('service_end_date', '>=', orderline.service_end_date)
                        ]
                        record = self.env['purchase.order.line'].search(domain)
                        listpurchase = []
                        for rec in record:
                            refproveedor = ""
                            if rec.order_id.partner_ref:
                                refproveedor = rec.order_id.partner_ref
                            if rec.order_id not in listpurchase:
                                flag = True
                                listpurchase.append(rec.order_id)
                                purchaseorders = _('{0}\n {1} {2} {3} al {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date))
                if flag:
                    msg_title = _('Warning')
                    msg = _('The Shadow contains services on the dates selected of the following Purchase Orders:')
                    return {
                        'warning': {
                            'title': msg_title,
                            'message': _('{0} {1}'.format(msg,purchaseorders)),
                        },
                    }

    @api.onchange('assessment_id')
    def _change_assessment_id(self):
        for rec in self:
            if rec.assessment_id:
                listpurchase = []
                listorderid = []
                purchaseorders = ""
                flag = False
                domain = []
                refproveedor = ""
                if rec._origin.id:
                    listorderid.append(rec._origin.id)
                
                for orderline in rec.order_line:
                    if orderline.service_end_date and orderline.service_start_date:
                        domain = [('order_id', 'not in', listorderid),('state', '<>', 'cancel'),
                        '|','|',('partner_id', '=', orderline.assessment_id.id),
                        ('assessment_id', '=', orderline.assessment_id.id),
                        ('shadow_id', '=', orderline.assessment_id.id),
                        '|','|','|',
                        '&',('service_start_date', '>=', orderline.service_start_date),
                        ('service_start_date', '<=', orderline.service_end_date),
                        '&',('service_end_date', '<=', orderline.service_start_date),
                        ('service_end_date', '>=', orderline.service_end_date),
                        '&',('service_start_date', '<=', orderline.service_start_date),
                        ('service_end_date', '>=', orderline.service_start_date),
                        '&',('service_start_date', '<=', orderline.service_end_date),
                        ('service_end_date', '>=', orderline.service_end_date)
                        ]
                        record = self.env['purchase.order.line'].search(domain)
                        listpurchase = []
                        for rec in record:
                            refproveedor = ""
                            if rec.order_id.partner_ref:
                                refproveedor = rec.order_id.partner_ref
                            if rec.order_id not in listpurchase:
                                flag = True
                                listpurchase.append(rec.order_id)
                                purchaseorders = _('{0}\n {1} {2} {3} al {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date))
                if flag: 
                    msg_title = _('Warning')
                    msg = _('The Assessment contains services on the dates selected of the following Purchase Orders:')
                    return {
                        'warning': {
                            'title': msg_title,
                            'message': _('{0} {1}'.format(msg, purchaseorders)),
                        },
                    }

    @api.onchange('partner_id')
    def _change_partner_id_agenda(self):
        cont = 0
        for rec in self:
            if rec.partner_id:
                listpurchase = []
                listorderid = []
                purchaseorders = ""
                flag = False
                domain = []
                refproveedor = ""
                if rec._origin.id:
                    listorderid.append(rec._origin.id)
                
                for orderline in rec.order_line:
                    if orderline.service_end_date and orderline.service_start_date:
                        domain = [('order_id', 'not in', listorderid),('state', '<>', 'cancel'),
                        '|','|',('partner_id', '=', orderline.partner_id.id),
                        ('assessment_id', '=', orderline.partner_id.id),
                        ('shadow_id', '=', orderline.partner_id.id),
                        '|','|','|',
                        '&',('service_start_date', '>=', orderline.service_start_date),
                        ('service_start_date', '<=', orderline.service_end_date),
                        '&',('service_end_date', '<=', orderline.service_start_date),
                        ('service_end_date', '>=', orderline.service_end_date),
                        '&',('service_start_date', '<=', orderline.service_start_date),
                        ('service_end_date', '>=', orderline.service_start_date),
                        '&',('service_start_date', '<=', orderline.service_end_date),
                        ('service_end_date', '>=', orderline.service_end_date)
                        ]
                        record = self.env['purchase.order.line'].search(domain)
                        listpurchase = []
                        for rec in record:
                            refproveedor = ""
                            if rec.order_id.partner_ref:
                                refproveedor = rec.order_id.partner_ref
                            if rec.order_id not in listpurchase:
                                flag = True
                                listpurchase.append(rec.order_id)
                                purchaseorders = _('{0}\n {1} {2} {3} al {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date))
                if flag:
                    msg_title = _('Warning')
                    msg = _('The Vendor contains services on the dates selected of the following Purchase Orders:')
                    return {
                        'warning': {
                            'title': msg_title,
                            'message': _('{0} {1}'.format(msg,purchaseorders)),
                        },
                    }

                    
                    

from datetime import datetime, timedelta
from email import message
from odoo import fields, models, api, _
from logging import getLogger


_logger = getLogger(__name__)
class PurchaseOrderLine(models.Model):
    _inherit='purchase.order.line'
    shadow_id = fields.Many2one('res.partner', 
    related='order_id.shadow_id', string='Shawow', readonly=True, store=True)
    assessment_id = fields.Many2one('res.partner', 
    related='order_id.assessment_id', string='Assessment', readonly=True, store=True)

    @api.onchange('service_end_date','service_start_date')
    def _change_start_end_date(self):
        for orderline in self:
            purchaseorders = ""
            purchaseordersshadow = ""
            purchaseordersassessment = ""
            returnmsg = ""
            flag = False
            listpurchase = []
            domain = []
            listidline = []

            for recpurchaseline in orderline.order_id.order_line:
                if recpurchaseline._origin.id:
                    listidline.append(recpurchaseline._origin.id)
            if orderline.service_end_date and orderline.service_start_date: 
                if orderline.order_id.partner_id:
                    domain = ['&','|',('shadow_id', '=', orderline.partner_id.id),
                    ('assessment_id', '=', orderline.partner_id.id),
                    ('id', 'not in', listidline),('state', '<>', 'cancel'),
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
                    if purchaseorders != "":
                        msg_vendor = _('The Vendor is assigned as Shadow or Assessment on the dates selected of the following Purchase Orders: ')
                        returnmsg = '{0} {1}'.format(msg_vendor,purchaseorders)
                if orderline.order_id.shadow_id:
                    domain = [('id', 'not in', listidline),('state', '<>', 'cancel'),
                    '|','|',('partner_id', '=', orderline.shadow_id.id),
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
                            purchaseordersshadow = _('{0}\n {1} {2} {3} al {4}'.format(purchaseordersshadow,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date))
                    if purchaseordersshadow != "":
                        msg_shadow = _('The Shadow contains services on the dates selected of the following Purchase Orders: ')
                        returnmsg = '{0}\n{1} {2}'.format(returnmsg,msg_shadow,purchaseordersshadow)
                if orderline.order_id.assessment_id:
                    domain = [('id', 'not in', listidline),('state', '<>', 'cancel'),
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
                            purchaseordersassessment = _('{0}\n {1} {2} {3} al {4}'.format(purchaseordersassessment,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date))
                    if purchaseordersassessment != "":
                        msg = _('The Assessment contains services on the dates selected of the following Purchase Orders: ')
                        returnmsg = _('{0}\n{1} {2}'.format(returnmsg,msg,purchaseordersassessment))                
            if flag:
                msg_title = _('Warning')
                return {
                    'warning': {
                        'title':msg_title,
                        'message': returnmsg
                    },
                }

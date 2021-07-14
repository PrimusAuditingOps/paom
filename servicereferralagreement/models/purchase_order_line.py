from datetime import datetime, timedelta
from odoo import fields, models, api, _

class PurchaseOrderLine(models.Model):
    _inherit='purchase.order.line'

    def _generate_referral_date(self):
        for rec in self:
            if rec.service_start_date:
                rec.referral_date = rec.service_start_date + timedelta(days=-1)
            else:
                rec.referral_date = datetime.today()

    organization_id = fields.Many2one(
        comodel_name = 'servicereferralagreement.organization', 
        string='Organization', 
        help='Select Organization', 
        ondelete='set null',
    )
    registrynumber_id = fields.Many2one(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registry number',
        ondelete='set null',
    )
       
    service_start_date = fields.Date(
        string="Service start date",
    )
    service_end_date = fields.Date(
         string="Service end date",
    )
    referral_date = fields.Date(
        compute= _generate_referral_date,
    )
    update_number = fields.Integer(
        default= 0,
    )
    sra_customer_id = fields.Many2one(
       related="order_id.sale_order_id.partner_id",
    )  
    sra_sale_line_ids = fields.Many2many(
        'sale.order.line',
        'sale_order_line_purchase_line_rel',
        'purchase_order_line_id', 'sale_order_line_id',
        string='Sales Order Lines', readonly=True, copy=False)
    
     

    @api.onchange('service_end_date')
    def _change_end_date(self):
        cont = 0
        for orderline in self:
            cont = 1
            if orderline.service_start_date:
                if orderline.service_start_date > orderline.service_end_date:
                    orderline.service_start_date = orderline.service_end_date
            else:
                orderline.service_start_date = orderline.service_end_date
            for line in orderline.order_id.order_line:
                if line.product_id:
                    if orderline.registrynumber_id.id == line.registrynumber_id.id and orderline.organization_id.id == line.organization_id.id:
                        cont += line.update_number    
            orderline.update_number = cont
        
        purchaseorders = ""
        suma = 0
        listpurchase = []
        refproveedor = ""
        if self.service_end_date and self.service_start_date: 
            if self.order_id.partner_id:
                domain = [('partner_id', '=', self.partner_id.id),'|','|','|',
                    '&',('service_start_date', '>=', self.service_start_date),
                    ('service_start_date', '<=', self.service_end_date),
                    '&',('service_end_date', '<=', self.service_start_date),
                    ('service_end_date', '>=', self.service_end_date),
                    '&',('service_start_date', '<=', self.service_start_date),
                    ('service_end_date', '>=', self.service_start_date),
                    '&',('service_start_date', '<=', self.service_end_date),
                    ('service_end_date', '>=', self.service_end_date)
                ]
                record = self.env['purchase.order.line'].search(domain)
                for rec in record:
                    refproveedor = ""
                    if rec.order_id.partner_ref:
                        refproveedor = rec.order_id.partner_ref

                    if self.id:
                        if self.id != rec.order_id:
                            if rec.order_id.state != 'cancel' and rec.order_id not in listpurchase:
                                suma = 1
                                listpurchase.append(rec.order_id)
                                purchaseorders = '{0}\n {1} {2} {3} to {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date)
                    else:
                       
                        if rec.order_id.state != 'cancel' and rec.order_id not in listpurchase:
                            suma = 1
                            listpurchase.append(rec.order_id)
                            purchaseorders = '{0}\n {1} {2} {3} to {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date)
        if suma == 1:
            return {
                'warning': {
                    'title': "Warning",
                    'message': _('The supplier contains services assigned on the selected dates on the following purchase orders: {0}'.format(purchaseorders)),
                },
            }

    @api.onchange('service_start_date')
    def _change_start_date(self):
        cont = 0
        for orderline in self:
            cont = 1
            if orderline.service_end_date:
                if orderline.service_end_date < orderline.service_start_date:
                    orderline.service_end_date = orderline.service_start_date
            else:
                orderline.service_end_date = orderline.service_start_date
            for line in orderline.order_id.order_line:
                if line.product_id:
                    if orderline.registrynumber_id.id == line.registrynumber_id.id and orderline.organization_id.id == line.organization_id.id:
                        cont += line.update_number    
            orderline.update_number = cont
        purchaseorders = ""
        suma = 0
        listpurchase = []
        refproveedor = ""
        if self.service_end_date and self.service_start_date: 
            if self.order_id.partner_id:
                domain = [('partner_id', '=', self.partner_id.id),'|','|','|',
                    '&',('service_start_date', '>=', self.service_start_date),
                    ('service_start_date', '<=', self.service_end_date),
                    '&',('service_end_date', '<=', self.service_start_date),
                    ('service_end_date', '>=', self.service_end_date),
                    '&',('service_start_date', '<=', self.service_start_date),
                    ('service_end_date', '>=', self.service_start_date),
                    '&',('service_start_date', '<=', self.service_end_date),
                    ('service_end_date', '>=', self.service_end_date)
                ]
                record = self.env['purchase.order.line'].search(domain)
                for rec in record:
                    refproveedor = ""
                    if rec.order_id.partner_ref:
                        refproveedor = rec.order_id.partner_ref

                    if self.id:
                        if self.id != rec.order_id:
                            if rec.order_id.state != 'cancel' and rec.order_id not in listpurchase:
                                suma = 1
                                listpurchase.append(rec.order_id)
                                purchaseorders = '{0}\n {1} {2} {3} to {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date)
                    else:
                        if rec.order_id.state != 'cancel' and rec.order_id not in listpurchase:
                            suma = 1
                            listpurchase.append(rec.order_id)
                            purchaseorders = '{0}\n {1} {2} {3} to {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date)
        if suma == 1:
            return {
                'warning': {
                    'title': "Warning",
                    'message': _('The supplier contains services assigned on the selected dates on the following purchase orders: {0}'.format(purchaseorders)),
                },
            }
from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger


_logger = getLogger(__name__)
class PurchaseOrderLine(models.Model):
    _inherit='purchase.order.line'

    @api.depends('price_subtotal', 'taxes_id')
    def _generate_subtotal(self):
        for line in self:
            sumasubtotaliva = 0.0
            subtotaliva = 0.0
            for lineiva in line.taxes_id:
                if lineiva.amount > 0:
                    sumasubtotaliva += line.price_subtotal * lineiva.amount / 100 

            subtotaliva = line.price_subtotal + sumasubtotaliva

            line.update({
                'sra_subtotal_iva': subtotaliva,
            })

    def _generate_referral_date(self):
        for rec in self:
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
        copy=False,
    )
    sra_customer_id = fields.Many2one(
       related="order_id.sale_order_id.partner_id",
    )  
    sra_sale_line_ids = fields.Many2many(
        'sale.order.line',
        'sale_order_line_purchase_line_rel',
        'purchase_order_line_id', 'sale_order_line_id',
        string='Sales Order Lines')
    

    sra_sale_line_product_audit_ids = fields.Many2many(
        related="sra_sale_line_ids.audit_products",
        string="Audit products",
    )
    sra_sale_line_price_unit = fields.Float(
        related="sra_sale_line_ids.price_unit",
        string="Price unit",
    )
    sra_subtotal_iva = fields.Monetary(
        compute= _generate_subtotal,
        string="Subtotal Iva",
    )

    @api.onchange('service_end_date')
    def _change_end_date(self):
        cont = 0
        for orderline in self:
            cont = 1
            if orderline.service_end_date:
                if orderline.service_start_date:
                    if orderline.service_start_date > orderline.service_end_date:
                        orderline.service_start_date = orderline.service_end_date
                else:
                    orderline.service_start_date = orderline.service_end_date
            else:
                orderline.service_start_date = None
            
            for line in orderline.order_id.order_line:
                if line.product_id:
                    if orderline.registrynumber_id.id == line.registrynumber_id.id and orderline.organization_id.id == line.organization_id.id:
                        if line.update_number and line.update_number > cont:
                            cont = line.update_number  
            orderline.update_number = cont + 1

            purchaseorders = ""
            suma = 0
            listpurchase = []
            domain = []
            listidline = []
            refproveedor = ""

            for recpurchaseline in orderline.order_id.order_line:
                if recpurchaseline._origin.id:
                    listidline.append(recpurchaseline._origin.id)
            if orderline.service_end_date and orderline.service_start_date: 
                if orderline.order_id.partner_id:
                    
                    domain = [('partner_id', '=', orderline.partner_id.id),
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
                    for rec in record:
                        refproveedor = ""
                        if rec.order_id.partner_ref:
                            refproveedor = rec.order_id.partner_ref
                        if rec.order_id not in listpurchase:
                            suma = 1
                            listpurchase.append(rec.order_id)
                            purchaseorders = _('{0}\n {1} {2} {3} to {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date))
            if suma == 1:
                return {
                    'warning': {
                        'title': "Warning",
                        'message': _('EL proveedor contiene servicios asignados para la fecha seleccionada en los siguientes pedidos de compra: {0}'.format(purchaseorders)),
                    },
                }

    @api.onchange('service_start_date')
    def _change_start_date(self):
        cont = 0
        for orderline in self:
            cont = 1
            if orderline.service_start_date:
                if orderline.service_end_date:
                    if orderline.service_end_date < orderline.service_start_date:
                        orderline.service_end_date = orderline.service_start_date
                else:
                    orderline.service_end_date = orderline.service_start_date
            else:
                orderline.service_end_date = None
                
            for line in orderline.order_id.order_line:
                if line.product_id:
                    if orderline.registrynumber_id.id == line.registrynumber_id.id and orderline.organization_id.id == line.organization_id.id:  
                        if line.update_number and line.update_number > cont:
                            cont = line.update_number
            orderline.update_number = cont + 1

            purchaseorders = ""
            suma = 0
            listpurchase = []
            domain = []
            listidline = []
            refproveedor = ""

            for recpurchaseline in orderline.order_id.order_line:
                if recpurchaseline._origin.id:
                    listidline.append(recpurchaseline._origin.id)
            if orderline.service_end_date and orderline.service_start_date: 
                if orderline.order_id.partner_id:
                    
                    domain = [('partner_id', '=', orderline.partner_id.id),
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
                    for rec in record:
                        refproveedor = ""
                        if rec.order_id.partner_ref:
                            refproveedor = rec.order_id.partner_ref
                        if rec.order_id not in listpurchase:
                            suma = 1
                            listpurchase.append(rec.order_id)
                            purchaseorders = _('{0}\n {1} {2} {3} to {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date))
            if suma == 1:
                return {
                    'warning': {
                        'title': "Warning",
                        'message': _('EL proveedor contiene servicios asignados para la fecha seleccionada en los siguientes pedidos de compra: {0}'.format(purchaseorders)),
                    },
                }
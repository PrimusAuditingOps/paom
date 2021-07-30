from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger


_logger = getLogger(__name__)
class PurchaseOrder(models.Model):

    _inherit='purchase.order'

    
    def _get_organization_id(self):
        dominio = [('id', '=', -1)]
        organization_list = []
        for rec in self:
            for recsale in rec.sale_order_id.order_line:
                if recsale.organization_id:
                    organization_list.append(recsale.organization_id.id)
        if organization_list:
            dominio = [('id', 'in', organization_list)]
        return dominio
    
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        ondelete='set null',
    )    
    coordinator_id = fields.Many2one(
        string="Coordinator",
        comodel_name='res.users',
        ondelete='set null',
        index=True,
        domain = [('share','=',False)],
    )
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            if rec.sale_order_id:
                rec.order_line = None
                rec.sale_order_id = None
    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        purchase_line = []
        percentagevendor = 0
        priceunit = 0.0
        domain = []
        qty = 0
        nr = 0
        idpro= 0
        listdic = []
        listfecha = []
        ind = 0
        add = True
        hasregistration = False
        notexist = True
        for recpurchase in self:
            if not recpurchase.sale_order_id:
                return
            else:
                purchase_line = [(5, 0, 0)]
                domain = [('id','!=',recpurchase._origin.id),('sale_order_id','=',recpurchase.sale_order_id.id),('sale_order_id','=',recpurchase.sale_order_id.id),('state','!=','cancel')]
                recorpurchase = self.env['purchase.order'].search(domain)
                for rec in recorpurchase:
                    for line in rec.order_line:
                        if line.registrynumber_id.id:
                            ind = 0
                            for lis in listdic:
                                nr = 0
                                idpro = 0
                                qty = 0
                                for k,v in lis.items():
                                    if k == 'nr':
                                        nr = v
                                    if k == 'prod':
                                        idpro = v
                                    if k == 'qty':
                                        qty = v
                                if nr == line.registrynumber_id.id and idpro == line.product_id.id:
                                    listdic[ind] = {'nr': nr, 'prod': idpro, 'qty': qty + line.product_uom_qty}
                                    notexist = False
                                    break
                                ind= ind + 1                        
                            if notexist:
                                listdic.append({'nr': line.registrynumber_id.id, 'qty': line.product_uom_qty, 'prod': line.product_id.id})
                            notexist=True
                for line in recpurchase.sale_order_id.order_line:
                    if line.product_template_id.can_be_commissionable:
                        add= True
                        ind = 0 
                        for lis in listdic:
                            nr = 0
                            idpro = 0
                            qty = 0
                            for k,v in lis.items():
                                if k == 'nr':
                                    nr = v
                                if k == 'prod':
                                    idpro = v
                                if k == 'qty':
                                    qty = v
                            if nr == line.registrynumber_id.id and idpro == line.product_id.id:
                                if line.product_uom_qty <= qty:
                                    add = False
                                    listdic[ind] = {'nr': nr, 'prod': idpro, 'qty': qty - line.product_uom_qty}
                                else:
                                    add = True
                                    line.product_uom_qty = line.product_uom_qty - qty
                                    listdic[ind] = {'nr': nr, 'prod': idpro, 'qty': 0}
                                break
                            ind= ind + 1
                        if add:
                            hasregistration = True
                            dateplanned = datetime.now()
                            priceunit = 0.0
                            if recpurchase.date_planned:
                                dateplanned = recpurchase.date_planned
                            else:
                                if recpurchase.date_order:
                                    dateplanned = recpurchase.date_order
                            
                            if recpurchase.partner_id:
                                percentagevendor = recpurchase.partner_id.vendor_service_percentage
                            
                            if percentagevendor and percentagevendor > 0:
                                priceunit = round((line.price_unit * percentagevendor) / 100,2)
                                if recpurchase.currency_id:
                                    if not recpurchase.currency_id == recpurchase.sale_order_id.pricelist_id.currency_id:
                                        domain = [('currency_id','=',recpurchase.currency_id.id)]
                                        recexchangerateauditor = self.env['servicereferralagreement.auditorexchangerate'].search(domain)
                                        for recrate in recexchangerateauditor:
                                            priceunit = recrate.exchange_rate * priceunit
                                
                            data = {
                                'name': line.name,
                                'price_unit': priceunit,
                                'product_uom_qty': line.product_uom_qty,
                                'product_qty': line.product_uom_qty,
                                'product_id': line.product_id.id,
                                'product_uom': line.product_uom.id,
                                'date_planned': dateplanned,
                                'organization_id': line.organization_id.id,
                                'registrynumber_id': line.registrynumber_id.id,
                                'service_start_date': line.service_start_date,
                                'service_end_date': line.service_end_date,
                                'sra_sale_line_ids': [(6, 0, [line.id])],
                            }                         
                            purchase_line.append((0,0,data))
                            dictfechas = {}
                            if line.service_start_date:
                                dictfechas = {'fechainicio': line.service_start_date, 'fechafin': line.service_end_date}
                                if dictfechas not in listfecha:
                                    listfecha.append(dictfechas)
            if  hasregistration and purchase_line:
                recpurchase.order_line=purchase_line
                recpurchase.order_line._compute_tax_id()

                #Busqueda para saber si el proveedor (auditor) cuenta con
                #un pedido de compra sobre la fecha tentativa del pedido de venta
                purchaseorders = ""
                suma = 0
                refproveedor = ""
                listpurchase = []
                domain = []
                if len(listfecha) > 0:
                    if recpurchase.partner_id:
                        for dictfechas in listfecha:
                            fechainicio = None
                            fechafin = None
                            for k,v in dictfechas.items():
                                if k == 'fechainicio':
                                    fechainicio = v
                                if k == 'fechafin':
                                    fechafin = v
            
                        domain = [('partner_id', '=', recpurchase.partner_id.id),
                            ('state', '<>', 'cancel'),
                            '|','|','|',
                            '&',('service_start_date', '>=', fechainicio),
                            ('service_start_date', '<=', fechafin),
                            '&',('service_end_date', '<=', fechainicio),
                            ('service_end_date', '>=', fechafin),
                            '&',('service_start_date', '<=', fechainicio),
                            ('service_end_date', '>=', fechainicio),
                            '&',('service_start_date', '<=', fechafin),
                            ('service_end_date', '>=', fechafin)
                            ]
                        record = self.env['purchase.order.line'].search(domain)
                        for rec in record:
                            refproveedor = ""
                            if rec.order_id.partner_ref:
                                refproveedor = rec.order_id.partner_ref

                            if recpurchase._origin.id:
                                if not recpurchase._origin.id == rec.order_id.id:
                                    if rec.order_id not in listpurchase:
                                        suma = 1
                                        listpurchase.append(rec.order_id)
                                        purchaseorders = '{0}\n {1} {2} {3} to {4}'.format(purchaseorders,rec.order_id.name, refproveedor, rec.service_start_date, rec.service_end_date)
                            else:
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

                ##

            else:
                pedido = recpurchase.sale_order_id.name
                recpurchase.sale_order_id = None
                return {
                        'warning': {
                            'title': "Warning",
                            'message': _('El pedido de venta {0} no tiene productos disponibles para relacionar con la orden de compra.'.format(pedido)),
                        },
                    }
    @api.onchange('order_line')
    def _change_date_order(self):
        
        for recpurchase in self:
            organization = -1
            registrynumber = -1
            service_end_date = None
            service_start_date = None
            for rec in recpurchase.order_line.sorted(key=lambda r: (r.organization_id.id,r.registrynumber_id.id,r.update_number), reverse=True):
                if not organization == rec.organization_id.id or not registrynumber == rec.registrynumber_id.id:
                    service_start_date = rec.service_start_date
                    service_end_date = rec.service_end_date
                    
                else:
                    rec.update({'service_end_date': service_end_date})
                    rec.update({'service_start_date': service_start_date})
                organization = rec.organization_id.id
                registrynumber = rec.registrynumber_id.id
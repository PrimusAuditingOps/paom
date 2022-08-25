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

    def _get_audit_type_id(self):
        dominio = [('id', '=', -1)]
        audit_type_list = []
        for rec in self:
            for recaudittype in rec.partner_id.audit_fee_id:
                audit_type_list.append(recaudittype.audit_fees_id.id)
        if audit_type_list:
            dominio = [('id', 'in', audit_type_list)]
        return dominio

    @api.model
    def _default_country(self):
        return self.env['res.country'].search(['|',('name','=','Mexico'),('name','=','México')], limit=1)
    
    audit_fee_id = fields.Many2one(
        comodel_name = 'servicereferralagreement.auditfees', 
        string='Audit type', 
        help='Select Audit type', 
        ondelete='restrict',
    )
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
    audit_country_id = fields.Many2one(
        comodel_name = 'res.country', 
        string='Audit Country', 
        help='Select Country', 
        ondelete='restrict',
        default = _default_country
    )  
    audit_state_id = fields.Many2one(
        comodel_name = "res.country.state", 
        string='Audit State', 
        help='Select State', 
        ondelete='restrict',
        domain=[('country_id', '=', -1)],
    )
    audit_city_id = fields.Many2one(
        comodel_name = "res.city", 
        string='Audit City', 
        help='Select City', 
        ondelete='restrict',
        domain=[('state_id', '=', -1)],
    )
    sra_audit_signature = fields.Binary(
        string="Audit Signature", 
        copy=False,
    )
    sra_audit_signature_name = fields.Char(
        string="Auditor's signature name", 
        copy=False,
    )
    sra_audit_signature_date = fields.Date(
        string="Auditor's signature date", 
        copy=False,
    )
    registration_number_order_lines_ids = fields.Many2many(
        comodel_name='servicereferralagreement.registrynumber', 
        compute='_get_registration_number', 
        string='Registration number order lines',
        readonly=True,
    )   
    def _get_registration_number(self):
        rn = []
        for rec in self:
            for orderline in rec.order_line:
                if orderline.registrynumber_id.id not in rn:
                    rn.append(orderline.registrynumber_id.id)
            
            rec.registration_number_order_lines_ids = rn
    
    registration_number_print = fields.Many2one(
        string="Document to print",
        comodel_name='servicereferralagreement.registrynumber',
        ondelete='set null',
        index=True,
    )

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            if rec.sale_order_id and rec.audit_fee_id:
                rec.order_line = None
                rec.sale_order_id = None
                rec.audit_fee_id = None
    @api.onchange('audit_fee_id')
    def _onchange_audit_fee_id(self):
        for rec in self:
            percentagevendor = 0.00
            if rec.partner_id and rec.audit_fee_id and rec.sale_order_id:
                for recorderline in rec.order_line:
                    for fee in rec.partner_id.audit_fee_percentages_ids:
                        if  fee.audit_fees_id.id == rec.audit_fee_id.id:
                            percentagevendor = fee.audit_percentage
                    priceunit = round((recorderline.sra_sale_line_price_unit * percentagevendor) / 100,2)
                    if rec.currency_id:
                        if not rec.currency_id == rec.sale_order_id.pricelist_id.currency_id:
                            domain = [('currency_id','=',rec.currency_id.id)]
                            recexchangerateauditor = self.env['servicereferralagreement.auditorexchangerate'].search(domain)
                            for recrate in recexchangerateauditor:
                                priceunit = recrate.exchange_rate * priceunit
                    recorderline.price_unit = priceunit

    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        purchase_line = []
        percentagevendor = 0.00
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
                        cantproduct = line.product_uom_qty
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
                                if cantproduct <= qty:
                                    add = False
                                    listdic[ind] = {'nr': nr, 'prod': idpro, 'qty': qty - cantproduct}
                                else:
                                    add = True
                                    cantproduct = cantproduct - qty
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
                                if recpurchase.audit_fee_id:
                                    for fee in recpurchase.partner_id.audit_fee_percentages_ids:
                                        if  fee.audit_fees_id.id == recpurchase.audit_fee_id.id:
                                            percentagevendor = fee.audit_percentage
                            
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
                                'product_uom_qty': cantproduct,
                                'product_qty': cantproduct,
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
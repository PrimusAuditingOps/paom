from datetime import datetime, timedelta
from odoo import fields, models, api
from logging import Logger, getLogger
import dateutil.parser

_logger = getLogger(__name__)
class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'
    _description = 'Linea de pedido de venta'

    
    def _generate_service_date(self):
        for rec in self:
            rec.service_date = datetime.today()
    def _generate_service_start_date_nop(self):
        for rec in self:
            if rec.service_start_date:
                rec.service_start_date_nop = datetime.strftime(rec.service_start_date, "%m/%d/%Y")
    def _generate_service_end_date_nop(self):
        for rec in self:
            if rec.service_end_date:
               rec.service_end_date_nop = datetime.strftime(rec.service_end_date, "%m/%d/%Y")
    def _generate_service_date_nop(self):
        datenop = None
        for rec in self:
            datenop = datetime.today()
            rec.service_date_nop = datetime.strftime(datenop, "%m/%d/%Y")
    def _generate_service_date_string(self):
        months = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")
        day = None
        month = None
        year = None
        dateservice = None
        for rec in self:
            dateservice = datetime.today()
            day = dateservice.day
            month = months[dateservice.month - 1]
            year = dateservice.year
            rec.service_date_string = "{0} de {1} del {2}".format(day, month, year)

    organization_id = fields.Many2one(
        comodel_name='servicereferralagreement.organization',
        string='Organization',
        ondelete='set null',
    )
    registrynumber_id = fields.Many2one(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registry number',
        ondelete='set null',
        domain = [('organization_id.id', '=', organization_id)]
    )
    audit_products = fields.Many2many(
        comodel_name='servicereferralagreement.auditproducts',
    )
    service_start_date = fields.Date(
        string="Service start date",
    )
    service_end_date = fields.Date(
         string="Service end date",
    )
    coordinator_id = fields.Many2one(
        string="Coordinator",
        comodel_name='res.users',
        ondelete='set null',
        index=True,
        domain = [('share','=',False)],
    )
    service_date = fields.Date(
        compute= _generate_service_date,
    )
    service_date_string = fields.Text(
        compute= _generate_service_date_string,
    )
    service_date_nop = fields.Text(
        compute= _generate_service_date_nop,
    )
    service_start_date_nop = fields.Text(
        compute= _generate_service_start_date_nop,
    )
    service_end_date_nop = fields.Text(
        compute= _generate_service_end_date_nop,
    )
    update_number = fields.Integer(
        default= 0,
        copy=False,
    )
    update_number_coordinator = fields.Integer(
        default= 0,
        copy=False,
    )
    @api.onchange('organization_id')
    def _cancel_selection_registrynumber(self):
        #organization = -1
        for rec in self:
            #if rec.organization_id:
                #organization = rec.organization_id.id
            rec.registrynumber_id = None
        #dominio = {'domain': {'registrynumber_id': [('organization_id.id', '=', organization)]}}
        #return dominio
    @api.onchange('registrynumber_id')
    def _copy_organization_date(self):
        organizationid = 0
        registrynumberid = 0
        for rec in self:
            if rec.product_id:
                organizationid = rec.organization_id.id
                registrynumberid = rec.registrynumber_id.id
                for line in rec.order_id.order_line:
                    if not rec.id == line.id:
                        if line.service_start_date and line.service_end_date and line.registrynumber_id.id == registrynumberid and line.organization_id.id == organizationid:
                            rec.service_start_date = line.service_start_date
                            rec.service_end_date = line.service_end_date
                            rec.coordinator_id = line.coordinator_id
                            break 
    
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
            orderline.update_number = cont +1
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

    @api.onchange('coordinator_id')
    def _change_coordinator(self):
        cont = 0
        for orderline in self:
            cont = 1
            for line in orderline.order_id.order_line:
                if line.product_id:
                    if orderline.registrynumber_id.id == line.registrynumber_id.id and orderline.organization_id.id == line.organization_id.id:
                        if line.update_number_coordinator and line.update_number_coordinator > cont:
                            cont = line.update_number_coordinator  
            orderline.update_number_coordinator = cont + 1
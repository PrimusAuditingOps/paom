from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from logging import getLogger
from datetime import datetime
from werkzeug.urls import url_join
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class PaoChildSalesOrderLineDetail(models.TransientModel):
    _name = 'pao.cso.line.detail'
    _description = 'Pao child sales order line'


    name = fields.Text(
        string="Description",
    )
    namee = fields.Text(
        string="Description",
    )

    audit_products = fields.Many2many(
        comodel_name='servicereferralagreement.auditproducts',
    )

    organization_id = fields.Many2one(
        comodel_name='servicereferralagreement.organization',
        string='Organization',
    )
    registrynumber_id = fields.Many2one(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registry number',
    )
    service_start_date = fields.Date(
        string="Service start date",
    )
    service_end_date = fields.Date(
         string="Service end date",
    )

    child_sale_order_id = fields.Many2one(
        comodel_name='pao.child.sales.order.line',
        string='Child sale order',
        ondelete='set null',
    )

    test = fields.Integer(
        string="Sale order line",
    )


    

  

    
    
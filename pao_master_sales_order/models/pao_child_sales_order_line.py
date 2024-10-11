from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from logging import getLogger
from datetime import datetime
from werkzeug.urls import url_join
import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class PaoChildSalesOrderLine(models.TransientModel):
    _name = 'pao.child.sales.order.line'
    _description = 'Pao child sales order line'

    sale_order_id = fields.Many2one(
        'sale.order', 
        string="Sale order",
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
    )
    

    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        for rec in self:
            cso_line = []
            """
            for line in rec.sale_order_id.order_line:
                _logger.error("errorrrr")
                _logger.error(line.id)
                detail = {
                    'name': line.name,
                    'namee': line.organization_id.name,
                    'audit_products': line.audit_products,
                    'organization_id': line.organization_id.id,
                    'registrynumber_id': line.registrynumber_id.id,
                    'service_start_date': line.service_start_date,
                    'service_end_date': line.service_end_date, 
                    'child_sale_order_id': rec._origin.id,
                    'test': 2
                }
                cso_line.append((0,0,detail))
            
            rec.order_line_detail_id = cso_line
            """
    def create_request(self):

        self.ensure_one()
        
        sale_id = self.env['sale.order'].browse(self.sale_order_id.id).copy(
            {
                'partner_id': self.partner_id.id,
                'pricelist_id': self.partner_id.pao_sc_price_list.id,
                'payment_term_id': self.partner_id.property_payment_term_id.id,
                'pao_is_a_child_sales_order': True,
                'pao_is_a_master_sales_order': False,
                'pao_parent_id': self.sale_order_id.id,
                'partner_invoice_id': self.partner_id.id,
                'partner_shipping_id': self.partner_id.id,
            }
        )
        sale_id._recompute_prices()

        return {
            'name': _('Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': sale_id.id,
        }
        
    
   
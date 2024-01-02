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
    """
    order_line_detail_id = fields.One2many(
        comodel_name='pao.cso.line.detail',
        inverse_name='child_sale_order_id',
        string='Order line',
        required=True,
    )
    """

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

        """
        sale_order = self.env["sale.order"].create({
            'partner_id': self.partner_id.id,
            'pricelist_id': self.partner_id.property_product_pricelist.id,
            'payment_term_id': self.partner_id.property_payment_term_id.id,
            'pao_is_a_child_sales_order': True,
            'pao_parent_id': self.sale_order_id.id,
        })
        """
        """
        child_so_line = [(5, 0, 0)]
        for line in self.order_line_detail_id:
            
            _logger.error(line.name)
            _logger.error(line.audit_products)
            _logger.error(line.organization_id)
            _logger.error(line.registrynumber_id)
            _logger.error(line.service_start_date)
            _logger.error(line.service_end_date)
            _logger.error(line.namee)
        """    
           
           
        """   
            detail = {
                    'order_id': sale_order.id,
                    'name': line.name,
                    'sequence': line.order_line_id.sequence,
                    'display_type': line.order_line_id.display_type,
                    'is_downpayment': line.order_line_id.is_downpayment,
                    'is_expense': line.order_line_id.is_expense,
                    'product_uom_qty': line.order_line_id.product_uom_qty,
                    'tax_id': line.order_line_id.tax_id,
                    'price_unit': line.order_line_id.price_unit,
                    'discount': line.order_line_id.discount,
                    'organization_id': line.order_line_id.organization_id.id,
                    'registrynumber_id': line.order_line_id.registrynumber_id.id,
                    'service_start_date': line.order_line_id.service_start_date,
                    'service_end_date': line.order_line_id.service_end_date
            }
            child_so_line.append((0,0,detail))
            
        sale_order.order_line = child_so_line
        """
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
        sale_id.update_prices()

        return {
            'name': _('Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': sale_id.id,
        }
        
    
   
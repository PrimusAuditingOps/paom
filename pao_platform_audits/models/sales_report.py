from odoo import fields, models, api

class SaleReport(models.Model):
    _inherit = 'sale.report'

    pao_platform_audit_ids = fields.Many2many(
        related="sale_order_line_id.pao_platform_audit_ids"
    )
                    
   
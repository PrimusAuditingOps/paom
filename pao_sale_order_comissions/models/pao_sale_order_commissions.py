from odoo import fields, models, api

class PaoSaleOrderCommissions(models.Model):
    _name = 'pao.sale.order.commissions'
    _description = 'PAO Sale Order Commissions'

    user_id = fields.Many2one(
        'res.users',
        string='Sales Specialist',
        domain = [('share','=',False)],
        required=True,
    )
    
    source_id = fields.Many2one('commissions.source', string="Source")
    
    commission_percentage = fields.Float(string="Commissions", digits=(3, 2), required=True)
    
    sale_order_id = fields.Many2one(
        'sale.order', 
        string="Sale Order",
    )
    
    @api.onchange('source_id')
    def _onchange_source_id(self):
        self.commission_percentage = 0.0
        if self.source_id and self.source_id.default_percentage:
            self.commission_percentage = self.source_id.default_percentage

class SourceSalesCommissions(models.Model):
    _name="commissions.source"
    _description="Commissions Sources"
    
    name = fields.Char(string="Lead Source", translate=True, required=True)
    default_percentage = fields.Float(string="Default Percentage (%)", digits=(3, 2))
    internal_name = fields.Char('Internal Name')
    company_id = fields.Many2one(
        'res.company', 'Company', copy=False,
        required=True, index=True, default=lambda s: s.env.company)
    
    @api.model_create_multi 
    def create(self, values_list):
        for values in values_list:
            record = super(SourceSalesCommissions, self).create(values)
            
            if not record.internal_name:
                internal_name = record.name.lower().replace(" ", "_")
                record.internal_name = internal_name
                
            return record
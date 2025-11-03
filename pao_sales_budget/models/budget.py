from odoo import models, fields, api
from odoo.exceptions import ValidationError
import calendar


class PAOSalesBudget(models.Model):
    _name = "pao.sales.budget"
    _description = "PAO Annual Sales Budget"


    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', default=2, required=True)
    year = fields.Integer(string='Año', required=True, default=lambda self: fields.Date.context_today(self).year)
    line_ids = fields.One2many('pao.sales.budget.line', 'budget_id', string='Lines', copy=True)

class PAOSalesBudgetLine(models.Model):
    _name = "pao.sales.budget.line"
    _description = "PAO Annual Sales Budget Lines"


    budget_id = fields.Many2one('pao.sales.budget', string='Budget', required=True, ondelete='cascade')
    region_id = fields.Many2one(
        'crm.team', 
        string='Region',
        ondelete='restrict', 
    )
    customer_category = fields.Char(string='Customer Category')
    customer_name = fields.Char(string='Customer Name')
    product_id = fields.Many2one('product.product', string='Producto')
    currency_id = fields.Many2one(related='budget_id.currency_id')
    price_unit = fields.Monetary(string='Precio unitario', currency_field='currency_id')
    total_amount = fields.Monetary(string='Total Amount', compute='_compute_total', currency_field='currency_id', store=True)
    total_quantity = fields.Float(string='Total Quantity', compute='_compute_total', store=True)


    # meses
    m01 = fields.Float("Jan", default=0.0)
    m02 = fields.Float("Feb", default=0.0)
    m03 = fields.Float("Mar", default=0.0)
    m04 = fields.Float("Apr", default=0.0)
    m05 = fields.Float("May", default=0.0)
    m06 = fields.Float("Jun", default=0.0)
    m07 = fields.Float("Jul", default=0.0)
    m08 = fields.Float("Aug", default=0.0)
    m09 = fields.Float("Sep", default=0.0)
    m10 = fields.Float("Oct", default=0.0)
    m11 = fields.Float("Nov", default=0.0)
    m12 = fields.Float("Dec", default=0.0)

   

    @api.depends('m01','m02','m03','m04','m05','m06','m07','m08','m09','m10','m11','m12','price_unit')
    def _compute_total(self):
        for rec in self:
            qty_sum = sum((rec.m01,rec.m02,rec.m03,rec.m04,rec.m05,rec.m06,rec.m07,rec.m08,rec.m09,rec.m10,rec.m11,rec.m12))
            rec.total_amount = qty_sum * (rec.price_unit or 0.0)
            rec.total_quantity = qty_sum


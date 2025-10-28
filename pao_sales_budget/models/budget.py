from odoo import models, fields, api
from odoo.exceptions import ValidationError
import calendar

class VsqBudget(models.Model):
    _name = "vsq.budget"
    _description = "Presupuesto Anual (Normalizado)"
    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    year = fields.Integer(string='Año', required=True, default=lambda self: fields.Date.context_today(self).year)
    line_ids = fields.One2many('vsq.budget.line', 'budget_id', string='Líneas', copy=True)

class VsqBudgetLine(models.Model):
    _name = "vsq.budget.line"
    _description = "Línea presupuesto por producto y mes"
    budget_id = fields.Many2one('vsq.budget', string='Presupuesto', required=True, ondelete='cascade')
    group_id = fields.Char( string='Grupo')  # reemplaza por tu propio modelo de grupo si tienes
    partner_category_id = fields.Char(string='Categoría cliente')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    product_id = fields.Many2one('product.product', string='Producto/Servicio')
    product_type = fields.Selection([('gfs','PrimusGFS'),('org','Organico')], string='Esquema')
    price_unit = fields.Monetary(string='Precio unitario', currency_field='company_currency_id')
    month = fields.Integer(string='Mes (1-12)', required=True)
    qty = fields.Float(string='Cantidad', default=0.0)
    amount = fields.Monetary(string='Importe', compute='_compute_amount', store=True)
    company_currency_id = fields.Many2one('res.currency', string='Moneda',default=2,)

    _sql_constraints = [
        ('unique_line_month', 'unique(budget_id, product_id, partner_id, month)',
         'Ya existe una línea para ese producto/cliente en ese mes para este presupuesto.'),
    ]

    @api.depends('price_unit','qty')
    def _compute_amount(self):
        for rec in self:
            rec.amount = (rec.price_unit or 0.0) * (rec.qty or 0.0)

 


# -------------------------
# Flat model (12 columns)
# -------------------------
class VsqBudgetFlat(models.Model):
    _name = "vsq.budget.flat"
    _description = "Presupuesto Anual (Flat 12 columnas)"
    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    year = fields.Integer(string='Año', required=True, default=lambda self: fields.Date.context_today(self).year)
    line_ids = fields.One2many('vsq.budget.flat.line', 'budget_id', string='Líneas', copy=True)

class VsqBudgetFlatLine(models.Model):
    _name = "vsq.budget.flat.line"
    _description = "Línea flat con 12 meses"
    budget_id = fields.Many2one('vsq.budget.flat', string='Presupuesto', required=True, ondelete='cascade')
    group_id = fields.Char(string='Grupo')
    partner_category_id = fields.Char(string='Categoría cliente')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    product_id = fields.Many2one('product.product', string='Producto/Servicio')
    product_type = fields.Selection([('gfs','PrimusGFS'),('org','Organico')], string='tipo')
    price_unit = fields.Monetary(string='Precio unitario', currency_field='company_currency_id')

    # meses
    m01 = fields.Float("Ene", default=0.0)
    m02 = fields.Float("Feb", default=0.0)
    m03 = fields.Float("Mar", default=0.0)
    m04 = fields.Float("Abr", default=0.0)
    m05 = fields.Float("May", default=0.0)
    m06 = fields.Float("Jun", default=0.0)
    m07 = fields.Float("Jul", default=0.0)
    m08 = fields.Float("Ago", default=0.0)
    m09 = fields.Float("Sep", default=0.0)
    m10 = fields.Float("Oct", default=0.0)
    m11 = fields.Float("Nov", default=0.0)
    m12 = fields.Float("Dic", default=0.0)

    total = fields.Monetary(string='Total', compute='_compute_total', store=True)
    company_currency_id = fields.Many2one('res.currency', string='Moneda',default=2,)

    @api.depends('m01','m02','m03','m04','m05','m06','m07','m08','m09','m10','m11','m12','price_unit')
    def _compute_total(self):
        for rec in self:
            qty_sum = sum((rec.m01,rec.m02,rec.m03,rec.m04,rec.m05,rec.m06,rec.m07,rec.m08,rec.m09,rec.m10,rec.m11,rec.m12))
            rec.total = qty_sum * (rec.price_unit or 0.0)


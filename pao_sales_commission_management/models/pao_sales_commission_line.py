# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PaoSalesCommissionLine(models.Model):
    _name = 'pao.sales.commission.line'
    _description = 'Sales Commission Payable - Product Line Detail'

    commission_id = fields.Many2one(
        comodel_name='pao.sales.commission', string='Commission',
        required=True, ondelete='cascade', index=True,
    )
    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line', string='Quotation Line',
        readonly=True, ondelete='restrict',
    )
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product', readonly=True,
    )
    original_product_uom_qty = fields.Float(
        string='Quantity Sold', readonly=True,
        help='Quantity actually sold on the quotation line at the time '
             'this commission was generated. Reference only, never '
             'changes afterwards.',
    )
    product_uom_qty = fields.Float(
        string='Commissionable Quantity',
        help='Quantity Finance is actually paying commission on. Defaults '
             "to the quantity sold, but can be lowered if the promoter "
             "doesn't earn commission on the full quantity sold. Editing "
             'this never changes the quotation.',
    )
    currency_id = fields.Many2one(
        related='commission_id.currency_cotizacion_id', store=True, readonly=True,
    )
    price_unit = fields.Monetary(
        string='Unit Price', readonly=True, currency_field='currency_id',
    )
    organization_id = fields.Many2one(
        comodel_name='servicereferralagreement.organization', string='Organization',
        readonly=True,
    )
    registrynumber_id = fields.Many2one(
        comodel_name='servicereferralagreement.registrynumber', string='Registration Number',
        readonly=True,
    )
    service_start_date = fields.Date(string='Service Start Date', readonly=True)
    service_end_date = fields.Date(string='Service End Date', readonly=True)
    subtotal = fields.Monetary(
        string='Subtotal', compute='_compute_subtotal', store=True,
        currency_field='currency_id',
    )

    @api.depends('product_uom_qty', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.product_uom_qty * line.price_unit

    @api.constrains('product_uom_qty', 'original_product_uom_qty')
    def _check_product_uom_qty(self):
        for line in self:
            if line.product_uom_qty < 0:
                raise ValidationError(
                    'The commissionable quantity cannot be negative.'
                )
            if line.product_uom_qty > line.original_product_uom_qty:
                raise ValidationError(
                    'The commissionable quantity (%s) cannot be greater '
                    'than the quantity actually sold (%s) on %s.' % (
                        line.product_uom_qty, line.original_product_uom_qty,
                        line.product_id.display_name,
                    )
                )

    def write(self, vals):
        for line in self:
            if line.commission_id.state in ('paid', 'under_review'):
                raise UserError(
                    'You cannot edit a commission line whose commission is '
                    'already Paid or Under Review. Contact Finance if an '
                    'adjustment is required.'
                )
        res = super().write(vals)
        if 'product_uom_qty' in vals:
            for commission in self.mapped('commission_id'):
                commission._update_for_sale_order()
        return res

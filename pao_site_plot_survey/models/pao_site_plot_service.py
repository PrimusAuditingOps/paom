# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class PaoSitePlotService(models.Model):
    _name = 'pao.site.plot.service'
    _description = 'Site Service Estimate (Calidad vs. external counter-offer)'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Cotización',
        required=True,
        ondelete='cascade',
        index=True,
    )
    site_ids = fields.Many2many(
        comodel_name='pao.site.plot',
        string='Sitios',
        domain="[('sale_order_id', '=', sale_order_id)]",
        help='Sitios que comparten este servicio (por ejemplo, dos sitios '
             'cercanos entre sí que se cubren con un solo servicio).',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Servicio',
        required=True,
        domain=[('type', '=', 'service')],
    )
    calidad_qty = fields.Float(string='Cantidad Calidad')
    external_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Proveedor externo',
    )
    external_qty = fields.Float(string='Cantidad contraoferta externa')
    final_qty = fields.Float(string='Cantidad final')
    estimate_source = fields.Selection(
        selection=[
            ('draft', 'Borrador'),
            ('calidad', 'Estimación Calidad'),
            ('external', 'Contraoferta externa'),
            ('final', 'Confirmada'),
        ],
        string='Origen del estimado',
        default='draft',
        required=True,
    )
    sale_order_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Línea de venta',
        ondelete='set null',
        copy=False,
    )

    def action_push_to_order_line(self):
        for rec in self:
            if not rec.final_qty:
                raise UserError(_('Set a final quantity before pushing it to the order line.'))
            if rec.sale_order_line_id:
                rec.sale_order_line_id.product_uom_qty = rec.final_qty
            else:
                line = self.env['sale.order.line'].create({
                    'order_id': rec.sale_order_id.id,
                    'product_id': rec.product_id.id,
                    'product_uom_qty': rec.final_qty,
                })
                rec.sale_order_line_id = line.id
            rec.estimate_source = 'final'

from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    pao_promotor_id = fields.Many2one(
        comodel_name='comisionpromotores.promotor',
        compute='_pao_compute_pao_promotor_id', 
        string="Quotation Consultant", 
        store=True,
    )
    
    pao_promotor_payment = fields.Monetary(
        compute='_get_promotor_id_pay', 
        string='Quotation Consultant Payment',
        store=True,
    )

    @api.depends('invoice_origin')
    def _pao_compute_pao_promotor_id(self):
        for rec in self:
            rec.pao_promotor_id = None
            if rec.invoice_origin:
                sale_order = self.env['sale.order'].search([('name', '=', rec.invoice_origin)], limit=1)
                for sale in sale_order:
                    rec.pao_promotor_id = sale.pao_promotor_id.id
            
    @api.depends('pao_promotor_id')
    def _get_promotor_id_pay(self):
        for rec in self:
            payqty = 0.0
            rec.pao_promotor_payment = 0.00
            if rec.pao_promotor_id.porcentaje and rec.pao_promotor_id.porcentaje > 0:
                for r in rec.invoice_line_ids:
                    if r.product_id.pao_commission_payment:
                        payqty += r.price_subtotal

                rec.pao_promotor_payment = round((payqty * rec.pao_promotor_id.porcentaje) / 100,2)
                
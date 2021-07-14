from odoo import fields, models, api

class AccountMove(models.Model):
    _inherit='account.move'

    promotor_name = fields.Many2one(
        related='partner_id.promotor_id',
    )
    detail_of_operations = fields.Text(
        compute='_get_operations', 
        string='Detail of Operations',
        readonly=True,
    )
    cp_promotor_pay = fields.Monetary(
        compute='_get_promotor_pay', 
        string='Promoter payment',
        readonly=True,
    )   
    def _get_operations(self):
        idproduct = 0
        productqty = 0
        operations = ""
        for rec in self:
            idproduct = 0
            productqty = 0
            operations = ""
            productname = ""
            for r in rec.invoice_line_ids.sorted(key=lambda r: (r.product_id.id)):
                if r.product_id.can_be_commissionable:
                    if not idproduct == 0 and not idproduct == r.product_id.id:
                        if not operations:
                            operations = '{0}-{1}'.format(productqty,productname)
                        else:
                            operations += ', {0}-{1}'.format(productqty,productname)
                        productqty = 0
                    idproduct = r.product_id.id
                    productname = r.product_id.name
                    productqty += r.quantity
            if not idproduct == 0:
                if not operations:
                    operations = '{0}-{1}'.format(productqty,productname)
                else:
                    operations += ', {0}-{1}'.format(productqty,productname)
            rec.detail_of_operations= operations
    
    def _get_promotor_pay(self):
        payqty = 0.0
        for rec in self:
            payqty = 0.0
            if rec.promotor_name.porcentaje and rec.promotor_name.porcentaje > 0:
                for r in rec.invoice_line_ids:
                    if r.product_id.can_be_commissionable:
                        payqty += r.price_subtotal

                rec.cp_promotor_pay = round((payqty * rec.promotor_name.porcentaje) / 100,2)
            else:
                rec.cp_promotor_pay = 0.00
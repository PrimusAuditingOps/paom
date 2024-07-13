from odoo import fields, models




class ResPartner(models.Model):
    _inherit='res.partner'

    pac_product_ids = fields.Many2many('servicereferralagreement.auditproducts',
                                       compute='_get_products',
                                       string='Product Audit',
                                       readonly=True)

    def _get_products(self):
        listproduct = []
        for rec in self:
            domain = [
                ('partner_id', '=', rec.id),
                ('state','!=','cancel')
            ]
            saleordeline = self.env['sale.order'].search(domain).order_line
            for r in saleordeline:
                for p in r.audit_products:
                    if p.id not in listproduct:
                        listproduct.append(p.id)
            rec.pac_product_ids = listproduct
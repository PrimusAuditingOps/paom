from odoo import fields, models, api

class PaoCrVisitsReportServicesProducts(models.Model):
    
    _name = 'pao.cr.visits.report.services.products'
    _description = 'pao cr visits report services products'
    _rec_name='product_id'

    service_id = fields.Many2one(
        string="CR visits reports service id",
        comodel_name='pao.cr.visits.report.services',
        ondelete='cascade',
        index=True,
    )

    sequence = fields.Integer(string='Sequence', default=10)

    product_id = fields.Many2one(
        string="Product",
        required=True,
        comodel_name='product.product',
        ondelete='cascade',
        index=True,
    )

    list_price_product = fields.Float(
        related='product_id.lst_price', 
    )


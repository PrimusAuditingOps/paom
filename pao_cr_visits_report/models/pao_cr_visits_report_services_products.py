from odoo import fields, models, api

class PaoCrVisitsReportServicesProducts(models.Model):
    
    _name = 'pao.cr.visits.report.services.products'
    _description = 'Model for...'
    _rec_name='product_template_id'

    service_id = fields.Many2one(
        string="CR visits reports service id",
        comodel_name='pao.cr.visits.report.services',
        ondelete='delete',
        index=True,
    )

    sequence = fields.Integer(string='Sequence', default=10)

    product_template_id = fields.Many2one(
        string="Product template",
        comodel_name='product.template',
        ondelete='delete',
        index=True,
    )
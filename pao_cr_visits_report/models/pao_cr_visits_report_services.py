from odoo import fields, models, api

class PaoCrVisitsReportServices(models.Model):
    
    _name = 'pao.cr.visits.report.services'
    _description = 'Model for...'

    name = fields.Char(
        string="name",
        required=True,
    )

    product_template_ids = fields.One2many(
        comodel_name='product.template',
        inverse_name='pao_cr_vr_services_id',
        string='Product template ids',
    )
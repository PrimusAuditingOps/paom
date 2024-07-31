from odoo import fields, models, api

class PaoCrVisitsReportServices(models.Model):
    
    _name = 'pao.cr.visits.report.services'
    _description = 'pao cr visits report services'
    
    name = fields.Char(
        string="Name",
        required=True,
    )
    short_name = fields.Char(
        string="Short name",
        required=True,
    )

    products_ids = fields.One2many(
        comodel_name='pao.cr.visits.report.services.products',
        inverse_name='service_id',
        string='Product ids',
    )
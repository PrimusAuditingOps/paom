from odoo import fields, models, api

class PaoCrVisitsReportServices(models.Model):
    
    _name = 'pao.cr.visits.report.services'
    _description = 'Model for...'
    
    name = fields.Char(
        string="Name",
        required=True,
    )
    
    products_ids = fields.One2many(
        comodel_name='pao.cr.visits.report.services.products',
        inverse_name='service_id',
        string='Product ids',
    )
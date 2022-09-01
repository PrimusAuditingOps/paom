from odoo import fields, models
class PaaSchemesRanking(models.Model):
    _name = 'paoassignmentauditor.schemeranking'
    _description = 'Schemes Rankin'
    _rec_name = 'name'

    
    name = fields.Char(
        string = 'Ranking',
        compute = '_get_name'
    )

    def _get_name(self):
        for rec in self:
            rec.name = rec.schem_id.name + ' - '+str(rec.rating)

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Auditor',
        ondelete='set null',
    )

    schem_id = fields.Many2one(
        comodel_name='paa.assignment.auditor.scheme',
        string='Scheme',
        ondelete='set null',
    )

    rating = fields.Float(
        default = 0.00,
        digits=(12,2),
        required = True,
        string= "Rating Scheme",
    )
    

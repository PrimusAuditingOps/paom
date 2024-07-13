from odoo import fields, models



class PaoPromoterHistoryBlock(models.Model):
    _name = 'pao.promoter.history.block'
    _description = 'Promoter history block'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string="Year", required=True)
    history_text = fields.Text(string="Description", required=True,
                               translate=True)
    promotor_cv_id = fields.Many2one('pao.promoter.cv',
                                     string='Promoter CV',
                                     ondelete='cascade')
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company) 
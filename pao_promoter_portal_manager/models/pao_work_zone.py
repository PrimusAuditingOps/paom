from odoo import fields, models, _



class PaoWorkZone(models.Model):
    _name = 'pao.work.zone'
    _description = 'Work Zone'

    _sql_constraints = [
        ('name_unique', 'unique(name)', _('Work Zone already exists!'))
    ]
    name = fields.Char(string="Work Zone", required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company) 
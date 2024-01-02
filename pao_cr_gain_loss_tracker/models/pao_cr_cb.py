from odoo import fields, models, api
class PaoCrCB(models.Model):
    _name = 'pao.cr.cb'
    _description = 'Customer relation CB'
    
    _sql_constraints = [
        ('uc_name_cb',
         'UNIQUE(name)',
         "There is already a CB with this name"),
    ]

    name = fields.Char(
        string="CB",
        help='Enter CB',
        required= True,
    )

    previous_partner_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='pao_previous_cb_id',
        string='Previous partners',
    )

    new_partner_ids = fields.One2many(
        comodel_name='res.partner',
        inverse_name='pao_new_cb_id',
        string='New partners',
    )
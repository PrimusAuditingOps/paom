from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit='res.partner'
 
    pao_old_sales_team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Old Sales Team',
        ondelete='set null',
    )
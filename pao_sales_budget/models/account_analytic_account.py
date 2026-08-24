from odoo import fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    pao_sales_budget_scheme_ids = fields.Many2many(
        'pao.sales.budget.scheme', string='Esquemas',
        help="Esquemas que esta cuenta analítica atiende directamente, para efectos "
             "de costo operativo. Si se deja vacío, esta cuenta se considera personal "
             "de staff/overhead y su presupuesto se reparte entre todos los servicios "
             "sin importar esquema.")

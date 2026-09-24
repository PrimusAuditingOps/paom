from odoo import models, fields


class PAOSalesBudgetDashboardFilter(models.Model):
    _name = 'pao.sales.budget.dashboard.filter'
    _description = 'PAO Sales Budget - Filtro guardado del Dashboard'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    domain = fields.Char(string='Filtro', required=True, default='[]')
    user_id = fields.Many2one('res.users', string='Propietario', required=True,
                              default=lambda self: self.env.user, ondelete='cascade')
    is_shared = fields.Boolean(string='Compartido', default=False,
                               help='Si está marcado, todos los usuarios con acceso al dashboard pueden usar este filtro.')

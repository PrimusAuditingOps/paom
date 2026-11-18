from odoo import api, fields, models


class PAOSeasonFilter(models.Model):
    """Filtro guardado (favorito) de los comparativos por temporada. Es un
    dominio sobre el reporte de origen: sales.invoicing.report (facturación) o
    purchase.report (coordinación)."""
    _name = 'pao.season.filter'
    _description = 'PAO Comparativo por Temporada - Filtro guardado'
    _order = 'name'

    REPORT_MODELS = {
        'billing': 'sales.invoicing.report',
        'coordination': 'purchase.report',
    }

    name = fields.Char(string='Nombre', required=True)
    report_type = fields.Selection([
        ('billing', 'Facturación'),
        ('coordination', 'Coordinación'),
    ], string='Comparativo', required=True, default='billing')
    domain = fields.Char(string='Filtro', required=True, default='[]')
    model_name = fields.Char(compute='_compute_model_name',
                             help='Modelo sobre el que se arma el filtro (lo usa el editor de condiciones).')
    user_id = fields.Many2one('res.users', string='Propietario', required=True,
                              default=lambda self: self.env.user, ondelete='cascade')
    is_shared = fields.Boolean(string='Compartido', default=False,
                               help='Si está marcado, todos los usuarios con acceso a este comparativo pueden usar este filtro.')

    @api.depends('report_type')
    def _compute_model_name(self):
        for rec in self:
            rec.model_name = self.REPORT_MODELS.get(rec.report_type)

from odoo import fields, models

from .billing_report import MONTHS, MONTH_SHORT


class PAOSeasonCoordinationLine(models.TransientModel):
    """Una fila (coordinador, esquema, cliente) del comparativo de coordinación,
    para la interfaz de lista dinámica. Se genera desde el wizard."""
    _name = 'pao.season.coordination.line'
    _description = 'PAO Comparativo de Coordinación por Temporada - Línea'
    _order = 'coordinator_id, scheme_id, partner_id'

    wizard_id = fields.Many2one('pao.season.coordination.wizard', string='Wizard',
                                required=True, ondelete='cascade', index=True)
    coordinator_id = fields.Many2one('res.users', string='Coordinador')
    scheme_id = fields.Many2one('pao.sales.budget.scheme', string='Esquema')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    group_id = fields.Many2one('customergroups.group', string='Grupo')
    promotor_id = fields.Many2one('comisionpromotores.promotor', string='Promotor')
    region_id = fields.Many2one('crm.team', string='Región')
    status = fields.Selection([
        ('kept', 'Sigue coordinando'),
        ('lost', 'Dejó de coordinar'),
        ('new', 'Nuevo coordinado'),
    ], string='Estatus')

    qty_a = fields.Float(string='Cant. Temp. A')
    qty_b = fields.Float(string='Cant. Temp. B')
    diff_qty = fields.Float(string='Dif. Cant. (B - A)')
    # Un porcentaje no se puede sumar al agrupar, por eso sin group_operator.
    var_qty = fields.Float(string='Var Cant.', group_operator=False)

    # Detalle mensual: m09_a, m09_b, ... (24 campos)
    for _mm, _month_label in MONTHS:
        vars()['m%s_a' % _mm] = fields.Float(string='%s Cant. A' % MONTH_SHORT[_mm])
        vars()['m%s_b' % _mm] = fields.Float(string='%s Cant. B' % MONTH_SHORT[_mm])
    del _mm, _month_label

from odoo import fields, models

from .billing_report import MONTHS, MONTH_SHORT


class PAOSeasonBillingLine(models.TransientModel):
    """Una fila (esquema, cliente) del comparativo, para la interfaz de lista
    dinámica. Se genera desde el wizard y se limpia sola (transient)."""
    _name = 'pao.season.billing.line'
    _description = 'PAO Comparativo de Facturación por Temporada - Línea'
    _order = 'scheme_id, partner_id'

    wizard_id = fields.Many2one('pao.season.billing.wizard', string='Wizard',
                                required=True, ondelete='cascade', index=True)
    scheme_id = fields.Many2one('pao.sales.budget.scheme', string='Esquema')
    partner_id = fields.Many2one('res.partner', string='Cliente')
    group_id = fields.Many2one('customergroups.group', string='Grupo')
    promotor_id = fields.Many2one('comisionpromotores.promotor', string='Promotor')
    region_id = fields.Many2one('crm.team', string='Región')
    status = fields.Selection([
        ('kept', 'Sigue comprando'),
        ('lost', 'Dejó de comprar'),
        ('new', 'Nuevo / Recuperado'),
    ], string='Estatus')

    qty_a = fields.Float(string='Cant. Temp. A')
    amt_a = fields.Float(string='USD Temp. A')
    qty_b = fields.Float(string='Cant. Temp. B')
    amt_b = fields.Float(string='USD Temp. B')
    diff_qty = fields.Float(string='Dif. Cant. (B - A)')
    diff_amt = fields.Float(string='Dif. USD (B - A)')
    # Un porcentaje no se puede sumar al agrupar, por eso sin group_operator.
    var_qty = fields.Float(string='Var Cant.', group_operator=False)
    var_amt = fields.Float(string='Var $', group_operator=False)

    # Detalle mensual: m09_qty_a, m09_amt_a, m09_qty_b, m09_amt_b, ... (48 campos)
    for _mm, _name in MONTHS:
        vars()['m%s_qty_a' % _mm] = fields.Float(string='%s Cant. A' % MONTH_SHORT[_mm])
        vars()['m%s_amt_a' % _mm] = fields.Float(string='%s USD A' % MONTH_SHORT[_mm])
        vars()['m%s_qty_b' % _mm] = fields.Float(string='%s Cant. B' % MONTH_SHORT[_mm])
        vars()['m%s_amt_b' % _mm] = fields.Float(string='%s USD B' % MONTH_SHORT[_mm])
    del _mm, _name

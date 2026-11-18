from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class PAOSeasonFilterMixin(models.AbstractModel):
    """Filtro avanzado (editor de condiciones) con favoritos, compartido por los
    wizards de los comparativos. Cada wizard define sobre qué reporte se arma
    el filtro (_season_filter_model) y de qué tipo son sus favoritos
    (_season_filter_type)."""
    _name = 'pao.season.filter.mixin'
    _description = 'PAO Comparativo por Temporada - Filtro avanzado'

    _season_filter_model = None
    _season_filter_type = None

    filter_domain = fields.Char(
        string='Filtro avanzado', default='[]',
        help='Condiciones sobre el reporte de origen (producto, cliente, equipo, etc.). '
             'Se aplican junto con los demás filtros.')
    saved_filter_id = fields.Many2one('pao.season.filter', string='Filtro guardado')
    new_filter_name = fields.Char(string='Guardar filtro como')

    @api.onchange('saved_filter_id')
    def _onchange_saved_filter_id(self):
        if self.saved_filter_id:
            self.filter_domain = self.saved_filter_id.domain

    def _parse_filter_domain(self):
        self.ensure_one()
        try:
            return list(safe_eval(self.filter_domain or '[]'))
        except Exception:
            raise UserError(_('El filtro avanzado no es válido.'))

    def action_save_filter(self):
        self.ensure_one()
        name = (self.new_filter_name or '').strip()
        if not name:
            raise UserError(_('Escribe un nombre para guardar el filtro.'))
        if not self._parse_filter_domain():
            raise UserError(_('No hay condiciones que guardar.'))
        self.saved_filter_id = self.env['pao.season.filter'].create({
            'name': name,
            'report_type': self._season_filter_type,
            'domain': self.filter_domain,
        })
        self.new_filter_name = False
        return True

    def _filter_ids_sql(self):
        """Subconsulta SQL (ya con los valores incluidos y los '%' escapados para
        cr.execute) con los ids del reporte de origen que cumplen el filtro
        avanzado, o '' si no hay filtro. Se usa como `AND <alias>.id IN (...)`.
        """
        self.ensure_one()
        domain = self._parse_filter_domain()
        if not domain:
            return ''
        Model = self.env[self._season_filter_model].sudo()
        try:
            select = Model._where_calc(domain).select()
        except Exception as e:
            raise UserError(_('El filtro avanzado no se pudo aplicar: %s') % e)
        # Según el build de Odoo 17, select() regresa un objeto SQL o una tupla.
        code, params = select if isinstance(select, tuple) else (select.code, select.params)
        return self.env.cr.mogrify(code, params or None).decode().replace('%', '%%')

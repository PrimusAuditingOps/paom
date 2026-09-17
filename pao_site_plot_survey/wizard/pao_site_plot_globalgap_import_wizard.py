# -*- coding: utf-8 -*-
"""Importer for the company's alternate site-capture format, "Estimación de
duración de auditorías GLOBALG.A.P." — a spreadsheet with a client/project
header block followed by a per-site table (Nombre del sitio, Cultivo, Zona,
Superficie (ha), Coordenadas, Distancia (min) Ida y vuelta PHU). Coordenadas
is a single cell holding both lat and lon together, usually in
degrees/minutes/seconds (e.g. 25°19'43.59"N 111°40'41.52"W).

Kept as its own wizard/button (rather than folded into the standard
Excel/KML importer) since it's a distinct template the client sends only
sometimes, with its own header layout and an extra "Distancia PHU" column
that the standard format doesn't have.
"""
import base64
import io
import json

from odoo import fields, models, _
from odoo.exceptions import UserError

from . import pao_coordinate_utils as coord_utils

try:
    import openpyxl
except ImportError:
    openpyxl = None

# Candidate header substrings per logical column, tried in order, tolerant of
# accent/casing/spacing variations across different exports of this same
# GLOBALG.A.P. template.
GLOBALGAP_COLUMN_MARKERS = {
    'name': ['NOMBRE DEL SITIO', 'NOMBRE DE SITIO', 'NOMBRE SITIO', 'NOMBRE'],
    'variety': ['CULTIVO'],
    'location': ['ZONA'],
    'declared_ha': ['SUPERFICIE'],
    'coords': ['COORDENADAS'],
    'travel_time': ['DISTANCIA'],
}


class PaoSitePlotGlobalgapImportWizard(models.TransientModel):
    _name = 'pao.site.plot.globalgap.import.wizard'
    _description = 'Importar sitios desde el formato GLOBALG.A.P. (estimación de duración de auditorías)'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Cotización',
        required=True,
        default=lambda self: self.env.context.get('active_id'),
    )
    import_file = fields.Binary(string='Archivo (.xlsx)', required=True, attachment=True)
    file_name = fields.Char(string='Nombre del archivo')
    state = fields.Selection(
        selection=[('draft', 'Listo'), ('preview', 'Vista previa'), ('done', 'Importado')],
        default='draft',
    )
    preview_html = fields.Html(string='Vista previa', readonly=True)
    total_rows = fields.Integer(string='Total de filas leídas', readonly=True)
    valid_rows = fields.Integer(string='Filas válidas', readonly=True)
    error_rows = fields.Integer(string='Filas con error', readonly=True)
    parsed_rows = fields.Text()

    # ── Preview ────────────────────────────────────────────────────────────
    def action_preview(self):
        self.ensure_one()
        if not openpyxl:
            raise UserError(_('The openpyxl library is not installed on the server.'))
        rows, errors = self._parse_excel()

        self.total_rows = len(rows) + len(errors)
        self.valid_rows = len(rows)
        self.error_rows = len(errors)
        self.parsed_rows = json.dumps(rows)
        self.preview_html = self._render_preview_html(rows, errors)
        self.state = 'preview'
        return self._reopen()

    def _render_preview_html(self, rows, errors):
        html = [
            '<div style="overflow-x:auto; max-width:100%;">'
            '<table class="table table-sm table-bordered" '
            'style="font-size:12px; white-space:nowrap; width:auto;">'
        ]
        html.append(
            '<thead class="table-dark"><tr>'
            '<th>#</th><th>Sitio</th><th>Cultivo</th><th>Zona</th>'
            '<th>Superficie (HA)</th><th>Latitud</th><th>Longitud</th>'
            '<th>Distancia PHU (min)</th></tr></thead><tbody>'
        )
        for i, row in enumerate(rows[:20], 1):
            html.append(
                '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
                '<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
                    i,
                    row.get('name', ''),
                    row.get('variety', ''),
                    row.get('location', ''),
                    row.get('declared_ha', ''),
                    row.get('lat', ''),
                    row.get('lng', ''),
                    row.get('travel_time', ''),
                )
            )
        if len(rows) > 20:
            html.append(
                '<tr><td colspan="8" class="text-center text-muted">%s</td></tr>'
                % (_('… y %d filas más') % (len(rows) - 20))
            )
        html.append('</tbody></table></div>')
        if errors:
            html.append('<div class="alert alert-warning mt-2"><b>%s</b><ul>' % _('Filas con problemas:'))
            for err in errors:
                html.append('<li>%s</li>' % err)
            html.append('</ul></div>')
        return ''.join(html)

    # ── Import ─────────────────────────────────────────────────────────────
    def action_import(self):
        self.ensure_one()
        rows = json.loads(self.parsed_rows or '[]')
        if not rows:
            raise UserError(_('No valid rows were found to import.'))

        Site = self.env['pao.site.plot']
        for row in rows:
            Site.create({
                'sale_order_id': self.sale_order_id.id,
                'name': row.get('name') or _('Sin nombre'),
                'variety': row.get('variety') or '',
                'location': row.get('location') or '',
                'declared_surface_ha': row.get('declared_ha') or 0.0,
                'center_lat': row.get('lat'),
                'center_lng': row.get('lng'),
                'travel_time_phu_minutes': row.get('travel_time') or 0.0,
                'source': 'globalgap_import',
            })
        self.state = 'done'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import complete'),
                'message': _('%d sites imported.') % len(rows),
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    # ── Excel branch ─────────────────────────────────────────────────────────
    def _parse_excel(self):
        try:
            content = base64.b64decode(self.import_file)
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        except Exception as e:
            raise UserError(_('Could not read the Excel file: %s') % str(e))
        ws = wb.active

        header_row_idx, col_index = self._find_header(ws)
        if header_row_idx is None:
            raise UserError(
                _('Could not find the site table header (Nombre del sitio, Cultivo, '
                  'Superficie (ha), Coordenadas...). Make sure the GLOBALG.A.P. sheet is active.')
            )
        if 'coords' not in col_index:
            raise UserError(_('Could not find the "Coordenadas" column.'))

        rows = []
        errors = []
        for i, excel_row in enumerate(
            ws.iter_rows(min_row=header_row_idx + 1, values_only=True),
            start=header_row_idx + 1,
        ):
            if not any(c is not None for c in excel_row):
                continue
            name = self._cell(excel_row, col_index.get('name'))
            if not name:
                continue
            coords_raw = self._cell(excel_row, col_index.get('coords'))
            if not coords_raw:
                # No coordinates at all (not even a bad value to report) -
                # this is trailing free text below the table (a "Nota:..."
                # footer, an instruction line...), not a real site row.
                continue
            try:
                lat, lng = coord_utils.parse_combined_point(coords_raw)
                rows.append({
                    'name': name,
                    'variety': self._cell(excel_row, col_index.get('variety')),
                    'location': self._cell(excel_row, col_index.get('location')),
                    'declared_ha': self._cell_float(excel_row, col_index.get('declared_ha')),
                    'travel_time': self._cell_float(excel_row, col_index.get('travel_time')),
                    'lat': lat,
                    'lng': lng,
                    'geojson': None,
                })
            except (ValueError, IndexError) as e:
                errors.append(_('Row %d: "%s" — invalid coordinates (%s).') % (i, name, e))
        return rows, errors

    @staticmethod
    def _find_header(ws, max_scan_rows=30):
        # The real per-site table sits below a client/project metadata block
        # of variable length, so scan further down than the standard
        # importer needs to before giving up.
        for row_idx, row in enumerate(
            ws.iter_rows(min_row=1, max_row=max_scan_rows, values_only=True), start=1
        ):
            normalized = [str(c).strip().upper() if c else '' for c in row]
            has_name = any(marker in cell for cell in normalized for marker in GLOBALGAP_COLUMN_MARKERS['name'])
            has_coords = any(marker in cell for cell in normalized for marker in GLOBALGAP_COLUMN_MARKERS['coords'])
            if has_name and has_coords:
                col_index = {}
                for key, markers in GLOBALGAP_COLUMN_MARKERS.items():
                    for marker in markers:
                        found = False
                        for idx, cell in enumerate(normalized):
                            if marker in cell:
                                col_index[key] = idx
                                found = True
                                break
                        if found:
                            break
                return row_idx, col_index
        return None, {}

    @staticmethod
    def _cell(row, idx):
        if idx is None or idx >= len(row) or row[idx] is None:
            return ''
        return str(row[idx]).strip()

    @staticmethod
    def _cell_float(row, idx):
        if idx is None or idx >= len(row) or row[idx] is None:
            return 0.0
        try:
            return float(row[idx])
        except (TypeError, ValueError):
            return 0.0

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

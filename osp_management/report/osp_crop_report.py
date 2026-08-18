# -*- coding: utf-8 -*-
"""
Lógica del reporte PDF del formulario Crop. Traduce form_data (el JSON
plano con las respuestas del cliente) + CROP_REPORT_SECTIONS (la lista de
preguntas, ver osp_crop_report_data.py) a una estructura ya lista para
que el template QWeb (report/osp_report_templates.xml) solo la recorra e
imprima — así el template no tiene que saber nada de tipos de campo,
Selection, Many2one, ni JSON de tablas dinámicas.
"""

import json

from odoo import models

from .osp_crop_report_data import CROP_REPORT_SECTIONS

YN_OPTIONS = ['Yes', 'No']
YNNA_OPTIONS = ['Yes', 'No', 'N/A']


class OSPRequestReport(models.Model):
    _inherit = 'osp.request'

    def _report_lookup_name(self, model, res_id):
        """Para campos m2o_state/m2o_country: form_data solo guarda el id
        (como string) del select — aquí se resuelve a su nombre real."""
        if not res_id:
            return ''
        try:
            record = self.env[model].sudo().browse(int(res_id))
            return record.name if record.exists() else ''
        except (ValueError, TypeError):
            return ''

    def _report_parse_table(self, raw_json):
        """Decodifica el JSON de una tabla dinámica y descarta filas
        completamente vacías (el JS del formulario siempre deja al menos
        una fila en blanco lista para editar, que no aporta nada en el PDF)."""
        try:
            rows = json.loads(raw_json) if raw_json else []
        except (ValueError, TypeError):
            rows = []

        def is_empty_row(row):
            return not any((str(v).strip() if v is not None else '') for v in row.values())

        return [row for row in rows if isinstance(row, dict) and not is_empty_row(row)]

    def get_crop_report_sections(self):
        """Devuelve la lista de secciones ya resuelta contra self.form_data,
        lista para que el template QWeb del reporte solo la recorra."""
        self.ensure_one()
        data = self.form_data or {}
        sections = []

        for section in CROP_REPORT_SECTIONS:
            fields_out = []
            for field in section['fields']:
                ftype = field['type']

                if ftype == 'static':
                    fields_out.append({'kind': 'static', 'text': field['text']})
                    continue

                key = field['key']
                label = field['label']
                value = data.get(key)

                if ftype in ('text', 'date'):
                    fields_out.append({'kind': 'text', 'label': label, 'value': value or ''})
                elif ftype == 'textarea':
                    fields_out.append({'kind': 'textarea', 'label': label, 'value': value or ''})
                elif ftype == 'yn':
                    fields_out.append({'kind': 'options', 'label': label, 'options': YN_OPTIONS, 'value': value or ''})
                elif ftype == 'yn_na':
                    fields_out.append({'kind': 'options', 'label': label, 'options': YNNA_OPTIONS, 'value': value or ''})
                elif ftype == 'checkbox':
                    fields_out.append({'kind': 'checkbox', 'label': label, 'checked': bool(value)})
                elif ftype == 'checkbox_group':
                    fields_out.append({'kind': 'checkbox_group', 'label': label, 'selected': value or []})
                elif ftype == 'm2o_state':
                    fields_out.append({'kind': 'text', 'label': label, 'value': self._report_lookup_name('res.country.state', value)})
                elif ftype == 'm2o_country':
                    fields_out.append({'kind': 'text', 'label': label, 'value': self._report_lookup_name('res.country', value)})
                elif ftype == 'table':
                    fields_out.append({
                        'kind': 'table',
                        'label': label,
                        'columns': field['columns'],
                        'rows': self._report_parse_table(value),
                    })

            sections.append({'title': section['title'], 'fields': fields_out})

        return sections

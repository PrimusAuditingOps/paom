# -*- coding: utf-8 -*-
"""
Motor GENÉRICO del reporte PDF, compartido por todos los tipos de
formulario (Crop, Handler, y los que se construyan a futuro). Antes este
código vivía duplicado dentro de osp_crop_report.py; se extrajo aquí al
construir Handler para no repetir el mismo switch de tipos de campo por
cada formulario nuevo — ver CONTEXT.md, punto 15, "lo primero que hay que
generalizar cuando se construya el segundo formulario".

Cada formulario solo necesita:
  1. Su propio manifest de secciones (osp_<nombre>_report_data.py), mismo
     formato que CROP_REPORT_SECTIONS/HANDLER_REPORT_SECTIONS.
  2. Un método de una línea `get_<nombre>_report_sections()` que llame a
     `self._resolve_report_sections(<NOMBRE>_REPORT_SECTIONS)`.
`get_report_sections()` (usado por el template QWeb del reporte) despacha
solo, por convención de nombre, a partir de `form_template_id.technical_code`
— no hace falta tocar este archivo ni el template al agregar un formulario.
"""

import json

from odoo import models

YN_OPTIONS = ['Yes', 'No']
YNNA_OPTIONS = ['Yes', 'No', 'N/A']


class OSPRequestReportCommon(models.Model):
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

    def _report_fixed_rows(self, field, data):
        """Para secciones con un número FIJO de filas armadas desde varias
        claves sueltas de form_data en vez de un solo blob JSON (ej. la
        tabla Storage de Handler, Sección 7b: 4 categorías fijas —
        Ingredients/Finished Goods/Packaging Materials/Other — cada una
        guardada como '7b_<row_key>_<columna>'). No usa _report_parse_table
        porque no hay JSON que decodificar."""
        rows = []
        for row_def in field['rows']:
            row_key = row_def['key']
            label_key = row_def.get('label_key')
            row_label = data.get(label_key) if label_key else row_def.get('label')
            row = {'__label': row_label or row_key}
            for col_key, _col_header in field['columns']:
                row[col_key] = data.get('%s_%s_%s' % (field['prefix'], row_key, col_key), '')
            rows.append(row)
        return rows

    def _resolve_report_sections(self, sections_manifest):
        """Motor genérico: resuelve un manifest de secciones (mismo formato
        que CROP_REPORT_SECTIONS/HANDLER_REPORT_SECTIONS) contra
        self.form_data, listo para que el template QWeb solo lo recorra."""
        self.ensure_one()
        data = self.form_data or {}
        sections = []

        for section in sections_manifest:
            fields_out = []
            for field in section['fields']:
                ftype = field['type']

                if ftype == 'static':
                    fields_out.append({'kind': 'static', 'text': field['text']})
                    continue

                label = field.get('label')

                if ftype == 'fixed_rows':
                    fields_out.append({
                        'kind': 'table',
                        'label': label,
                        'columns': [('__label', field.get('row_header', 'Category'))] + field['columns'],
                        'rows': self._report_fixed_rows(field, data),
                    })
                    continue

                key = field['key']
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

    def get_report_sections(self):
        """Punto de entrada único que usa el template QWeb del reporte.
        Despacha por convención de nombre a partir del technical_code
        (ej. 'form_handler' -> get_handler_report_sections()) — agregar un
        formulario nuevo no requiere tocar este método ni el template."""
        self.ensure_one()
        technical_code = self.form_template_id.technical_code or ''
        suffix = technical_code[len('form_'):] if technical_code.startswith('form_') else technical_code
        method = getattr(self, 'get_%s_report_sections' % suffix, None) if suffix else None
        return method() if method else []

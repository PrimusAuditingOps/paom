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

# Retro de usuario piloto: el PDF imprimía literalmente "Yes"/"No"/"N/A"
# en los 3 formularios en español (el motor solo conocía el valor guardado
# en form_data, siempre en inglés — "Sí"/"No" son solo la etiqueta que
# muestra el HTML del formulario web, el PDF nunca tuvo acceso a eso).
# Cada opción es una tupla (valor_guardado, etiqueta_a_mostrar) — mismo
# patrón que ya se usa para las columnas de las tablas ('columns': [(key,
# header), ...]) — así el valor interno para comparar "¿está marcado?"
# sigue siendo el de siempre (inglés), y solo cambia lo que se imprime.
YN_OPTIONS_EN = [('Yes', 'Yes'), ('No', 'No')]
YN_OPTIONS_ES = [('Yes', 'Sí'), ('No', 'No')]
YNNA_OPTIONS_EN = [('Yes', 'Yes'), ('No', 'No'), ('N/A', 'N/A')]
YNNA_OPTIONS_ES = [('Yes', 'Sí'), ('No', 'No'), ('N/A', 'N/A')]

# Mismos 3 formularios nativos en español reconocidos en todo el módulo
# (ver SPANISH_FORMS en static/src/js/osp_form.js).
SPANISH_FORM_CODES = ['form_manejo_proceso', 'form_comercializador', 'form_cultivo']


class OSPRequestReportCommon(models.Model):
    _inherit = 'osp.request'

    def _report_is_spanish(self):
        """True si el formulario es uno de los 3 nativos en español
        (Manejo o Proceso, Comercializador, Cultivo) — determina si las
        opciones Sí/No/N/A del PDF se imprimen en español o en inglés."""
        return (self.form_template_id.technical_code or '') in SPANISH_FORM_CODES

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

        return [self._report_localize_yn_cells(row) for row in rows
                if isinstance(row, dict) and not is_empty_row(row)]

    def _report_localize_yn_cells(self, row):
        """Los selects Y/N de las tablas dinámicas guardan 'Y'/'N' (valor
        interno estable) pero muestran Sí/No (o Yes/No) en pantalla; aquí
        el PDF imprime la misma etiqueta visible en vez del valor crudo."""
        labels = {'Y': 'Sí', 'N': 'No', 'Yes': 'Sí'} if self._report_is_spanish() else {'Y': 'Yes', 'N': 'No'}
        return {k: labels.get(v, v) if isinstance(v, str) else v for k, v in row.items()}

    def _report_show_if_met(self, condition, data):
        """condition: None (siempre se muestra, comportamiento de siempre)
        o {'field': <key>, 'value': <valor esperado>} — mismo concepto que
        data-conditional-field/data-conditional-value en el HTML (ver
        osp-conditional en osp_form.js). 'data' es el dict contra el que se
        evalúa: form_data completo para un campo normal, o la entrada
        individual (entry) para un subfield de 'repeatable'.

        El campo controlador puede ser un 'checkbox_group' (ej. "marque
        todas las que apliquen"), cuyo valor en form_data es una LISTA de
        opciones marcadas, no un string único — a diferencia de un radio o
        un select. Si el valor guardado es una lista, se revisa que el
        valor esperado esté DENTRO de ella; si no, se compara igual que
        siempre (==)."""
        if not condition:
            return True
        current = data.get(condition['field'])
        if isinstance(current, list):
            return condition['value'] in current
        return current == condition['value']

    def _report_repeatable_entries(self, field, raw_json):
        """Decodifica un campo 'repeatable' (ej. Sección 19: varios campos
        nuevos, cada uno con su propio set de preguntas + su propia tabla
        año-por-año anidada — ver Sección 19 en osp_crop_report_data.py).
        A diferencia de 'table' (filas planas de un solo tipo de celda),
        cada entrada aquí es una mini-lista de sub-campos de distinto tipo
        (texto/sí-no/checkbox/tabla), resuelta con el mismo switch que
        _resolve_report_sections() usa para los campos normales de nivel
        superior — así una entrada nueva de subfields no requiere tocar
        el motor, solo el manifest."""
        try:
            entries = json.loads(raw_json) if raw_json else []
        except (ValueError, TypeError):
            entries = []

        entries_out = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            subfields_out = []
            for subfield in field['subfields']:
                if not self._report_show_if_met(subfield.get('show_if'), entry):
                    continue
                sftype = subfield['type']
                svalue = entry.get(subfield['key'])
                slabel = subfield.get('label')
                if sftype in ('text', 'date'):
                    subfields_out.append({'kind': 'text', 'label': slabel, 'value': svalue or ''})
                elif sftype == 'yn':
                    yn_options = YN_OPTIONS_ES if self._report_is_spanish() else YN_OPTIONS_EN
                    subfields_out.append({'kind': 'options', 'label': slabel, 'options': yn_options, 'value': svalue or ''})
                elif sftype == 'checkbox':
                    subfields_out.append({'kind': 'checkbox', 'label': slabel, 'checked': svalue == 'X'})
                elif sftype == 'table':
                    rows = svalue if isinstance(svalue, list) else []
                    rows = [self._report_localize_yn_cells(r) for r in rows
                            if isinstance(r, dict) and any((str(v).strip() if v is not None else '') for v in r.values())]
                    subfields_out.append({'kind': 'table', 'label': slabel, 'columns': subfield['columns'], 'rows': rows})
            # Entrada completamente vacía (usuario nunca la llenó): se
            # descarta, mismo criterio que _report_parse_table() con las
            # filas de las tablas planas.
            if any(sf.get('value') or sf.get('checked') or sf.get('rows') for sf in subfields_out):
                entries_out.append(subfields_out)
        return entries_out

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
            # Retro de usuario piloto: si el cliente deja vacío el campo de
            # texto libre (ej. "Categoría" de la fila "Otro"), el fallback
            # ANTES caía en row_key — el nombre técnico interno en inglés
            # ("other") — en vez de una etiqueta real. Ahora usa row_def
            # ['label'] (la etiqueta ya traducida que trae cada manifest)
            # como fallback antes de llegar a row_key.
            row_label = (data.get(label_key) if label_key else None) or row_def.get('label')
            row = {'__label': row_label or row_key}
            for col_key, _col_header in field['columns']:
                row[col_key] = data.get('%s_%s_%s' % (field['prefix'], row_key, col_key), '')
            rows.append(self._report_localize_yn_cells(row))
        return rows

    def _report_option_label(self, options, value):
        """Busca 'value' dentro de una lista de opciones [(valor_guardado,
        etiqueta_a_mostrar), ...] (mismo patrón que YN_OPTIONS_ES/EN y que
        las columnas de tabla) y devuelve la etiqueta correspondiente. Si
        no hay match (valor vacío, o un valor viejo que ya no está en la
        lista de opciones actual), devuelve el valor crudo tal cual —
        mejor mostrar el dato viejo en inglés que no mostrar nada."""
        if not value:
            return ''
        for opt_value, opt_label in options:
            if opt_value == value:
                return opt_label
        return value

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
                # 'show_if' (opcional, cualquier tipo de campo): mismo
                # concepto que osp-conditional/data-conditional-field en el
                # HTML del formulario — antes, el PDF imprimía TODOS los
                # campos del manifest sin importar si la pregunta de la que
                # dependen en realidad los reveló (retro de usuario piloto:
                # ej. "Si no, explique" salía vacío aunque la respuesta
                # hubiera sido "Sí"). Si no coincide, el campo se omite del
                # PDF por completo — no se agrega ni siquiera vacío.
                if not self._report_show_if_met(field.get('show_if'), data):
                    continue

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
                elif ftype == 'select':
                    # Retro de usuario piloto: un <select>/radio guarda un
                    # valor interno en inglés aunque el HTML muestre una
                    # etiqueta en español — el PDF (que solo conoce el
                    # valor guardado) imprimía ese valor crudo en vez de la
                    # etiqueta. 'options' (obligatorio para este tipo) es
                    # la misma lista [(valor, etiqueta)] que el manifest ya
                    # trae para reconstruir el <select> si hiciera falta.
                    fields_out.append({'kind': 'text', 'label': label, 'value': self._report_option_label(field['options'], value)})
                elif ftype == 'textarea':
                    fields_out.append({'kind': 'textarea', 'label': label, 'value': value or ''})
                elif ftype == 'yn':
                    yn_options = YN_OPTIONS_ES if self._report_is_spanish() else YN_OPTIONS_EN
                    fields_out.append({'kind': 'options', 'label': label, 'options': yn_options, 'value': value or ''})
                elif ftype == 'yn_na':
                    ynna_options = YNNA_OPTIONS_ES if self._report_is_spanish() else YNNA_OPTIONS_EN
                    fields_out.append({'kind': 'options', 'label': label, 'options': ynna_options, 'value': value or ''})
                elif ftype == 'checkbox':
                    fields_out.append({'kind': 'checkbox', 'label': label, 'checked': bool(value)})
                elif ftype == 'image':
                    # Firma a mano (retro de usuario piloto): se guarda como
                    # PNG en base64 (data URL) — wkhtmltopdf imprime data:
                    # URIs de imagen sin problema, no hace falta subirla
                    # como ir.attachment aparte.
                    fields_out.append({'kind': 'image', 'label': label, 'value': value or ''})
                elif ftype == 'checkbox_group':
                    # 'options' es opcional (retrocompatible): si el campo
                    # ya trae la lista [(valor, etiqueta)], cada valor
                    # marcado se resuelve a su etiqueta en español antes de
                    # imprimir — mismo problema y mismo mecanismo que
                    # 'select' de arriba, pero aquí el valor guardado es
                    # una LISTA (varias opciones marcadas), no uno solo.
                    selected = value or []
                    options = field.get('options')
                    if options:
                        selected = [self._report_option_label(options, v) for v in selected]
                    fields_out.append({'kind': 'checkbox_group', 'label': label, 'selected': selected})
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
                elif ftype == 'repeatable':
                    fields_out.append({
                        'kind': 'repeatable',
                        'label': label,
                        'entries': self._report_repeatable_entries(field, value),
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

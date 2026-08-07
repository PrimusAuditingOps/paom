import base64
import io
import logging
from datetime import datetime, date

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date):
        return value if not isinstance(value, datetime) else value.date()
    if isinstance(value, str):
        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%m-%d-%Y'):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
    return None


class SurveyImportWizard(models.TransientModel):
    _name = 'survey.import.wizard'
    _description = 'Audit import wizard from XLSX'

    survey_id = fields.Many2one(
        'survey.survey',
        string='Survey',
        required=True,
        ondelete='cascade',
    )
    file_data = fields.Binary(string='Xlsx File', required=True)
    file_name = fields.Char(string='File Name')

    # Estado para controlar el paso del wizard (upload → confirm → done)
    wizard_state = fields.Selection(
        selection=[
            ('upload', 'Upload file'),
            ('confirm', 'Confirm sending'),
        ],
        default='upload',
        required=True,
    )

    # Resumen previo a confirmación
    preview_total = fields.Integer(string='Total records', readonly=True)
    preview_emails = fields.Integer(string='Total emails to send', readonly=True)
    preview_html = fields.Html(string='Preview', readonly=True)

    # Paso 1: cargar y analizar el archivo
    def action_load_preview(self):
        """Lee el archivo xlsx y muestra un resumen para confirmación."""
        self.ensure_one()
        if not self.file_data:
            raise UserError(_('Please select an XLSX file before continuing.'))

        rows, headers = self._read_xlsx()
        if not rows:
            raise UserError(_('The file does not contain data or could not be read correctly.'))

        parsed = self._parse_rows(headers, rows)
        total_records = len(parsed)
        total_emails = sum(len(r['emails']) for r in parsed)

        # Genera tabla HTML de previsualización (primeras 10 filas)
        preview_rows = parsed[:10]
        html = self._build_preview_html(preview_rows, total_records, total_emails)

        self.write({
            'wizard_state': 'confirm',
            'preview_total': total_records,
            'preview_emails': total_emails,
            'preview_html': html,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    # Paso 2: confirmar e importar
    def action_import_and_send(self):
        """Crea los user_input y envía los correos."""
        self.ensure_one()
        rows, headers = self._read_xlsx()
        if not rows:
            raise UserError(_('The file does not contain valid data.'))

        parsed = self._parse_rows(headers, rows)
        if not parsed:
            raise UserError(_('No valid records with email addresses found.'))

        survey = self.survey_id
        created_inputs = self.env['survey.user_input']

        for record in parsed:
            user_input = self._create_user_input(survey, record)
            created_inputs |= user_input
            self._send_emails(survey, user_input, record)

        # Redirige a la lista de participantes de la encuesta
        return {
            'type': 'ir.actions.act_window',
            'name': _('Participations'),
            'res_model': 'survey.user_input',
            'view_mode': 'tree,form',
            'domain': [('survey_id', '=', survey.id), ('imported_from_file', '=', True)],
            'context': {'default_survey_id': survey.id},
        }

    def _read_xlsx(self):
        """Carga el archivo xlsx y devuelve (rows, headers)."""
        try:
            import openpyxl  # type: ignore
        except ImportError:
            raise UserError(_(
                'The openpyxl library is not installed. '
                'Run: pip install openpyxl --break-system-packages'
            ))

        raw = base64.b64decode(self.file_data)
        fname = (self.file_name or '').lower()

        try:
            if fname.endswith('.csv'):
                import csv
                text = raw.decode('utf-8-sig', errors='replace')
                reader = list(csv.reader(io.StringIO(text)))
                if len(reader) < 2:
                    return [], []
                headers   = [str(c).strip() for c in reader[0]]
                data_rows = [tuple(r) for r in reader[1:]]
            else:
                wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
                if len(rows) < 2:
                    return [], []
                headers   = [str(c).strip() if c is not None else '' for c in rows[0]]
                data_rows = rows[1:]
        except openpyxl.utils.exceptions.InvalidFileException:
            raise UserError(_(
                'The selected file is not a valid spreadsheet.\n'
                'Please upload a file in .xlsx or .csv format.'
            ))
        except Exception as exc:
            _logger.warning('Error reading file in survey import wizard: %s', exc)
            raise UserError(_(
                'Could not read the file. Make sure it is a valid .xlsx or .csv file.\n'
            ) % str(exc))

        return data_rows, headers

    def _parse_rows(self, headers, rows):
        """
        Parses rows using the column mapping configured in the survey.
        Merges duplicate records that share organization + registration_number + any email.
        """
        # Build mapping dict from survey configuration
        survey_mapping = {
            line.field_name: line.column_name
            for line in self.survey_id.column_mapping_ids
        }

        if not survey_mapping:
            raise UserError(_(
                'This survey has no column mapping configured.\n'
                'Please configure the file column mapping in the survey settings '
                'before importing.'
            ))

        # Validate that contact_email is mapped
        if 'contact_email' not in survey_mapping:
            raise UserError(_(
                'The "Contact Email" field is not mapped in this survey.\n'
                'Please configure the column mapping in the survey settings.'
            ))
        
        # Reverse: { column_name_in_file: field_name }
        col_name_to_field = {v: k for k, v in survey_mapping.items()}
        
        # Build index: { field_name: column_index_in_file }
        col_index = {h.lower().strip(): i for i, h in enumerate(headers)}
        field_to_idx = {}
        for field, col_name in survey_mapping.items():
            normalized = col_name.lower().strip()
            if normalized in col_index:
                field_to_idx[field] = col_index[normalized]

        def get(field, default=''):
            idx = field_to_idx.get(field)
            if idx is None:
                return default
            val = row[idx]
            return str(val).strip() if val is not None else default

        result = []
        for row in rows:
            if not any(row):
                continue

            emails_raw = get('contact_email')
            emails = [e.strip() for e in emails_raw.split(';') if e.strip()]
            if not emails:
                continue

            names_raw = get('contact_name')
            names = [n.strip() for n in names_raw.split(';') if n.strip()]

            date_idx = field_to_idx.get('certified_date')
            cert_date = _parse_date(
                row[date_idx] if date_idx is not None and date_idx < len(row) else None
            )

            result.append({
                'registration_number': get('registration_number'),
                'organization_name':   get('organization_name'),
                'app_id':              get('app_id'),
                'audit_id':            get('audit_id'),
                'certified_date':      cert_date,
                'coordinator_name':    get('coordinator_name'),
                'auditor_name':        get('auditor_name'),
                'audit_state':         get('audit_state'),
                'audit_country':       get('audit_country'),
                'contact_name':        names_raw,
                'contact_email':       emails_raw,
                'emails':              emails,
                'names':               names,
                'primary_email':       '; '.join(emails),
                'primary_name':        names[0] if names else emails[0],
            })

        # Deduplicate: merge records that share organization + registration_number + any email
        merged = []
        seen = []  # list of (organization_name, registration_number, emails_set)

        for record in result:
            record_emails = set(record['emails'])
            record_names  = record['names']
            match_idx = None

            for idx, (org, reg, emails_set) in enumerate(seen):
                if (
                    org == record['organization_name']
                    and reg == record['registration_number']
                    and record_emails & emails_set  # any email in common
                ):
                    match_idx = idx
                    break

            if match_idx is None:
                # No duplicate found, add as new record
                merged.append(record)
                seen.append((
                    record['organization_name'],
                    record['registration_number'],
                    record_emails,
                ))
            else:
                # Duplicate found: merge emails and names into existing record
                existing = merged[match_idx]
                existing_emails = existing['emails']
                existing_names  = existing['names']

                # Add only new emails and their corresponding names
                for i, email in enumerate(record['emails']):
                    if email not in existing_emails:
                        existing_emails.append(email)
                        name = record_names[i] if i < len(record_names) else email
                        existing_names.append(name)

                # Update all email/name related fields
                existing['emails']        = existing_emails
                existing['names']         = existing_names
                existing['contact_email'] = '; '.join(existing_emails)
                existing['contact_name']  = '; '.join(existing_names)
                existing['primary_email'] = '; '.join(existing_emails)
                existing['primary_name']  = existing_names[0] if existing_names else existing_emails[0]

                # Update the emails_set in seen
                seen[match_idx] = (
                    seen[match_idx][0],
                    seen[match_idx][1],
                    seen[match_idx][2] | record_emails,
                )

        return merged
    
    # def _parse_rows(self, headers, rows):
    #     """
    #     Parsea las filas del xlsx y devuelve una lista de dicts listos para crear
    #     user_input. Cada dict incluye la lista de emails separados.
    #     """
    #     col = {h: i for i, h in enumerate(headers)}
    #     result = []

    #     for row in rows:
    #         if not any(row):
    #             continue

    #         def get(col_name, default=''):
    #             idx = col.get(col_name)
    #             if idx is None:
    #                 return default
    #             val = row[idx]
    #             return str(val).strip() if val is not None else default

    #         emails_raw = get('Contact Email')
    #         emails = [e.strip() for e in emails_raw.split(';') if e.strip()]
    #         if not emails:
    #             continue  # Registros sin correo se omiten

    #         names_raw = get('Contact Name')
    #         names = [n.strip() for n in names_raw.split(';') if n.strip()]

    #         result.append({
    #             'registration_number': get('PGFSNumber'),
    #             'organization_name':   get('Organization Name'),
    #             'app_id':              get('App ID'),
    #             'audit_id':            get('Audit ID'),
    #             'certified_date':      _parse_date(
    #                 row[col['Certification Date']] if 'Certification Date' in col else None
    #             ),
    #             'coordinator_name':    get('Coordinator'),
    #             'auditor_name':        get('Auditor'),
    #             'audit_state':         get('Operation State'),
    #             'audit_country':       get('Operation Country'),
    #             'contact_name':        names_raw,
    #             'contact_email':       emails_raw,
    #             'emails':              emails,
    #             'names':               names,
    #             'primary_email':       '; '.join(emails),
    #             'primary_name':        names[0] if names else emails[0],
    #         })

    #     return result

    def _create_user_input(self, survey, record):
        """
        Crea un único survey.user_input por organización.
        El token generado por Odoo será el mismo para todos los contactos
        de ese registro, garantizando una sola respuesta a nivel organización.
        """
        vals = {
            'survey_id':           survey.id,
            'partner_id':          False,
            'email':               record['primary_email'],
            # 'partner_name':        record['primary_name'],
            'nickname':            record['primary_name'],
            'imported_from_file':  True,
            # Campos de auditoría
            'registration_number': record['registration_number'],
            'organization_name':   record['organization_name'],
            'app_id':              record['app_id'],
            'audit_id':            record['audit_id'],
            'certified_date':      record['certified_date'],
            'coordinator_name':    record['coordinator_name'],
            'auditor_name':        record['auditor_name'],
            'audit_state':         record['audit_state'],
            'audit_country':       record['audit_country'],
            'contact_name':        record['contact_name'],
            'contact_email':       record['contact_email'],
        }
        return self.env['survey.user_input'].create(vals)

    def _send_emails(self, survey, user_input, record):
        """
        Envía el mismo link de encuesta a todos los contactos del registro.
        Un token único → misma URL → una sola respuesta posible por organización.
        """
        survey_url = user_input.get_start_url()
        emails = record['emails']
        names = record['names']
        
        # emails = [e.strip() for e in email.split(',') if e.strip()]

        for idx, email in enumerate(emails):
            _logger.warning('Sending to email: %s', email)
            partner_name = names[idx] if idx < len(names) else email
            _logger.warning('Sending to partner_name: %s', partner_name)
            try:
                survey._send_survey_mail_to_contact(email, partner_name, user_input)
            except Exception as exc:
                _logger.warning(
                    'Failed to send survey to a %s (input %s): %s',
                    email, user_input.id, exc
                )

    def _build_preview_html(self, rows, total_records, total_emails):
        """Genera una tabla HTML de previsualización de los primeros registros."""

        records_found_label = _('Records found:')
        emails_to_send_label = _('Emails to send:')
        organization_label = _('Organization')
        auditor_label = _('Auditor')
        coordinator_label = _('Coordinator')
        contacts_label = _('Contacts')
        emails_label = _('Emails')
        more_records_label = _('... and %s more records')

        html = f"""
        <div style="font-family: sans-serif; font-size: 13px;">
            <p><strong>{records_found_label}</strong> {total_records} &nbsp; - &nbsp;
            <strong>{emails_to_send_label}</strong> {total_emails}</p>

            <table style="width:100%; border-collapse:collapse; margin-top:8px;">
                <thead>
                    <tr style="background:#f0f0f0;">
                        <th style="padding:6px; border:1px solid #ddd; text-align:left;">{organization_label}</th>
                        <th style="padding:6px; border:1px solid #ddd; text-align:left;">{auditor_label}</th>
                        <th style="padding:6px; border:1px solid #ddd; text-align:left;">{coordinator_label}</th>
                        <th style="padding:6px; border:1px solid #ddd; text-align:left;">{contacts_label}</th>
                        <th style="padding:6px; border:1px solid #ddd; text-align:left;">{emails_label}</th>
                    </tr>
                </thead>
                <tbody>
        """

        for r in rows:
            html += f"""
                    <tr>
                        <td style="padding:5px; border:1px solid #ddd;">{r['organization_name']}</td>
                        <td style="padding:5px; border:1px solid #ddd;">{r['auditor_name']}</td>
                        <td style="padding:5px; border:1px solid #ddd;">{r['coordinator_name']}</td>
                        <td style="padding:5px; border:1px solid #ddd;">{len(r['names'])}</td>
                        <td style="padding:5px; border:1px solid #ddd;">{r['contact_email']}</td>
                    </tr>
            """

        if total_records > 10:
            html += f"""
                    <tr>
                        <td colspan="5" style="padding:5px; text-align:center; color:#888; border:1px solid #ddd;">
                            {more_records_label % (total_records - 10)}
                        </td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """

        return html

import io
import re

import markupsafe

from odoo import fields, models
from odoo.tools.pdf import PdfFileReader

FOLIO_OPTION = 'pao_folio'


def advance_folio(folio, pages):
    """ Folio `pages` pages later, counted the same way as the page header:
    '123' + 2 -> '125', 'A-0099' + 1 -> 'A-0100'. A folio that does not end in
    digits never changes.
    """
    match = re.match(r'^(.*?)(\d+)$', folio)
    if not match:
        return folio
    prefix, digits = match.groups()
    return prefix + str(int(digits) + pages).zfill(len(digits))


class AccountReport(models.Model):
    _inherit = 'account.report'

    pao_ask_folio = fields.Boolean(
        string='Pedir folio al imprimir PDF',
        help="Al presionar PDF se pide un folio opcional. Si se captura, cada hoja "
             "lo muestra arriba a la derecha y va aumentando por hoja (123, 124...).",
    )

    def _init_options_buttons(self, options, previous_options=None):
        super()._init_options_buttons(options, previous_options=previous_options)
        if not self.pao_ask_folio:
            return
        # The PDF button opens the folio dialog instead of downloading directly.
        for button in options['buttons']:
            if button.get('action') == 'export_file' and button.get('action_param') == 'export_to_pdf':
                button['action'] = 'action_open_pao_folio_wizard'
                button.pop('action_param', None)

    def _init_options_pao_folio(self, options, previous_options=None):
        # Odoo rebuilds the options while printing: keep the folio typed in the dialog.
        folio = (previous_options or {}).get(FOLIO_OPTION)
        if folio and self.pao_ask_folio:
            options[FOLIO_OPTION] = folio

    def action_open_pao_folio_wizard(self, options):
        wizard = self.env['pao.cl.account.report.folio.wizard'].create({
            'report_id': options['report_id'],
            'options_data': options,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Imprimir PDF',
            'res_model': wizard._name,
            'res_id': wizard.id,
            'views': [[False, 'form']],
            'target': 'new',
        }

    def export_to_pdf(self, options):
        """ Same as Odoo's, plus a page header with the folio, which goes up by one per page. """
        folio = options.get(FOLIO_OPTION)
        if not folio:
            return super().export_to_pdf(options)
        self.ensure_one()

        action_report = self.env['ir.actions.report']
        files_stream = []
        for (bodies, footer, is_landscape) in self._get_html_data_for_pdf_export(options):
            stream = io.BytesIO(action_report._run_wkhtmltopdf(
                bodies,
                header=self._pao_folio_header_html(folio),
                footer=footer.decode(),
                landscape=is_landscape or self._context.get('force_landscape_printing'),
                specific_paperformat_args={
                    # Odoo uses 10 / 10 / 15; a bit more on top to fit the folio line.
                    'data-report-margin-top': 16,
                    'data-report-header-spacing': 6,
                    'data-report-margin-bottom': 15,
                },
            ))
            files_stream.append(stream)
            # Wide and narrow sections are printed apart and then merged:
            # the next part starts its folio where this one ended.
            folio = advance_folio(folio, PdfFileReader(stream).getNumPages())
            stream.seek(0)

        if len(files_stream) > 1:
            result_stream = action_report._merge_pdfs(files_stream)
            result = result_stream.getvalue()
            result_stream.close()
            for file_stream in files_stream:
                file_stream.close()
        else:
            result = files_stream[0].read()

        return {
            'file_name': self.get_default_report_filename(options, 'pdf'),
            'file_content': result,
            'file_type': 'pdf',
        }

    def _pao_folio_header_html(self, folio):
        action_report = self.env['ir.actions.report']
        config = self.env['ir.config_parameter'].sudo()
        header = action_report._render_template(
            'pao_cl_report_folio.account_report_folio_header', values={'folio': folio})
        header = action_report._render_template('web.minimal_layout', values={
            'base_url': config.get_param('report.url') or config.get_param('web.base.url'),
            'subst': True,
            'body': markupsafe.Markup(header.decode()),
        })
        return header.decode()

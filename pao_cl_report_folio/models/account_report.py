import io
import re

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from odoo import fields, models
from odoo.tools.pdf import PdfFileReader, PdfFileWriter

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
        if not self._pao_asks_folio():
            return
        # The PDF button opens the folio dialog instead of downloading directly.
        for button in options['buttons']:
            if button.get('action') == 'export_file' and button.get('action_param') == 'export_to_pdf':
                button['action'] = 'action_open_pao_folio_wizard'
                button.pop('action_param', None)

    def _init_options_pao_folio(self, options, previous_options=None):
        # Odoo rebuilds the options while printing: keep the folio typed in the dialog.
        folio = (previous_options or {}).get(FOLIO_OPTION)
        if folio and self._pao_asks_folio():
            options[FOLIO_OPTION] = folio

    def _pao_asks_folio(self):
        # A variant (e.g. a copy of the Libro mayor) follows its root report's checkbox too.
        return self.pao_ask_folio or self.root_report_id.pao_ask_folio

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
        """ Same PDF as Odoo's; when a folio was typed, each page gets "FOLIO: n" at the
        top right, going up by one per page (123, 124...). """
        result = super().export_to_pdf(options)
        folio = options.get(FOLIO_OPTION)
        if folio and result.get('file_type') == 'pdf':
            result['file_content'] = self._pao_stamp_folio(result['file_content'], folio)
        return result

    def _pao_stamp_folio(self, pdf_content, folio):
        reader = PdfFileReader(io.BytesIO(pdf_content), strict=False)
        paperformat = self.env.company.paperformat_id
        margin_right = (paperformat.margin_right or 7) * mm

        # One overlay page per PDF page with only the folio text.
        overlay_stream = io.BytesIO()
        overlay = canvas.Canvas(overlay_stream)
        for index in range(reader.getNumPages()):
            box = reader.getPage(index).mediaBox
            width, height = float(abs(box.getWidth())), float(abs(box.getHeight()))
            overlay.setPageSize((width, height))
            overlay.setFont('Helvetica-Bold', 9)
            # Inside the top margin (10 mm in Odoo's accounting reports), above the grey block.
            overlay.drawRightString(width - margin_right, height - 7 * mm, f"FOLIO: {advance_folio(folio, index)}")
            overlay.showPage()
        overlay.save()

        overlay_reader = PdfFileReader(overlay_stream, strict=False)
        writer = PdfFileWriter()
        for index in range(reader.getNumPages()):
            page = reader.getPage(index)
            page.mergePage(overlay_reader.getPage(index))
            writer.addPage(page)
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()

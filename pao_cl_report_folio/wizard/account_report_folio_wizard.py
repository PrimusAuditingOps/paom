from odoo import fields, models

from ..models.account_report import FOLIO_OPTION


class AccountReportFolioWizard(models.TransientModel):
    """ Optional folio asked before printing the PDF of an accounting report
    (Balance General, Libro mayor...). Only used for that print; nothing is kept.
    """
    _name = 'pao.cl.account.report.folio.wizard'
    _description = 'Folio para PDF de reportes contables (Chile)'

    report_id = fields.Many2one('account.report', required=True, ondelete='cascade')
    options_data = fields.Json()
    folio = fields.Char(string='Folio')

    def action_print_pdf(self):
        self.ensure_one()
        options = dict(self.options_data or {})
        folio = (self.folio or '').strip()
        if folio:
            options[FOLIO_OPTION] = folio
        else:
            options.pop(FOLIO_OPTION, None)
        return self.report_id.export_file(options, 'export_to_pdf')

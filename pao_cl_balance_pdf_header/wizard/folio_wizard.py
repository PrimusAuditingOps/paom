from odoo import fields, models

from ..models.l10n_cl_report_handler import FOLIO_OPTION


class ChileanBalanceFolioWizard(models.TransientModel):
    """ Asks for an optional folio before printing the PDF. The folio is only
    used for that print; it is not kept anywhere (transient record, cleaned up
    automatically by Odoo).
    """
    _name = 'pao.cl.balance.folio.wizard'
    _description = 'Folio para PDF del Balance General (Chile)'

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

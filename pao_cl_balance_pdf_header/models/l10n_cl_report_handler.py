from odoo import models

FOLIO_OPTION = 'pao_folio'


class ChileanReportCustomHandler(models.AbstractModel):
    _inherit = 'l10n_cl.report.handler'

    def _get_custom_display_config(self):
        """ Use our own PDF title and company header for the Chilean
        8-column balance report only; every other report keeps Odoo's default.
        """
        config = super()._get_custom_display_config()
        pdf_export = config.setdefault('pdf_export', {})
        pdf_export['pdf_export_main'] = 'pao_cl_balance_pdf_header.pdf_export_main'
        pdf_export['company_information'] = 'pao_cl_balance_pdf_header.company_information'
        pdf_export['pdf_export_filters'] = 'pao_cl_balance_pdf_header.pdf_export_filters'
        return config

    def _custom_options_initializer(self, report, options, previous_options=None):
        super()._custom_options_initializer(report, options, previous_options=previous_options)

        # The PDF button opens the folio dialog instead of downloading directly.
        for button in options.get('buttons', []):
            if button.get('action') == 'export_file' and button.get('action_param') == 'export_to_pdf':
                button['action'] = 'action_open_folio_wizard'
                button.pop('action_param', None)

        # Odoo rebuilds the options while printing: keep the folio typed in the dialog.
        folio = (previous_options or {}).get(FOLIO_OPTION)
        if folio:
            options[FOLIO_OPTION] = folio

    def action_open_folio_wizard(self, options):
        wizard = self.env['pao.cl.balance.folio.wizard'].create({
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

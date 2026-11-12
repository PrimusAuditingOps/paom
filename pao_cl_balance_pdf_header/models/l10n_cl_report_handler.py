from odoo import models


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
        return config

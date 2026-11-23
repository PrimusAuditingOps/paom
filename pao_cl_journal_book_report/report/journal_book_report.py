from odoo import api, models
from odoo.exceptions import UserError

MONTHS = [
    'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO',
    'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE',
]


class JournalBookReport(models.AbstractModel):
    _name = 'report.pao_cl_journal_book_report.report_journal_book'
    _description = 'Reporte: Libro diario (Chile)'

    @api.model
    def _get_report_values(self, docids, data=None):
        lines = self.env['account.move.line'].browse(docids).exists()
        if not lines:
            raise UserError("Selecciona al menos un apunte contable.")

        company = lines.company_id
        if len(company) != 1:
            raise UserError("Todos los apuntes seleccionados deben ser de la misma compañía.")
        if company.account_fiscal_country_id.code != 'CL':
            raise UserError("El Reporte: Libro diario solo está disponible para la compañía de Chile.")

        months = {(line.date.year, line.date.month) for line in lines}
        if len(months) != 1:
            raise UserError("Selecciona apuntes de un solo mes para imprimir el Reporte: Libro diario.")
        year, month = months.pop()

        lines = lines.sorted(lambda l: (l.date, l.move_id.name or '', l.move_id.id, l.id))

        month_debit = sum(lines.mapped('debit'))
        month_credit = sum(lines.mapped('credit'))

        return {
            'doc_ids': lines.ids,
            'doc_model': 'account.move.line',
            'docs': lines,
            'company': company,
            'title': f"DIARIO GENERAL {MONTHS[month - 1]} DE {year}",
            'month_debit': month_debit,
            'month_credit': month_credit,
            'fmt_amount': self._format_amount,
            'fmt_date': lambda d: f"{d.day}/{d.month}/{d.year}",
            'cost_center': self._cost_center,
        }

    @api.model
    def _format_amount(self, value):
        """ Chilean style, no decimals: 35213990059 -> 35.213.990.059 """
        return f"{round(value or 0.0):,}".replace(',', '.')

    @api.model
    def _cost_center(self, line):
        """ Analytic accounts of the line (code if it has one, otherwise name). """
        if not line.analytic_distribution:
            return ''
        analytic_ids = {
            int(analytic_id)
            for key in line.analytic_distribution
            for analytic_id in str(key).split(',')
            if analytic_id.isdigit()
        }
        accounts = self.env['account.analytic.account'].browse(sorted(analytic_ids)).exists()
        return ', '.join(account.code or account.name for account in accounts)

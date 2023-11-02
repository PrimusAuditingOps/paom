from odoo import models, fields, api

class SaleReport(models.Model):
    _inherit="sale.report"

    pao_invoice_date = fields.Date(string="Invoice Date")
            
    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['pao_invoice_date'] = ", s.pao_invoice_date as pao_invoice_date"
        groupby += ', s.pao_invoice_date'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)

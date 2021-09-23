from odoo import fields, models
from logging import getLogger

_logger = getLogger(__name__)
class AccountMoveInh(models.Model):
    
    _inherit = 'account.move'


    ad_usd_neto = fields.Monetary(
        compute='_get_usd_neto', 
        string='Neto USD',
        readonly=True,
    )
    ad_usd_iva = fields.Monetary(
        compute='_get_usd_iva', 
        string='IVA USD',
        readonly=True,
    )
    ad_usd_total = fields.Monetary(
        compute='_get_usd_total', 
        string='Total USD',
        readonly=True,
    )
    ad_mxn_neto = fields.Monetary(
        compute='_get_mxn_neto', 
        string='Neto MXN',
        readonly=True,
    )
    ad_mxn_iva = fields.Monetary(
        compute='_get_mxn_iva', 
        string='IVA MXN',
        readonly=True,
    )
    ad_mxn_total = fields.Monetary(
        compute='_get_mxn_total', 
        string='Total MXN',
        readonly=True,
    )
    def _get_usd_neto(self):
        for rec in self:
            rec.ad_usd_neto = 0.00
            dateinvoice = rec.date
            if rec.invoice_date:
                dateinvoice = rec.invoice_date

            if rec.currency_id.name == 'MXN':
                currencyrate = self._get_rates_currency(dateinvoice)
                if currencyrate:
                    rec.ad_usd_neto = round((rec.amount_untaxed * currencyrate.get('USD')),2)
            elif rec.currency_id.name == "USD":
                rec.ad_usd_neto = rec.amount_untaxed
    def _get_usd_iva(self):
        for rec in self:
            rec.ad_usd_iva = 0.00
            dateinvoice = rec.date
            if rec.invoice_date:
                dateinvoice = rec.invoice_date
            if rec.currency_id.name == 'MXN':
                currencyrate = self._get_rates_currency(dateinvoice)
                if currencyrate:
                    rec.ad_usd_iva = round((rec.amount_tax * currencyrate.get('USD')),2)
            elif rec.currency_id.name == "USD":
                rec.ad_usd_iva = rec.amount_tax
            
    def _get_usd_total(self):
        for rec in self:
            rec.ad_usd_total = 0.00
            dateinvoice = rec.date
            if rec.invoice_date:
                dateinvoice = rec.invoice_date
            if rec.currency_id.name == 'MXN':
                currencyrate = self._get_rates_currency(dateinvoice)
                if currencyrate:
                    rec.ad_usd_total = round((rec.amount_total * currencyrate.get('USD')),2)
            elif rec.currency_id.name == "USD":
                rec.ad_usd_total = rec.amount_total
    def _get_mxn_neto(self):
        for rec in self:
            rec.ad_mxn_neto = 0.00
            dateinvoice = rec.date
            if rec.invoice_date:
                dateinvoice = rec.invoice_date
            if rec.currency_id.name == 'USD':
                currencyrate = self._get_rates_currency(dateinvoice)
                if currencyrate:
                    rec.ad_mxn_neto = round((rec.amount_untaxed / currencyrate.get('USD')),2)
            elif rec.currency_id.name == 'MXN':
                rec.ad_mxn_neto = rec.amount_untaxed

    def _get_mxn_iva(self):
        for rec in self:
            rec.ad_mxn_iva = 0.00
            dateinvoice = rec.date
            if rec.invoice_date:
                dateinvoice = rec.invoice_date
            if rec.currency_id.name == 'USD':
                currencyrate = self._get_rates_currency(dateinvoice)
                if currencyrate:
                    rec.ad_mxn_iva = round((rec.amount_tax / currencyrate.get('USD')),2)
            elif rec.currency_id.name == 'MXN':
                rec.ad_mxn_iva = rec.amount_tax

    def _get_mxn_total(self):
        for rec in self:
            rec.ad_mxn_total = 0.00
            dateinvoice = rec.date
            if rec.invoice_date:
                dateinvoice = rec.invoice_date
            if rec.currency_id.name == 'USD':
                currencyrate = self._get_rates_currency(dateinvoice)
                if currencyrate:
                    rec.ad_mxn_total = round((rec.amount_total / currencyrate.get('USD')),2)
            elif rec.currency_id.name == 'MXN':
                rec.ad_mxn_total = rec.amount_total
    
    def _get_rates_currency(self, date):
        currencyname = 'USD'
        self.env['res.currency.rate'].flush(['rate', 'currency_id', 'company_id', 'name'])
        query = """SELECT c.name,
                          COALESCE((SELECT r.rate FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name <= %s
                               ORDER BY r.name DESC
                                  LIMIT 1), 1.0) AS rate
                   FROM res_currency c
                   WHERE c.name = %s"""
        self._cr.execute(query, (date, currencyname))
        currency_rates = dict(self._cr.fetchall())
        return currency_rates
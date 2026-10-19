# -*- coding: utf-8 -*-
from odoo import Command, api, fields, models
from odoo.tools.misc import formatLang

CERT008_SCHEME = 'GLOBALG.A.P.'
CERT008_COUNTRY = 'CL'


class RegistrationNumberToSign(models.Model):
    _inherit = 'pao.registration.number.to.sign'

    pao_cert008_line_ids = fields.One2many(
        comodel_name='pao.sa.cert008.line',
        inverse_name='registration_number_to_sign_id',
        string='CERT-008 Lines',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered(lambda r: r._pao_is_cert008()):
            record.pao_cert008_line_ids = [Command.create(vals) for vals in record._pao_cert008_lines_from_order()]
        return records

    def _pao_is_cert008(self):
        self.ensure_one()
        return self.scheme == CERT008_SCHEME and self.sign_sa_agreements_id.country_format == CERT008_COUNTRY

    def _pao_cert008_order_lines(self):
        """Quotation lines of this organization / registration number."""
        self.ensure_one()
        order = self.sign_sa_agreements_id.sale_order_id
        return order.order_line.filtered(
            lambda line: line.product_id
            and not line.display_type
            and line.registrynumber_id.name == self.name
            and (line.organization_id.name or '') == (self.organization_name or '')
        )

    def _pao_cert008_lines_from_order(self):
        """Classify the quotation lines by the product catalog flags. A product is only one of: travel expense,
        fee, add-on; anything else is the audit service. Amount = line subtotal, currency = product base
        currency (pao_chile_invoices), without conversion."""
        self.ensure_one()
        values = []
        for line in self._pao_cert008_order_lines():
            template = line.product_id.product_tmpl_id
            if template.is_travel_expenses:
                line_type = 'travel'
            elif template.pao_sa_is_fee:
                line_type = 'fee'
            elif template.pao_sa_addon_id:
                line_type = 'addon'
            else:
                line_type = 'audit'
            values.append({
                'sequence': line.sequence,
                'name': line.name,
                'line_type': line_type,
                'addon_id': template.pao_sa_addon_id.id,
                'currency_id': (line.product_id.base_currency_id or line.order_id.currency_id).id,
                'amount': line.price_subtotal,
            })
        return values

    def _pao_cert008_data(self):
        """Values printed in the CERT-008 form. Uses the lines saved when the SA was sent, or the current
        quotation lines for the preview."""
        self.ensure_one()
        if self.pao_cert008_line_ids:
            lines = [{
                'name': line.name,
                'line_type': line.line_type,
                'addon': line.addon_id,
                'currency': line.currency_id,
                'amount': line.amount,
            } for line in self.pao_cert008_line_ids]
        else:
            Addon = self.env['pao.sa.addon']
            Currency = self.env['res.currency']
            lines = [{
                'name': vals['name'],
                'line_type': vals['line_type'],
                'addon': Addon.browse(vals['addon_id']),
                'currency': Currency.browse(vals['currency_id']),
                'amount': vals['amount'],
            } for vals in self._pao_cert008_lines_from_order()]

        def totals(line_types):
            result = {}
            for line in lines:
                if line['line_type'] in line_types:
                    result[line['currency']] = result.get(line['currency'], 0.0) + line['amount']
            return [(currency, amount) for currency, amount in result.items()]

        used_addons = self.env['pao.sa.addon']
        for line in lines:
            used_addons |= line['addon']
        company = self.sign_sa_agreements_id.sale_order_id.company_id
        addons = self.env['pao.sa.addon'].sudo().search([('company_id', '=', company.id)]) | used_addons

        return {
            'audit_services': [(line['name'] or '').split('\n')[0] for line in lines if line['line_type'] == 'audit'],
            'addons': [(addon.name, addon in used_addons) for addon in addons.sorted(lambda a: (a.sequence, a.name))],
            'fees': [line for line in lines if line['line_type'] == 'fee'],
            'audit_totals': totals(('audit', 'addon')),
            'fee_totals': totals(('fee',)),
            'travel_totals': totals(('travel',)),
        }

    def _pao_cert008_amount(self, amount, currency):
        """'€ 23,00' for euros, '940,00 USD' for the other currencies (avoids the ambiguous '$')."""
        formatted = formatLang(self.env, amount, digits=currency.decimal_places)
        return f'€ {formatted}' if currency.name == 'EUR' else f'{formatted} {currency.name}'

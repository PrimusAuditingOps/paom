# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import _, fields, models
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def xml2record(self):
        """Use the last attachment in the payment (xml) and fill the payment
        data"""
        atts = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
        ])
        prod_supplier = self.env['product.supplierinfo']
        prod = self.env['product.product']
        sat_code = self.env['product.unspsc.code']
        uom_obj = self.env['uom.uom']
        default_account = self.journal_id.default_account_id.id
        invoice = self
        for attachment in atts:
            cfdi = attachment.l10n_mx_edi_is_cfdi33()
            if cfdi is False:
                continue
            amount = 0
            currency = self.env['res.currency'].search([
                ('name', '=', cfdi.get('Moneda'))], limit=1)
            self.l10n_mx_edi_set_cfdi_partner(cfdi, currency)
            invoice = self._search_invoice(cfdi) or invoice
            if invoice != self:
                attachment.write({'res_id': False, 'res_model': False})
                self.unlink()
                invoice._l10n_mx_edi_update_data(attachment)
                continue
            fiscal_position = self.fiscal_position_id
            for rec in cfdi.Conceptos.Concepto:
                name = rec.get('Descripcion', '')
                no_id = rec.get('NoIdentificacion', name)
                uom = rec.get('Unidad', '')
                uom_code = rec.get('ClaveUnidad', '')
                qty = rec.get('Cantidad', '')
                price = rec.get('ValorUnitario', '')
                amount = float(rec.get('Importe', '0.0'))
                supplierinfo = prod_supplier.search([
                    ('name', '=', self.partner_id.id),
                    '|', ('product_name', '=ilike', name),
                    ('product_code', '=ilike', no_id)], limit=1)
                product = supplierinfo.product_tmpl_id.product_variant_id
                product = product or prod.search([
                    '|', ('default_code', '=ilike', no_id),
                    ('name', '=ilike', name)], limit=1)
                accounts = product.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
                if self.is_sale_document(include_receipts=True):
                    # Out invoice.
                    account_id = accounts['income'] or default_account
                elif self.is_purchase_document(include_receipts=True):
                    # In invoice.
                    account_id = accounts['expense'] or default_account

                discount = 0.0
                if rec.get('Descuento') and amount:
                    discount = (float(rec.get('Descuento', '0.0')) / amount) * 100  # noqa

                domain_uom = [('name', '=ilike', uom)]
                code_sat = sat_code.search([('code', '=', uom_code)], limit=1)
                domain_uom = [('unspsc_code_id', '=', code_sat.id)]
                uom_id = uom_obj.with_context(
                    lang='es_MX').search(domain_uom, limit=1)
                # if product_code in self._get_fuel_codes() or \
                #         restaurant_category_id in supplier.category_id:
                #     tax = taxes.get(index)[0] if taxes.get(index, []) else {}
                #     qty = 1.0
                #     price = tax.get('amount') / (tax.get('rate') / 100)
                #     invoice_line_ids.append((0, 0, {
                #         'account_id': account_id,
                #         'name':  _('Non Deductible') if
                #         restaurant_category_id in supplier.category_id else
                #         _('FUEL - IEPS'),
                #         'quantity': qty,
                #         'uom_id': uom_id.id,
                #         'price_unit': float(rec.get('Importe', 0)) - price,
                #     }))
                self.write({'invoice_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'account_id': account_id,
                    'name': name,
                    'quantity': float(qty),
                    'product_uom_id': uom_id.id,
                    'tax_ids': self.get_line_taxes(rec),
                    'price_unit': float(price),
                    'discount': discount,
                })]})

            cfdi_related = ''
            if hasattr(cfdi, 'CfdiRelacionados'):
                cfdi_related = '%s|%s' % (
                    cfdi.CfdiRelacionados.get('TipoRelacion'),
                    ','.join([rel.get('UUID') for
                              rel in cfdi.CfdiRelacionados.CfdiRelacionado]))
            invoice_data = {
                'ref': '%s%s' % (cfdi.get('Serie'), cfdi.get('Folio')),
                'invoice_date': cfdi.get('Fecha').split('T')[0],
                'date': cfdi.get('Fecha').split('T')[0],
                'currency_id': currency.id,
                'l10n_mx_edi_post_time': cfdi.get('Fecha').replace('T', ' '),
                'l10n_mx_edi_origin': cfdi_related,
            }
            self.write(invoice_data)
            self._recompute_tax_lines()
            self._l10n_mx_edi_update_data(attachment)
            if cfdi_related.split('|')[0] in ('01', '02', '03'):
                move = self.line_ids.filtered(
                    lambda line: line.account_id.internal_type in (
                        'payable', 'receivable'))
                for uuid in self.l10n_mx_edi_origin.split('|')[1].split(','):
                    inv = self.search([('l10n_mx_edi_cfdi_uuid', '=', uuid.upper().strip())])
                    if not inv:
                        continue
                    inv.js_assign_outstanding_line(move.ids)
        return invoice

    def _l10n_mx_edi_update_data(self, attachment):
        if self.edi_state != 'sent':
            self.edi_state = 'sent'
            self.env['account.edi.document'].create({
                'edi_format_id': self.env.ref('l10n_mx_edi.edi_cfdi_3_3').id,
                'move_id': self.id,
                'state': 'sent',
                'attachment_id': attachment.id,
            })
            try:
                self.action_post()
            except (UserError, ValidationError) as exe:
                self.message_post(body=_(
                    '<b>Error on invoice validation </b><br/>%s') % exe.name)

    def l10n_mx_edi_set_cfdi_partner(self, cfdi, currency):
        self.ensure_one()
        partner = self.env['res.partner']
        domain = []
        partner_cfdi = {}
        if self.move_type in ('out_invoice', 'out_refund'):
            partner_cfdi = cfdi.Receptor
            domain.append(('vat', '=', partner_cfdi.get('Rfc')))
        elif self.move_type in ('in_invoice', 'in_refund'):
            partner_cfdi = cfdi.Emisor
            domain.append(('vat', '=', partner_cfdi.get('Rfc')))
        domain.append(('is_company', '=', True))
        cfdi_partner = partner.search(domain, limit=1)
        currency_field = 'property_purchase_currency_id' in partner._fields
        if currency_field:
            domain.append(('property_purchase_currency_id', '=', currency.id))
        if currency_field and not cfdi_partner:
            domain.pop()
            cfdi_partner = partner.search(domain, limit=1)
        if not cfdi_partner:
            domain.pop()
            cfdi_partner = partner.search(domain, limit=1)
        if not cfdi_partner:
            cfdi_partner = partner.create({
                'name': partner_cfdi.get('Nombre'),
                'vat': partner_cfdi.get('Rfc'),
                'country_id': False,  # TODO
            })
            cfdi_partner.message_post(body=_(
                'This record was generated from DMS'))
        self.partner_id = cfdi_partner
        self._onchange_partner_id()

    def get_line_taxes(self, line):
        taxes_list = []
        if not hasattr(line, 'Impuestos'):
            return taxes_list
        taxes_xml = line.Impuestos
        if hasattr(taxes_xml, 'Traslados'):
            taxes = self.collect_taxes(taxes_xml.Traslados.Traslado)
        if hasattr(taxes_xml, 'Retenciones'):
            taxes += self.collect_taxes(taxes_xml.Retenciones.Retencion)
        for tax in taxes:
            tax_group_id = self.env['account.tax.group'].search(
                [('name', 'ilike', tax['tax'])])
            domain = [
                ('tax_group_id', 'in', tax_group_id.ids),
                ('type_tax_use', '=', 'purchase' if 'in_' in self.move_type else 'sale')]  # noqa
            if -10.67 <= tax['rate'] <= -10.66:
                domain.append(('amount', '<=', -10.66))
                domain.append(('amount', '>=', -10.67))
            else:
                domain.append(('amount', '=', tax['rate']))
            name = '%s(%s%%)' % (tax['tax'], tax['rate'])

            tax_get = self.env['account.tax'].search(domain, limit=1)
            if not tax_get:
                self.message_post(body=_('The tax %s cannot be found') % name)
                continue
            tax_account = tax_get.invoice_repartition_line_ids.filtered(
                lambda rec: rec.repartition_type == 'tax')
            if not tax_account:
                self.message_post(body=_(
                    'Please configure the tax account in the tax %s') % name)
                continue
            taxes_list.append((4, tax_get.id))
        return taxes_list

    @staticmethod
    def collect_taxes(taxes_xml):
        """ Get tax data of the Impuesto node of the xml and return
        dictionary with taxes datas
        :param taxes_xml: Impuesto node of xml
        :type taxes_xml: etree
        :return: A list with the taxes data
        :rtype: list
        """
        taxes = []
        tax_codes = {'001': 'ISR', '002': 'IVA', '003': 'IEPS'}
        for rec in taxes_xml:
            tax_xml = rec.get('Impuesto', '')
            tax_xml = tax_codes.get(tax_xml, tax_xml)
            amount_xml = float(rec.get('Importe', '0.0'))
            rate_xml = float_round(
                float(rec.get('TasaOCuota', '0.0')) * 100, 4)
            if 'Retenciones' in rec.getparent().tag:
                amount_xml = amount_xml * -1
                rate_xml = rate_xml * -1

            taxes.append({'rate': rate_xml, 'tax': tax_xml,
                          'amount': amount_xml})
        return taxes

    def _search_invoice(self, cfdi):
        folio = cfdi.get('Folio')
        serie_folio = '%s%s' % (cfdi.get('Serie'), folio)
        domain = [
            '|', ('partner_id', 'child_of', self.partner_id.id),
            ('partner_id', '=', self.partner_id.id)]
        # The parameter l10n_mx_force_only_folio is used when the user create the invoices from a PO and only set
        # the folio in the reference.
        force_folio = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_force_only_folio', '')
        if serie_folio and force_folio:
            domain.append('|')
            domain.append(('ref', '=ilike', folio))
        if serie_folio:
            domain.append(('ref', '=ilike', serie_folio))
            return self.search(domain, limit=1)
        amount = float(cfdi.get('Total', 0.0))
        domain.append(('amount_total', '>=', amount - 1))
        domain.append(('amount_total', '<=', amount + 1))
        domain.append(('l10n_mx_edi_cfdi_name', '=', False))
        domain.append(('state', '!=', 'cancel'))

        # The parameter l10n_mx_edi_vendor_bills_force_use_date is used when the user create the invoices from a PO
        # and not assign the same date that in the CFDI.
        date_type = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_edi_vendor_bills_force_use_date')
        xml_date = fields.datetime.strptime(cfdi.get('Fecha').split('T')[0], '%Y-%m-%dT%H:%M:%S').date()

        if date_type == "day":
            domain.append(('invoice_date', '=', xml_date))
        elif date_type == "month":
            domain.append(('invoice_date', '>=', xml_date.replace(day=1)))
            last_day = xml_date.replace(
                day=1, month=xml_date.month + 1) - timedelta(days=1)
            domain.append(('invoice_date', '<=', last_day))

        return self.search(domain, limit=1)

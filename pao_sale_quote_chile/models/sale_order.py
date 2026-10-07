# -*- coding: utf-8 -*-
from babel.dates import format_date as babel_format_date
from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import is_html_empty
from odoo.tools.image import image_data_uri
from odoo.tools.misc import babel_locale_parse

FEMALE_TITLES = {'señora', 'señorita', 'sra', 'srta', 'madam', 'miss', 'mrs', 'ms'}
MALE_TITLES = {'señor', 'sr', 'mister', 'mr', 'sir'}

SIGNATURE_PLACEHOLDER = '[[FIRMA]]'


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pao_use_chile_format = fields.Boolean(
        string='Chile Quotation Format',
        compute='_compute_pao_use_chile_format',
    )
    pao_quote_format = fields.Html(
        string='Quotation Format',
        copy=False,
        help="Content printed in the quotation (between the logo header and the footer). "
             "Generated from the rate sheet of the quotation template, then freely editable.",
    )

    @api.depends('company_id')
    def _compute_pao_use_chile_format(self):
        configs = self.env['pao.quote.config'].sudo().search([('company_id', 'in', self.company_id.ids)])
        companies = configs.company_id
        for order in self:
            order.pao_use_chile_format = order.company_id in companies

    # ------------------------------------------------------------
    # CRUD: the format is generated automatically while it is empty
    # ------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._pao_generate_empty_quote_format()
        return orders

    def write(self, vals):
        res = super().write(vals)
        if 'sale_order_template_id' in vals:
            self._pao_generate_empty_quote_format()
        return res

    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------

    def action_pao_generate_quote_format(self):
        for order in self:
            if not order._pao_quote_rate():
                raise UserError(_(
                    "The quotation template '%(template)s' has no rate sheet. Assign one in "
                    "Sales > Configuration > Quotation Templates.",
                    template=order.sale_order_template_id.name or _('(none)'),
                ))
        self._pao_generate_quote_format()
        return True

    # ------------------------------------------------------------
    # Native hooks
    # ------------------------------------------------------------

    def _get_name_portal_content_view(self):
        if self.pao_use_chile_format:
            return 'pao_sale_quote_chile.sale_order_portal_content_chile'
        return super()._get_name_portal_content_view()

    # ------------------------------------------------------------
    # Format generation
    # ------------------------------------------------------------

    def _pao_get_quote_config(self):
        self.ensure_one()
        return self.env['pao.quote.config'].sudo().search([('company_id', '=', self.company_id.id)], limit=1)

    def _pao_quote_rate(self):
        self.ensure_one()
        return self.sale_order_template_id.sudo().pao_quote_rate_id

    def _pao_generate_empty_quote_format(self):
        self.filtered(
            lambda order: order.pao_use_chile_format
            and is_html_empty(order.pao_quote_format)
            and order._pao_quote_rate()
        )._pao_generate_quote_format()

    def _pao_generate_quote_format(self):
        for order in self.filtered('pao_use_chile_format'):
            order.pao_quote_format = order._pao_build_quote_format()

    def _pao_build_quote_format(self):
        """Rate sheet of the quotation template with the customer placeholders replaced."""
        self.ensure_one()
        order = self.with_context(lang=self._pao_quote_lang())
        contact = order._pao_quote_contact()
        partner = contact or order.partner_id
        commercial_partner = order.partner_id.commercial_partner_id
        values = {
            '[[NUMERO]]': order.name if (order.name or '').startswith('#') else f'#{order.name}',
            '[[CLIENTE]]': commercial_partner.name or '',
            '[[CONTACTO]]': contact.name or '',
            '[[EMAIL]]': partner.email or '',
            '[[TELEFONO]]': partner.phone or partner.mobile or 'No Registra.',
            '[[PAIS]]': commercial_partner.country_id.name or '',
            '[[FECHA]]': order._pao_quote_date_label(),
            '[[SALUDO]]': order._pao_quote_greeting(),
        }
        html = str(order._pao_quote_rate().content or '')
        for placeholder, value in values.items():
            html = html.replace(placeholder, str(escape(value)))
        return Markup(html)

    def _pao_render_quote_format(self):
        """Printable content: the saved format (built on the fly when empty) with the signature image."""
        self.ensure_one()
        html = self.pao_quote_format
        if is_html_empty(html) and self._pao_quote_rate():
            html = self._pao_build_quote_format()
        signature = self._pao_get_quote_config().signature_image
        image = (
            str(Markup('<img src="%s" style="max-height: 90px;" alt="Firma"/>') % image_data_uri(signature))
            if signature else ''
        )
        return Markup(str(html or '').replace(SIGNATURE_PLACEHOLDER, image))

    # ------------------------------------------------------------
    # Placeholder values
    # ------------------------------------------------------------

    def _pao_quote_lang(self):
        lang = self._get_lang()
        return lang if lang and lang.startswith('es') else 'es_CL'

    def _pao_quote_date_label(self):
        """'Septiembre 2026.'"""
        self.ensure_one()
        if not self.date_order:
            return ''
        label = babel_format_date(
            self.date_order.date(), format='MMMM y', locale=babel_locale_parse(self._pao_quote_lang()),
        )
        return label[:1].upper() + label[1:] + '.'

    def _pao_quote_contact(self):
        """Contact person of the quotation, empty when the customer itself is the order partner."""
        self.ensure_one()
        partner = self.partner_id
        return partner if partner != partner.commercial_partner_id and not partner.is_company else partner.browse()

    def _pao_quote_greeting(self):
        """'Estimada Karina:' using the contact title, never guessing from the name."""
        self.ensure_one()
        contact = self._pao_quote_contact()
        if not contact:
            return 'Estimados:'
        titles = {
            (value or '').strip().lower().rstrip('.')
            for value in (contact.title.shortcut, contact.title.name)
        }
        if titles & FEMALE_TITLES:
            word = 'Estimada'
        elif titles & MALE_TITLES:
            word = 'Estimado'
        else:
            word = 'Estimado/a'
        first_name = (contact.name or '').split()[0] if contact.name else ''
        return f'{word} {first_name}:' if first_name else f'{word}:'

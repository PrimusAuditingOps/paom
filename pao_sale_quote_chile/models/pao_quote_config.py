# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import fields, models
from odoo.tools import file_open

DEFAULT_FORMAT_TEMPLATE_PATH = 'pao_sale_quote_chile/data/pao_quote_default_format.html'

DEFAULT_FOOTER_OFFICES = Markup(
    "<b>USA:</b> HQ Santa Maria, CA &#9679; Brandon, FL &#9679; "
    "<b>Mexico:</b> Guadalajara &#9679; Culiacán &#9679; Uruapan &#9679; "
    "<b>Costa Rica:</b> San José &#9679; <b>Chile:</b> Viña del Mar"
)


def default_format_template():
    """Sample format taken from the manual GLOBALG.A.P. quotations of Primus Auditing Ops Chile."""
    with file_open(DEFAULT_FORMAT_TEMPLATE_PATH) as template_file:
        return Markup(template_file.read())


class PaoQuoteConfig(models.Model):
    _name = 'pao.quote.config'
    _description = 'Chile Quotation Format'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        default=lambda self: self.env.company,
    )
    logo = fields.Binary(string='Logo', help="Logo printed in the header. Uses the company logo when empty.")
    signature_image = fields.Binary(string='Signature Image', help="Image printed in place of [[FIRMA]].")
    default_format_template = fields.Html(
        string='Default Format',
        default=lambda self: default_format_template(),
        help="Format used when the quotation has no quotation template, or its template has no Chile format.",
    )

    # Footer
    footer_address = fields.Char(
        string='Footer Address',
        default='Avenida Libertad No. 798, Oficina 902 Viña del Mar, Chile',
    )
    footer_offices = fields.Html(string='Footer Offices', default=DEFAULT_FOOTER_OFFICES)
    footer_email = fields.Char(string='Footer Email', default='paochile@primusauditingops.com')
    footer_phone = fields.Char(string='Footer Phone', default='+56.32.361.2313')
    footer_website = fields.Char(string='Footer Website', default='primusauditingops.com')

    _sql_constraints = [
        ('company_uniq', 'unique(company_id)', 'There can only be one quotation format per company.'),
    ]

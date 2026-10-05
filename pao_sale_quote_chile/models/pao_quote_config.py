# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import fields, models

DEFAULT_INTRO_LONG = Markup(
    "<p>Muchas gracias por su interés en los servicios que ofrece Primus Auditing Ops.<br/>"
    "Una de las principales ventajas de nuestra compañía es que los reportes de auditoría cuentan con una "
    "herramienta de traducción automática gratuita además de poder vincular los informes de auditorías "
    "PrimusGFS, GLOBALG.A.P. y Primus Estándar a la plataforma de Azzule.com para ser transferidas a sus "
    "Clientes/Compradores. A continuación, detallamos los valores de acuerdo a los servicios solicitados. "
    "Los precios indicados no incluyen IVA.</p>"
)

DEFAULT_INTRO_SHORT = Markup(
    "<p>Muchas gracias por su interés en los servicios que ofrece Primus Auditing Ops.<br/>"
    "A continuación, detallamos los valores de acuerdo a los servicios solicitados:</p>"
)

DEFAULT_CLOSING = Markup(
    "<p>Esperamos que esta propuesta sea satisfactoria para sus expectativas de inversión en inocuidad, "
    "además de que esta temporada sea de excelentes resultados, agradecemos de antemano su intención de "
    "trabajar con el equipo de Primus Auditing Ops - Chile.</p>"
    "<p>Quedamos atentos a sus consultas y/o dudas.</p>"
    "<p>Saludos Cordiales.</p>"
)

DEFAULT_SIGNATURE_TEXT = Markup(
    "<p>Katherine Legua S.<br/>"
    "<small>Director of Primus Auditing Ops<br/>"
    "Chile and South America<br/>"
    "Klegua@pao-cl.com<br/>"
    "Av. Libertad #798, oficina 902.<br/>"
    "Viña del Mar - Chile.<br/>"
    "Office (+56 32) 361 2313.<br/>"
    "Mobile (+569) 84298135</small></p>"
)

DEFAULT_FOOTER_OFFICES = Markup(
    "<b>USA:</b> HQ Santa Maria, CA &#9679; Brandon, FL &#9679; "
    "<b>Mexico:</b> Guadalajara &#9679; Culiacán &#9679; Uruapan &#9679; "
    "<b>Costa Rica:</b> San José &#9679; <b>Chile:</b> Viña del Mar"
)


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

    # Header
    logo = fields.Binary(string='Logo', help="Logo printed in the quotation header. Uses the company logo when empty.")
    title = fields.Char(string='Document Title', default='Cotización Servicios Auditorias', required=True)

    # Body texts
    intro_long = fields.Html(
        string='Introduction (long)',
        default=DEFAULT_INTRO_LONG,
        help="Used when at least one scheme of the quotation is marked to use the long introduction.",
    )
    intro_short = fields.Html(
        string='Introduction (short)',
        default=DEFAULT_INTRO_SHORT,
        help="Used when no scheme of the quotation asks for the long introduction.",
    )
    billing_title = fields.Char(string='Billing Section Title', default='Consideraciones de Facturación')
    closing = fields.Html(string='Closing Text', default=DEFAULT_CLOSING)
    signature_image = fields.Binary(string='Signature Image')
    signature_text = fields.Html(string='Signature Text', default=DEFAULT_SIGNATURE_TEXT)
    additional_title = fields.Char(string='Additional Information Title', default='INFORMACIÓN ADICIONAL')

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

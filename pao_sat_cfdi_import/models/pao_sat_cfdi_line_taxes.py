import base64
from lxml import etree
from odoo import models, fields, api
from logging import getLogger

_logger = getLogger(__name__)


class PAOSatCfdiLineTaxes(models.Model):
    _name = 'pao.sat.cfdi.line.taxes'
    _description = 'SAT CFDI Lines Taxes'


    name = fields.Selection(
        [
            ('001', 'ISR'),
            ('002', 'IVA'),
            ('003', 'IEPS'),
        ],
        string="Name",
    )
    tax_type = fields.Selection(
        [
            ('traslado', 'Traslado'),
            ('retencion', 'Retención'),
        ],
        string="Type",
    )
    base = fields.Float(string="base")
    factor_type = fields.Char(string="Factor Type")
    rate = fields.Float(string="Rate")
    amount = fields.Float(string="Amount")
    cfdi_line_id = fields.Many2one(
        'pao.sat.cfdi.xml.line',
        string="CFDI Line",
        ondelete='cascade'
    )
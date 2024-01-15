from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapDestinationCountries(models.Model):
    _name = "pao.globalgap.destination.countries"
    _description = "GLOBALG.A.P. Destination countries"

    name = fields.Char(
        string='Name', 
        copy=False,
        translate=True, 
    )
   
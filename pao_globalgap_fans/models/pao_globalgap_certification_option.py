from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoGlobalgapCertificationOption(models.Model):
    _name = "pao.globalgap.certification.option"
    _description = "GLOBALG.A.P. Certification Option"

    name = fields.Char(
        string='Name', 
        copy=False,
        translate=True, 
    )
   
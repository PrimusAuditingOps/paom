from odoo import fields, models
from logging import getLogger


_logger = getLogger(__name__)

class hrEmployeeInherit(models.Model):
    _inherit='hr.employee'


    es_sign_signature = fields.Binary(
        string="Digital Signature", 
    )
    
    

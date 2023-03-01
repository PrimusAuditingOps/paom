from odoo import fields, models, api, _
from logging import getLogger


_logger = getLogger(__name__)

class RegistrationNumberServices(models.Model):
    _name = "pao.registration.number.services"
    _description = "Registration number services"



    name = fields.Char(
        string="Service",
    )
    product_uom_qty = fields.Float(
        string="Quantity", 
        default=0.0,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        required=True, 
        ondelete='Restrict',
    )
    price_subtotal = fields.Monetary(
        string="Subtotal",
        currency_field='currency_id',
    )
    registration_number_to_sign_id = fields.Many2one(
        comodel_name='pao.registration.number.to.sign',
        string="Registration number Reference",
        ondelete='Cascade',
    )



from odoo import fields, models, api, _
import uuid
from logging import getLogger
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang

_logger = getLogger(__name__)

class PaoCustomerRegistrationContact(models.Model):
    _name='pao.customer.registration.contact'
    _description = 'Customer Registration Contact'
    

    @api.model
    def _default_access_token(self):
        return uuid.uuid4().hex
    name = fields.Char(
        string="Name",
    )
    occupation = fields.Char(
        string="Occupation",
    )
    email = fields.Char(
        string="Email",
    )
    phone = fields.Char(
        string="Phone",
    )
    customer_registration_id = fields.Many2one(
        comodel_name='pao.customer.registration',
        string='Customer registration',
        ondelete='cascade'
    )
   
    
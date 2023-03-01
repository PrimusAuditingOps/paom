from odoo import fields, models, api, _
from logging import getLogger


_logger = getLogger(__name__)

class RegistrationNumberToSign(models.Model):
    _name = "pao.registration.number.to.sign"
    _description = "Registration number to sign"


    name = fields.Char(
        string="Registration number",
    )
    scheme = fields.Char(
        string="Scheme",
    )
    version = fields.Char(
        string="Version",
    )
    customer_name = fields.Char(
        string="Customer",
    )
    customer_vat = fields.Char(
        string="Customer VAT",
    )
    phone = fields.Char(
        string="Phone",
    )
    contract_email = fields.Char(
        string="Contract email",
    )
    invoice_email = fields.Char(
        string="Invoice email",
    )
    organization_name = fields.Char(
        string="Organization",
    )
    organization_vat = fields.Char(
        string="Organization VAT",
    )
    organization_address = fields.Text(
        string="Organization Address",
    )
    organization_city = fields.Char(
        string="Organization city",
    )
    organization_state = fields.Char(
        string="Organization state",
    )
    organization_country = fields.Char(
        string="Organization country",
    )
    start_date = fields.Date(
        string="Start date",
    )
    end_date = fields.Date(
        string="End date",
    )
    audit_type = fields.Char(
        string="Audit type",
    )
    audit_scope = fields.Char(
        string="Audit scope",
    )
    products = fields.Text(
        string="Products",
    )
    client_requirements = fields.Char(
        string="Client requirements",
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        required=True, 
        ondelete='Restrict',
    )
    audit_duration = fields.Char(
        string="Audit duration",
    )
    coordinator_id = fields.Many2one(
        string="Coordinator",
        comodel_name='res.users',
        ondelete='set null',
        domain = [('share','=',False)],
    )
    sign_sa_agreements_id = fields.Many2one(
        comodel_name='pao.sign.sa.agreements.sent',
        string='Service Agreement',
        ondelete='Cascade',
    )
    services_ids = fields.One2many(
        comodel_name='pao.registration.number.services',
        inverse_name='registration_number_to_sign_id',
        string="Services",
        auto_join=True
    )
from odoo import fields, models, api
class ServicereferralagreementRegistryNumber(models.Model):
    _name = 'servicereferralagreement.registrynumber'
    _description = 'Modelo para manejar el catalogo de numero de registro de las organizaciones'

    name = fields.Char(
        string="Registry number",
        help='Enter registry number',
        required= True,
    )
    scheme_id = fields.Many2one(
        comodel_name = 'servicereferralagreement.scheme', 
        string='Scheme', 
        help='Select scheme', 
        ondelete='restrict',
        required=True,
    )
    version_scheme = fields.Char(
        related="scheme_id.version",
    )
    organization_id = fields.Many2one(
        comodel_name='servicereferralagreement.organization',
        string='Organization',
        help='Select organization', 
        ondelete='set null',
    )
    type_of_audit = fields.Char(
        string="Type of audit",
    )
    audit_scope = fields.Char(
        string="Audit scope",
    )
    audit_duration = fields.Char(
        string="Audit duration",
    )

    client_requirements = fields.Char(
        string="Client requirements",
    )
    contract_email = fields.Text(
        string="Contract E-mail",
    )
    phone = fields.Text(
        string="Phone",
    )
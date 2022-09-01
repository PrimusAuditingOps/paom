from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    paa_audit_quantity = fields.Integer(
        string="Number of Audit"
    )
    paa_currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
    )
    
    paa_audits_honorarium_total = fields.Monetary(
        string="Total honorarium of audits",
        currency_field='paa_currency_id',
    )
    
    paa_blocked_organizations_ids = fields.Many2many(
        'servicereferralagreement.organization',
        'servicereferralagreement_blocked_organizations_res_partner_rel',
        'res_partner_id', 'servicereferralagreement_blocked_organization_id',
        string='Blocked organizations',
    )
    paa_blocked_company_ids = fields.Many2many(
        'res.partner',
        'assignment_auditor_blocked_company_res_partner_rel',
        'res_partner_id', 'assignment_blocked_company_id',
        string='Blocked Customers',
    )
    paa_rating_scheme_ids = fields.One2many(
        comodel_name='paoassignmentauditor.schemeranking',
        inverse_name='partner_id',
        string='scheme rating',
    )
   
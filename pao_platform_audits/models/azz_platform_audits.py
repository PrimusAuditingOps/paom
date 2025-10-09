from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class PaoAzzPlatformAudits(models.Model):
    _name = "pao.azz.platform.audits"
    _description = "PAO Azz Platform Audits"
    _rec_name = "audit_id"

    audit_date = fields.Date(
        required=True,
        string= "Audit Date",
    )
    finished_date = fields.Date(
        string= "Finished Date",
    )
    audit_id = fields.Char(
        required=True,
        string= "Audit ID",
    )
    status = fields.Char(
        required=True,
        string= "Status",
    )
    app_id = fields.Char(
        required=True,
        string= "App ID",
    )
    is_announced = fields.Char(
        string= "Is Announced",
    )
    pre_assessment = fields.Char(
        string= "Pre-assessment",
    )
    audit_template = fields.Char(
        required=True,
        string= "Audit Template",
    )
    template_version = fields.Char(
        required=True,
        string= "Template Version",
    )
    organization = fields.Char(
        required=True,
        string= "Organization",
    )
    organization_contact_name = fields.Char(
        string= "Organization Contact Name",
    )
    organization_contact_email = fields.Char(
        string= "Organization Contact Email",
    )
    entities = fields.Char(
        string= "Entities",
    )
    auditor = fields.Char(
        required=True,
        string= "Auditor",
    )
    coordinator = fields.Char(
        string= "Coordinator",
    )
    plc = fields.Char(
        string= "PLC",
    )
    cycle = fields.Char(
        string= "Cycle",
    )
    country = fields.Char(
        string= "Country",
    )
    state = fields.Char(
        string= "State",
    )
    city = fields.Char(
        string= "City",
    )
    certification_decision_date = fields.Date(
        string= "Certification Decision Date",
    )
    commodities = fields.Char(
        string= "Commodities",
    )
    shipper = fields.Char(
        string= "Shipper",
    )

    #Related Fields
    organization_id = fields.Many2one(
        comodel_name='servicereferralagreement.organization',
        string='Organization',
        compute='_compute_organization',
        store=True,
        ondelete='restrict',
    ) 
    registration_number_id = fields.Many2one(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registration Number',
        compute='_compute_registration_number',
        store=True,
        ondelete='restrict',
    )    
    

    @api.depends('organization')
    def _compute_organization(self):
        for rec in self:
            rec.organization_id = None
            domain = [("name","=",rec.organization)]
            organization = self.env["servicereferralagreement.organization"].search(domain)
            if organization:
                for org in organization:
                    rec.organization_id = org.id
            else:
                organization_search = self._search_organization(rec.organization)
                if organization_search:
                    for organization_s in organization_search:
                        rec.organization_id = organization_s.id
                        break
                    if not rec.plc or rec.plc != "1": #Is not an Organic Audit
                        if rec.app_id:
                            for org in organization_reg_number:
                                domain = [("organization_id","=",org.id),("name","ilike",str(rec.app_id) if not rec.plc else rec.plc)]
                                reg_number = self.env["servicereferralagreement.registrynumber"].search(domain)
                                rec.organization_id = org.id
                                break
                                
                        
    def _search_organization(self, organization):
        records = self.env["servicereferralagreement.organization"].search([("name", "ilike", organization.lower())])
        records = records.sorted(
            key=lambda r: (
                (r.name or '').lower().find(organization.lower()) if organization.lower() in (r.name or '').lower() else 9999,
                abs(len(r.name or '') - len(organization))
            )
        )
        return records                
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
    audit_id = fields.Integer(
        required=True,
        string= "Audit ID",
    )
    status = fields.Char(
        required=True,
        string= "Status",
    )
    app_id = fields.Integer(
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


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
        required=True,
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
        required=True,
        string= "Is Announced",
    )
    pre_assessment = fields.Char(
        required=True,
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
        required=True,
        string= "Organization Contact Name",
    )
    organization_contact_email = fields.Char(
        required=True,
        string= "Organization Contact Email",
    )
    entities = fields.Char(
        required=True,
        string= "Entities",
    )
    auditor = fields.Char(
        required=True,
        string= "Auditor",
    )
    coordinator = fields.Char(
        required=True,
        string= "Coordinator",
    )
    plc = fields.Char(
        required=True,
        string= "PLC",
    )
    cycle = fields.Char(
        required=True,
        string= "Cycle",
    )
    country = fields.Char(
        required=True,
        string= "Country",
    )
    state = fields.Char(
        required=True,
        string= "State",
    )
    city = fields.Char(
        required=True,
        string= "City",
    )
    certification_decision_date = fields.Date(
        required=True,
        string= "Certification Decision Date",
    )
    commodities = fields.Char(
        required=True,
        string= "Commodities",
    )
    shipper = fields.Char(
        required=True,
        string= "Shipper",
    )


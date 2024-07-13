from odoo import fields, models



class PurchaseReportInherit(models.Model):
    _inherit = 'purchase.report'

    shadow_id = fields.Many2one('res.partner', string="Shadow", readonly = True)
    assessment_id = fields.Many2one('res.partner', string="Assessment",
                                    readonly = True)
    ado_is_external_audit = fields.Boolean(string="Is an external audit",
                                           readonly = True)
    ac_audit_status = fields.Many2one('auditconfirmation.auditstate',
                                      string="Audit status",
                                      readonly = True)
    coordinator_id = fields.Many2one('res.users', string="Coordinator",
                                     readonly = True)
    audit_country_id = fields.Many2one('res.country', string = 'Audit Country',
                                       readonly = True)  
    audit_state_id = fields.Many2one('res.country.state', string = 'Audit State',
                                     readonly = True)
    audit_city_id = fields.Many2one('res.city', string='Audit City',
                                    readonly = True)
    organization_id = fields.Many2one('servicereferralagreement.organization',
                                      string='Organization',
                                      readonly = True)
    registrynumber_id = fields.Many2one('servicereferralagreement.registrynumber',
                                        string='Registry number',
                                        readonly = True)
    service_start_date = fields.Date(string="Service start date", readonly = True)
    service_end_date = fields.Date(string="Service end date", readonly = True)
    
    def _select(self):
        return super(PurchaseReportInherit, self)._select() + ", po.shadow_id as shadow_id, po.assessment_id as assessment_id, po.ado_is_external_audit as ado_is_external_audit, po.ac_audit_status as ac_audit_status, po.coordinator_id as coordinator_id, po.audit_country_id as audit_country_id, po.audit_state_id as audit_state_id, po.audit_city_id as audit_city_id, l.organization_id as organization_id, l.registrynumber_id as registrynumber_id, l.service_start_date as service_start_date, l.service_end_date as service_end_date"

    def _group_by(self):
        return super(PurchaseReportInherit, self)._group_by() + ", po.shadow_id, po.assessment_id, po.ado_is_external_audit, po.ac_audit_status, po.coordinator_id, po.audit_country_id, po.audit_state_id, po.audit_city_id, l.organization_id, l.registrynumber_id, l.service_start_date, l.service_end_date"

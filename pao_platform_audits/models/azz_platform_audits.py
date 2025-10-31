from odoo import fields, models, api, _
from logging import getLogger
from dateutil.relativedelta import relativedelta

_logger = getLogger(__name__)

class PaoAzzPlatformAudits(models.Model):
    _name = "pao.azz.platform.audits"
    _description = "PAO Azz Platform Audits"
    _rec_name = "audit_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _sql_constraints = [
        ('uc_pao_platform_audit',
         'UNIQUE(audit_id,company_id,audit_date,organization,plc)',
         "There is already an Audit with this ID"),
    ]

    active = fields.Boolean(string="Active", default=True)
    
    company_id = fields.Many2one(
        'res.company', 
        'Company', 
        copy=False,
        index=True,
        default=lambda self: self.env.company
    )

    search_state = fields.Selection(
        selection=[
            ('not_found', "Not Found"),
            ('needs_validation', "Needs Validation"),
            ('found', "Found"),
        ],
        string="Search Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='not_found'
    )

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
        string= "Audit Status",
    )
    app_status = fields.Char(
        string= "APP Status",
    )
    app_id = fields.Char(
        required=True,
        string= "App ID",
    )
    is_announced = fields.Char(
        string= "Is Announced",
    )
    module_9 = fields.Char(
        string= "Module 9",
    )
    autid_type_code = fields.Char(
        string= "Audit Type Code",
    )
    preventive_control = fields.Char(
        string= "Preventive Control",
    )
    audit_visit_type = fields.Char(
        string= "Audit Visit Type",
    )
    pre_assessment = fields.Char(
        string= "Pre-assessment",
    )
    audit_template = fields.Char(
        required=True,
        string= "Audit Template",
    )
    template_version = fields.Char(
        string= "Template Version",
    )
    organization = fields.Char(
        required=True,
        string= "Platform Organization",
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
        string= "Platform Auditor",
    )
    coordinator = fields.Char(
        string= "Platform Coordinator",
    )
    plc = fields.Char(
        string= "Platform Registration Number",
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
    entity_ids = fields.Many2many(
        'pao.platform.entities', 
        'pao_azz_platform_audits_pao_platform_entities_rel',
        'platform_id', 
        'entity_id', 
        string='Entities',
        compute='_compute_entity_ids',
        store=True,
    )

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
    audit_template_id = fields.Many2one(
        comodel_name='pao.azz.audit.template',
        string='Audit Template',
        compute='_compute_audit_template',
        store=True,
        ondelete='restrict',
    ) 
    audit_template_version_id = fields.Many2one(
        comodel_name='pao.azz.template.version',
        string='Audit Template Version',
        compute='_compute_audit_template_version',
        store=True,
        ondelete='restrict',
    ) 
    operation_specialist_id = fields.Many2one(
        comodel_name='pao.platform.coordinator',
        string='Operation Specialist',
        compute='_compute_operation_specialist_id',
        store=True,
        ondelete='restrict',
    ) 
    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Sale Order Line',
        compute='_compute_sale_order_line',
        store=True,
    )
    sale_order_line_name = fields.Text(
        related='sale_order_line_id.name'
    )
    order_state = fields.Selection(
        related='sale_order_line_id.state'
    )
    order_id = fields.Many2one(
        related='sale_order_line_id.order_id'
    )
    coordinator_id = fields.Many2one(
        related='sale_order_line_id.coordinator_id'
    )
    purchase_order_line_id = fields.Many2one(
        'purchase.order.line',
        string='Purchase Order Line',
        compute='_compute_purchase_order_line',
        store=True,
    )
    purchase_order_line_name = fields.Text(
        related='purchase_order_line_id.name'
    )
    purchase_state = fields.Selection(
        related='purchase_order_line_id.state'
    )
    pruchase_id = fields.Many2one(
        related='purchase_order_line_id.order_id'
    )
    pruchase_country = fields.Many2one(
        related='purchase_order_line_id.order_id.audit_country_id'
    )
    pruchase_id_state = fields.Many2one(
        related='purchase_order_line_id.order_id.audit_state_id'
    )
    pruchase_id_city = fields.Many2one(
        related='purchase_order_line_id.order_id.audit_city_id'
    )
    pruchase_partner_id = fields.Many2one(
        related='purchase_order_line_id.order_id.partner_id'
    )

    @api.depends('entities')
    def _compute_entity_ids(self):
        for rec in self:
            ids = []
            rec.entity_ids = None
            if rec.entities:
                if rec.plc and 'PA-PGFS'in rec.plc:
                    rec_entity = self.env["pao.platform.entities"].search([("name","=",rec.entities)],limit=1)
                    if not rec_entity:
                        rec_entity = self.env["pao.platform.entities"].create({"name": rec.entities }) 
                    ids.append(rec_entity.id)
                
                else:
                    entity_list = rec.entities.split('|')
                    for entity in entity_list:
                        if entity and entity.strip() != "":
                            entity_type = entity.split(':')
                            type_name = entity_type[0].strip()
                            entity_name = entity_type[1].strip()
                            rec_type = self.env["pao.platform.entities.type"].search([("name","=",type_name)], limit=1)
                            if not rec_type:
                                rec_type = self.env["pao.platform.entities.type"].create({"name": type_name})
                                rec_entity = self.env["pao.platform.entities"].create({"name": entity_name, "entity_type_id": rec_type.id })
                                ids.append(rec_entity.id)
                            else:
                                rec_entity = self.env["pao.platform.entities"].search([("name","=",entity_name)],limit=1)
                                if not rec_entity:
                                    rec_entity = self.env["pao.platform.entities"].create({"name": entity_name, "entity_type_id": rec_type.id }) 
                                ids.append(rec_entity.id)

            if len(ids) > 0:
                rec.entity_ids = [(6, 0, ids)]

    @api.depends('sale_order_line_id')
    def _compute_purchase_order_line(self):
        for rec in self:
            pol_id = None
            if rec.sale_order_line_id:
                purchase_line = self.env["purchase.order.line"].search([("company_id","=",rec.company_id.id),("state","!=","cancel"),("sra_sale_line_ids","in",[rec.sale_order_line_id.id])])
                for line in purchase_line:
                    pol_id = line.id
                    break
            if not pol_id:       
                date_search = rec.audit_date - relativedelta(months=6)
                domain = [("create_date",">=",date_search),("state","!=","cancel")]
                if rec.organization_id:
                    domain.append(("organization_id","=",rec.organization_id.id))
                    if rec.registration_number_id:
                        domain.append(("registrynumber_id","=",rec.registration_number_id.id))
                    rec_purchase_order_line = self.env["purchase.order.line"].search(domain,order='id desc')
                    for line in rec_purchase_order_line:
                        if line.product_id.id in rec.audit_template_id.product_ids.ids:
                            if len(line.pao_platform_audit_ids.ids) != line.product_qty and line.product_qty > 0:
                                pol_id = line.id
                                rec.search_state = "needs_validation"
                                break
                    if not pol_id:
                        for line in rec_purchase_order_line:
                            if line.product_id.can_be_commissionable and not line.product_id.is_travel_expenses:
                                if len(line.pao_platform_audit_ids.ids) != line.product_qty and line.product_qty > 0:
                                    pol_id = line.id
                                    rec.search_state = "needs_validation"                        
                                    break
            if pol_id:
                rec.purchase_order_line_id = pol_id
                #rec.write({"pao_platform_audit_ids": [(4,pol_id)]})
                rec.purchase_order_line_id.write({"pao_platform_audit_ids": [(4,rec.id)]})
                if rec.module_9 and rec.module_9.lower() == "yes":
                    for line in rec.purchase_order_line_id.order_id.order_line.filtered(lambda l: l.product_id.pao_is_module_9 == True):
                        if len(line.pao_platform_audit_ids.ids) != line.product_qty and line.product_qty > 0:
                            line.write({"pao_platform_audit_ids": [(4,rec.id)]})
                            break

    @api.depends('audit_template_id')
    def _compute_sale_order_line(self):
        for rec in self:
            date_search = rec.audit_date - relativedelta(months=6)
            domain = [("create_date",">=",date_search),("state","!=","cancel"),("company_id","=",rec.company_id.id)]
            sol_id = None
            first_sol_id = None
            if rec.organization_id:
                domain.append(("organization_id","=",rec.organization_id.id))
                if rec.registration_number_id:
                    domain.append(("registrynumber_id","=",rec.registration_number_id.id))
                
                rec_sale_order_line = self.env["sale.order.line"].search(domain,order='id desc')
                rec_sale_ol = rec_sale_order_line.filtered(lambda l: not l.order_id.pao_is_a_child_sales_order)
                
                for line in rec_sale_ol:
                    if sol_id:
                        break
                    if line.product_id.id in rec.audit_template_id.product_ids.ids:
                        if len(line.pao_platform_audit_ids.ids) != line.product_uom_qty and line.product_uom_qty > 0:
                            rec.search_state = "found"
                            if not first_sol_id:
                                first_sol_id = line.id
                            if rec.entity_ids:
                                for ent in rec.entity_ids:
                                    if ent.name.lower() in line.name.lower():
                                        sol_id = line.id
                                        break
                              
                if not sol_id and first_sol_id:
                    sol_id = first_sol_id
                if not sol_id:
                    for line in rec_sale_ol:
                        if line.product_id.can_be_commissionable and not line.product_id.is_travel_expenses:
                            if len(line.pao_platform_audit_ids.ids) != line.product_uom_qty and line.product_uom_qty > 0:
                                rec.search_state = "needs_validation"
                                sol_id = line.id                        
                                break
            if sol_id:
                rec.sale_order_line_id = sol_id
                rec.sale_order_line_id.write({"pao_platform_audit_ids": [(4,rec.id)]})
                #Child Orders
                if rec.sale_order_line_id.order_id.pao_is_a_master_sales_order:
                    child_orders = self.env["sale.order"].search([("pao_parent_id","=",rec.sale_order_line_id.order_id.id)])
                    for child in child_orders:
                        for line_child in child.order_line:
                            if line_child.product_id.id in rec.audit_template_id.product_ids.ids and line_child.organization_id.id == rec.sale_order_line_id.organization_id.id and line_child.registrynumber_id.id == rec.sale_order_line_id.registrynumber_id.id:
                                if len(line_child.pao_platform_audit_ids.ids) != line_child.product_uom_qty and line_child.product_uom_qty > 0:
                                    line_child.write({"pao_platform_audit_ids": [(4,rec.id)]})

                        if rec.module_9 and rec.module_9.lower() == "yes":
                            for line_module_9 in child.order_line.filtered(lambda l: l.product_id.pao_is_module_9 == True):
                                if line_module_9.organization_id.id == rec.sale_order_line_id.organization_id.id and line_module_9.registrynumber_id.id == rec.sale_order_line_id.registrynumber_id.id:
                                    if len(line_module_9.pao_platform_audit_ids.ids) != line_module_9.product_uom_qty and line_module_9.product_uom_qty > 0:
                                        line_module_9.write({"pao_platform_audit_ids": [(4,rec.id)]})
                if rec.module_9 and rec.module_9.lower() == "yes":
                    for line in rec.sale_order_line_id.order_id.order_line.filtered(lambda l: l.product_id.pao_is_module_9 == True):
                        if len(line.pao_platform_audit_ids.ids) != line.product_uom_qty and line.product_uom_qty > 0:
                            line.write({"pao_platform_audit_ids": [(4,rec.id)]})
                            break
            
    def _search_sale_order_line(self, organization):
        records = self.env["servicereferralagreement.organization"].search([("company_id","=",self.company_id.id),("name", "ilike", organization.lower())])
        records = records.sorted(
            key=lambda r: (
                (r.name or '').lower().find(organization.lower()) if organization.lower() in (r.name or '').lower() else 9999,
                abs(len(r.name or '') - len(organization))
            )
        )
        return records                
    
    @api.depends('audit_template_id')
    def _compute_audit_template_version(self):
        for rec in self:
            rec.audit_template_version_id = None
            if rec.audit_template_id and rec.template_version:
                rec_template_version = self.env["pao.azz.template.version"].search([("name","=",rec.template_version)], limit=1)
                if not rec_template_version:
                    template_version = self.env["pao.azz.template.version"].create({"name": rec.template_version,"pao_audit_template_id": rec.audit_template_id.id})
                    rec.audit_template_version_id = template_version.id
                else: 
                    rec.audit_template_version_id = rec_template_version.id

    @api.depends('coordinator')
    def _compute_operation_specialist_id(self):
        for rec in self:
            rec.operation_specialist_id = None
            if rec.coordinator:
                recCoordinator = self.env["pao.platform.coordinator"].search([("name","=",rec.coordinator)], limit=1)
                if not recCoordinator:
                    coordinator = self.env["pao.platform.coordinator"].create({"name": rec.coordinator})
                    rec.operation_specialist_id = coordinator.id
                else: 
                    rec.operation_specialist_id = recCoordinator.id
    
    @api.depends('audit_template')
    def _compute_audit_template(self):
        for rec in self:
            rec.audit_template_id = None
            if rec.audit_template:
                rectemplate = self.env["pao.azz.audit.template"].search([("name","=",rec.audit_template)], limit=1)
                if not rectemplate:
                    template = self.env["pao.azz.audit.template"].create({"name": rec.audit_template})
                    rec.audit_template_id = template.id
                else: 
                    rec.audit_template_id = rectemplate.id
    
    @api.depends('organization_id')
    def _compute_registration_number(self):
        for rec in self:
            rec.registration_number_id = None
            if rec.organization_id:
                if not rec.plc or rec.plc != "1": #Is not an Organic Audit
                    if rec.app_id:
                        registration_number = self._search_registration_number(rec.organization_id.id,str(rec.app_id) if not rec.plc else rec.plc)
                        for rn in registration_number:      
                            rec.registration_number_id = rn.id
                            break

    @api.depends('organization')
    def _compute_organization(self):
        for rec in self:
            rec.organization_id = None
            domain = [("name","=",rec.organization),("company_id","=",rec.company_id.id)]
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
                            for org in organization_search:
                                domain = [("company_id","=",rec.company_id.id),("organization_id","=",org.id),("name","ilike",str(rec.app_id) if not rec.plc else rec.plc)]
                                reg_number = self.env["servicereferralagreement.registrynumber"].search(domain)
                                rec.organization_id = org.id
                                break
                                
    def _search_registration_number(self, organization,registration_number):
        domain = [("company_id","=",self.company_id.id),("organization_id","=",organization),("name","ilike",registration_number.lower())]
        records = self.env["servicereferralagreement.registrynumber"].search(domain)
        records = records.sorted(
            key=lambda r: (
                (r.name or '').lower().find(registration_number.lower()) if registration_number.lower() in (r.name or '').lower() else 9999,
                abs(len(r.name or '') - len(registration_number))
            )
        )
        return records 

    def _search_organization(self, organization):
        records = self.env["servicereferralagreement.organization"].search([("company_id","=",self.company_id.id),("name", "ilike", organization.lower())])
        records = records.sorted(
            key=lambda r: (
                (r.name or '').lower().find(organization.lower()) if organization.lower() in (r.name or '').lower() else 9999,
                abs(len(r.name or '') - len(organization))
            )
        )
        return records                

    def validate_audit(self):
        for rec in self:
            rec.write({"search_state": "found"})

    def search_audit(self):
        for rec in self:
            rec.purchase_order_line_id = None
            rec.sale_order_line_id = None
            
            if not rec.organization_id:
                rec._compute_organization()
            if not rec.registration_number_id:
                rec._compute_registration_number()

            rec._compute_sale_order_line()
            rec._compute_purchase_order_line()

    def unlink_audit(self):
        for rec in self:
            #[("pao_platform_audit_ids", "in", [19572])]
            #

            if rec.purchase_order_line_id:
                rec.purchase_order_line_id.write({'pao_platform_audit_ids': [(3, rec.id)]})
            if rec.sale_order_line_id:
                rec.sale_order_line_id.write({'pao_platform_audit_ids': [(3, rec.id)]})

            rec.purchase_order_line_id = None
            rec.sale_order_line_id = None
            rec.search_state = "not_found"
from asyncore import read
from itertools import product
from odoo import tools
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)

class ServiceReferralAgreementAgenda(models.Model):
    _name = "servicereferralagreement.agenda"
    _description = "Auditor Agenda"
    _auto = False
    _rec_name = 'combination'
    _order = 'service_start_date desc'


    id = fields.Integer('ID', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Auditor', readonly=True)
    partner_ref = fields.Char('Auditor Reference', readonly=True)
    order_id = fields.Many2one('purchase.order', 'Purchase Order', readonly=True)
    service_start_date = fields.Date('Service Start Date', readonly=True)
    service_end_date = fields.Date('Service End Date', readonly=True)
    coordinator_id = fields.Many2one('res.users', 'Coordinator', readonly=True)
    products  = fields.Text(
        compute='_get_products', 
        string='Products',
        readonly=True,
    )
    all_day = fields.Boolean(
        string="All Day",
        default=True,
    )
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('dayoff', 'Day Off')
    ], 'Status', readonly=True)
    audit_status = fields.Many2one(
        string="Audit status",
        comodel_name='auditconfirmation.auditstate',
        readonly = True,
    )
    color = fields.Integer(string="color", compute="_get_color")
    customer_group_id = fields.Text(string="Group", readonly=True)
    promotor_id = fields.Text(string="Promotor", readonly=True)
    customer_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    combination = fields.Char(string='name', compute='_compute_fields_combination')
    shadow_id = fields.Many2one('res.partner', 'Shadow', readonly=True)
    assessment_id = fields.Many2one('res.partner', 'Assessment', readonly=True)
    state_id = fields.Many2one(comodel_name = "res.country.state", string='Audit State', readonly=True)
    city_id = fields.Many2one(comodel_name = "res.city", string='Audit City', readonly=True)

    """
    @api.depends('order_id')
    def _get_audit_state(self):
        for rec in self:
            if rec.order_id:
                domain = [('purchase_order_id','=',rec.order_id.id)]
                result = self.env['auditconfirmation.auditstate.history'].search(domain, order="create_date desc", limit=1)
                
                rec.audit_states = result.audit_state.id if result.audit_state else None
    """

    @api.depends('audit_status')
    def _get_color(self):
        for rec in self:
            if rec.audit_status.id > 0:
                rec.color = rec.audit_status.color
            else: 
                rec.color = 8


    @api.depends('customer_id', 'partner_id')
    def _compute_fields_combination(self):
        for rec in self:
            customer=''
            auditor=''
            shadow=''
            assessment=''
            listorganization = []
            organization = ''
            if rec.order_id.id > 0:
                if not rec.customer_id:
                    for line in rec.order_id.order_line:
                        if line.product_id and line.organization_id:
                            if line.organization_id.id not in listorganization:
                                listorganization.append(line.organization_id.id)
                                organization +=  line.organization_id.name if organization == '' else ', ' + line.organization_id.name
                
                customer = rec.customer_id.name if rec.customer_id else organization
                auditor = rec.partner_id.name if rec.partner_id else ''
                shadow = rec.shadow_id.name if rec.shadow_id else ''
                assessment = rec.assessment_id.name if rec.assessment_id else ''
            else:
                customer = _('Day Off')
                auditor = rec.partner_id.name if rec.partner_id else ''
                shadow = rec.partner_ref
            rec.combination = customer + ' - ' + auditor +' ' + shadow + ' ' + assessment

    @api.depends('order_id')
    def _get_products(self):
        
        for rec in self:
            listproduct = []
            listproductaux = []
            productname = ''
            for r in rec.order_id.order_line:
                for p in r.product_id:
                    if p.id and p.id not in listproductaux:
                        listproductaux.append(p.id)
                        listproduct.append({"id": p.id, "name": p.name, "qty": r.product_qty})
                    else:
                        for x in range(0,len(listproduct)):
                            if listproduct[x].get("id") == p.id:
                               listproduct[x] = {"id": p.id, "name": p.name, "qty": listproduct[x].get("qty") + r.product_qty}
                               break
            for prod in listproduct:
                productname = productname + '\n' + prod.get("name") + ' - ' + str(prod.get("qty"))
            
            rec.products = productname


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            row_number() over() as id,
            po.partner_id as partner_id,
            po.partner_ref as partner_ref,
            po.id as order_id,
            pl.service_start_date as service_start_date,
            pl.service_end_date as service_end_date,
            po.coordinator_id as coordinator_id,
            true as all_day,
            po.state as state,
            cg.name as customer_group_id,
            cpromotor.name as promotor_id,
            so.partner_id as customer_id,
            po.shadow_id as shadow_id
        """

        for field in fields.values():
            select_ += field

        from_ = """
                purchase_order_line pl 
                inner join purchase_order po on (po.id=pl.order_id) 
                inner join res_partner partner on po.partner_id = partner.id 
                left join sale_order so on so.id = po.sale_order_id 
                left join res_partner partnerso on partnerso.id = so.partner_id 
                left join customergroups_group cg on partnerso.cgg_group_id = cg.id 
                left join comisionpromotores_promotor cpromotor on partnerso.promotor_id = cpromotor.id 
                %s
        """ % from_clause

        groupby_ = """
            po.partner_id,
            po.partner_ref,
            po.id,
            pl.service_start_date,
            pl.service_end_date,
            po.coordinator_id,
            all_day,
            po.state, 
            cg.name, 
            cpromotor.name,
            so.partner_id,
            po.shadow_id %s
        """ % (groupby)

        executequery = """
            SELECT row_number() over() as id,
            a.partner_id,
            a.partner_ref,
            a.order_id,
            a.service_start_date,
            a.service_end_date,
            a.coordinator_id,
            a.all_day,
            a.state,
            a.audit_status, 
            a.customer_group_id, 
            a.promotor_id,
            a.customer_id,
            a.shadow_id,
            a.assessment_id,
            a.state_id,
            a.city_id
            FROM 
            (
            SELECT 
            po.partner_id as partner_id,
            po.partner_ref as partner_ref,
            po.id as order_id,
            pl.service_start_date as service_start_date,
            pl.service_end_date as service_end_date,
            po.coordinator_id as coordinator_id,
            true as all_day,
            po.state as state,
            po.ac_audit_status as audit_status,
            cg.name as customer_group_id,
            cpromotor.name as promotor_id,
            so.partner_id as customer_id,
            po.shadow_id as shadow_id,
            po.assessment_id as assessment_id,
            po.audit_state_id as state_id,
            po.audit_city_id as city_id
            from 
            purchase_order_line pl 
                inner join purchase_order po on (po.id=pl.order_id) 
                inner join res_partner partner on po.partner_id = partner.id 
                left join sale_order so on so.id = po.sale_order_id 
                left join res_partner partnerso on partnerso.id = so.partner_id 
                left join customergroups_group cg on partnerso.cgg_group_id = cg.id 
                left join comisionpromotores_promotor cpromotor on partnerso.promotor_id = cpromotor.id
            GROUP BY
            po.partner_id,
            po.partner_ref,
            po.id,
            pl.service_start_date,
            pl.service_end_date,
            po.coordinator_id,
            all_day,
            po.state, 
            cg.name,
            po.ac_audit_status, 
            cpromotor.name,
            so.partner_id,
            po.shadow_id,
            po.assessment_id,
            po.audit_state_id,
            po.audit_city_id
            UNION ALL 
            SELECT 
            ado.auditor_id as partner_id,
            ado.name as partner_ref,
            0 as order_id,
            ado.start_date as service_start_date,
            ado.end_date as service_end_date,
            0 as coordinator_id,
            true as all_day,
            'dayoff' as state,
            0 as audit_status,
            '' as customer_group_id,
            '' as promotor_id,
            0 as customer_id,
            0 as shadow_id,
            0 as assessment_id,
            0 as state_id,
            0 as city_id
            from 
            auditordaysoff_days as ado
             GROUP BY
            partner_id,
            partner_ref,
            order_id,
            service_start_date,
            service_end_date,
            coordinator_id,
            all_day,
            state,
            audit_status, 
            customer_group_id, 
            promotor_id,
            customer_id,
            shadow_id,
            assessment_id,
            state_id,
            city_id) as a
        """  
        #return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)
        return '%s (%s)' % (with_, executequery)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))


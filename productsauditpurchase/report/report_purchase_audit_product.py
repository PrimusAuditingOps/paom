# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Please note that these reports are not multi-currency !!!
#

import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv.expression import AND, expression


class ReportPurchaseAuditProduct(models.Model):
    _name = "productsauditpurchase.purchase.report.products"
    _description = "Purchase Report By Audit Products"
    _auto = True
    _order = 'date_order desc'

    date_order = fields.Datetime('Order Date', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], 'Status', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Vendor', readonly=True)
    date_approve = fields.Datetime('Confirmation Date', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Reference Unit of Measure', required=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    user_id = fields.Many2one('res.users', 'Purchase Representative', readonly=True)
    #delay = fields.Float('Days to Confirm', digits=(16, 2), readonly=True, group_operator='avg', help="Amount of time between purchase approval and order by date.")
    #delay_pass = fields.Float('Days to Receive', digits=(16, 2), readonly=True, group_operator='avg',help="Amount of time between date planned and order by date for each purchase order line.")
    avg_days_to_purchase = fields.Float(
        'Average Days to Purchase', digits=(16, 2), readonly=True, store=False,  # needs store=False to prevent showing up as a 'measure' option
        help="Amount of time between purchase approval and document creation date. Due to a hack needed to calculate this, \
              every record will show the same average value, therefore only use this as an aggregated value with group_operator=avg")
    #price_total = fields.Float('Total', readonly=True)
    #price_average = fields.Float('Average Cost', readonly=True, group_operator="avg")
    nbr_lines = fields.Integer('# of Lines', readonly=True)
    category_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', readonly=True)
    country_id = fields.Many2one('res.country', 'Partner Country', readonly=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Commercial Entity', readonly=True)
    #weight = fields.Float('Gross Weight', readonly=True)
    #volume = fields.Float('Volume', readonly=True)
    order_id = fields.Many2one('purchase.order', 'Order', readonly=True)
    #untaxed_total = fields.Float('Untaxed Total', readonly=True)
    qty_ordered = fields.Float('Qty Ordered', readonly=True)
    qty_received = fields.Float('Qty Received', readonly=True)
    qty_billed = fields.Float('Qty Billed', readonly=True)
    qty_to_be_billed = fields.Float('Qty to be Billed', readonly=True)

    pao_auditproduct_ids= fields.Many2one(
        'servicereferralagreement.auditproducts', 
        string='Audit Products', 
        readonly=True
        )
    shadow_id = fields.Many2one(
        string = "Shadow",
        comodel_name = 'res.partner',
        readonly = True,
    )
    assessment_id = fields.Many2one(
        string = "Assessment",
        comodel_name = 'res.partner',
        readonly = True,
    )
    ado_is_external_audit = fields.Boolean(
        string = "Is an external audit",
        readonly = True,
    )
    ac_audit_status = fields.Many2one(
        string = "Audit status",
        comodel_name = 'auditconfirmation.auditstate',
        readonly = True,
    )
    coordinator_id = fields.Many2one(
        string = "Coordinator",
        comodel_name = 'res.users',
        readonly = True,
    )
    audit_country_id = fields.Many2one(
        comodel_name = 'res.country', 
        string = 'Audit Country',
        readonly = True,
    )  
    audit_state_id = fields.Many2one(
        comodel_name = "res.country.state",
        string = 'Audit State',
        readonly = True,
    )
    audit_city_id = fields.Many2one(
        comodel_name = "res.city",
        string = 'Audit City',
        readonly = True,
    )
    
    organization_id = fields.Many2one(
        comodel_name = 'servicereferralagreement.organization', 
        string='Organization',
        readonly = True, 
    )
    registrynumber_id = fields.Many2one(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registry number',
        readonly = True,
    )
    service_start_date = fields.Date(
        string="Service start date",
        readonly = True,
    )
    service_end_date = fields.Date(
         string="Service end date",
         readonly = True,
    )

    pao_customer_id = fields.Many2one(
        'res.partner', 
        string='Invoice Customer', 
        readonly=True
    )

    pao_crm_team_id = fields.Many2one(
        'crm.team', 
        string='Sales Team', 
        readonly=True
    )

    @property
    def _table_query(self):
        ''' Report needs to be dynamic to take into account multi-company selected + multi-currency rates '''
        return '%s %s %s %s' % (self._select(), self._from(), self._where(), self._group_by())

    def _select(self):
        select_str = """
                SELECT
                    po.id as order_id,
                    min(l.id) as id,
                    po.date_order as date_order,
                    po.state,
                    po.date_approve,
                    po.dest_address_id,
                    po.partner_id as partner_id,
                    po.user_id as user_id,
                    po.company_id as company_id,
                    po.fiscal_position_id as fiscal_position_id,
                    l.product_id,
                    p.product_tmpl_id,
                    t.categ_id as category_id,
                    po.currency_id,
                    t.uom_id as product_uom,
                    count(*) as nbr_lines,
                    partner.country_id as country_id,
                    partner.commercial_partner_id as commercial_partner_id,
                    sum(l.product_qty / line_uom.factor * product_uom.factor) as qty_ordered,
                    sum(l.qty_received / line_uom.factor * product_uom.factor) as qty_received,
                    sum(l.qty_invoiced / line_uom.factor * product_uom.factor) as qty_billed,
                    case when t.purchase_method = 'purchase' 
                         then sum(l.product_qty / line_uom.factor * product_uom.factor) - sum(l.qty_invoiced / line_uom.factor * product_uom.factor)
                         else sum(l.qty_received / line_uom.factor * product_uom.factor) - sum(l.qty_invoiced / line_uom.factor * product_uom.factor)
                    end as qty_to_be_billed,
                    ap.servicereferralagreement_auditproducts_id as pao_auditproduct_ids,
                    po.shadow_id as shadow_id, 
                    po.assessment_id as assessment_id, 
                    po.ado_is_external_audit as ado_is_external_audit, 
                    po.ac_audit_status as ac_audit_status, 
                    po.coordinator_id as coordinator_id, 
                    po.audit_country_id as audit_country_id, 
                    po.audit_state_id as audit_state_id, 
                    po.audit_city_id as audit_city_id, 
                    l.organization_id as organization_id, 
                    l.registrynumber_id as registrynumber_id, 
                    l.service_start_date as service_start_date, 
                    l.service_end_date as service_end_date,
                    saleorder.partner_id as pao_customer_id, 
                    c.team_id as pao_crm_team_id
        """
        return select_str

    def _from(self):
        from_str = """
            FROM
            purchase_order_line l
                join purchase_order po on (l.order_id=po.id)
                join res_partner partner on po.partner_id = partner.id
                    left join product_product p on (l.product_id=p.id)
                        left join product_template t on (p.product_tmpl_id=t.id)
                left join uom_uom line_uom on (line_uom.id=l.product_uom)
                left join uom_uom product_uom on (product_uom.id=t.uom_id)
                left join {currency_table} ON currency_table.company_id = po.company_id
                left join sale_order so on (so.id=po.sale_order_id) 
                left join sale_order_line saleorderline on (saleorderline.order_id=so.id)
                left join sale_order_line_servicereferralagreement_auditproducts_rel ap on (ap.sale_order_line_id=saleorderline.id)
                left join sale_order saleorder on (saleorder.id=po.sale_order_id) 
                left join res_partner c on (c.id=saleorder.partner_id)
                left join crm_team st on (st.id=c.team_id)
        """.format(
            currency_table=self.env['res.currency']._get_query_currency_table(self.env.companies.ids, fields.Date.today())
        )

        return from_str

    def _where(self):
        return """
            WHERE
                l.display_type IS NULL
        """

    def _group_by(self):
        group_by_str = """
            GROUP BY
                po.company_id,
                po.user_id,
                po.partner_id,
                line_uom.factor,
                po.currency_id,
                l.price_unit,
                po.date_approve,
                l.date_planned,
                l.product_uom,
                po.dest_address_id,
                po.fiscal_position_id,
                l.product_id,
                p.product_tmpl_id,
                t.categ_id,
                po.date_order,
                po.state,
                line_uom.uom_type,
                line_uom.category_id,
                t.uom_id,
                t.purchase_method,
                line_uom.id,
                product_uom.factor,
                partner.country_id,
                partner.commercial_partner_id,
                po.id,
                currency_table.rate,
                ap.servicereferralagreement_auditproducts_id,
                po.shadow_id, 
                po.assessment_id, 
                po.ado_is_external_audit, 
                po.ac_audit_status, 
                po.coordinator_id, 
                po.audit_country_id, 
                po.audit_state_id, 
                po.audit_city_id, 
                l.organization_id, 
                l.registrynumber_id, 
                l.service_start_date, 
                l.service_end_date,
                saleorder.partner_id, 
                c.team_id
        """
        return group_by_str

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """ This is a hack to allow us to correctly calculate the average of PO specific date values since
            the normal report query result will duplicate PO values across its PO lines during joins and
            lead to incorrect aggregation values.
            Only the AVG operator is supported for avg_days_to_purchase.
        """
        avg_days_to_purchase = next((field for field in fields if re.search(r'\bavg_days_to_purchase\b', field)), False)

        if avg_days_to_purchase:
            fields.remove(avg_days_to_purchase)
            if any(field.split(':')[1].split('(')[0] != 'avg' for field in [avg_days_to_purchase] if field):
                raise UserError(_("Value: 'avg_days_to_purchase' should only be used to show an average. If you are seeing this message then it is being accessed incorrectly."))

        res = []
        if fields:
            res = super(ReportPurchaseAuditProduct, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        if not res and avg_days_to_purchase:
            res = [{}]

        if avg_days_to_purchase:
            self.check_access_rights('read')
            query = """ SELECT AVG(days_to_purchase.po_days_to_purchase)::decimal(16,2) AS avg_days_to_purchase
                          FROM (
                              SELECT extract(epoch from age(po.date_approve,po.create_date))/(24*60*60) AS po_days_to_purchase
                              FROM purchase_order po
                              WHERE po.id IN (
                                  SELECT "purchase_report"."order_id" FROM %s WHERE %s)
                              ) AS days_to_purchase
                    """

            subdomain = AND([domain, [('company_id', '=', self.env.company.id), ('date_approve', '!=', False)]])
            subtables, subwhere, subparams = expression(subdomain, self).query.get_sql()

            self.env.cr.execute(query % (subtables, subwhere), subparams)
            res[0].update({
                '__count': 1,
                avg_days_to_purchase.split(':')[0]: self.env.cr.fetchall()[0][0],
            })
        return res

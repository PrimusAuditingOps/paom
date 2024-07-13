from odoo import models, fields, tools, api

class SalesInvoicingReport(models.Model):

    _name="sales.invoicing.report"
    _description = "Sales invoicing Analysis Report"
    _auto = False
    _rec_name = 'date_order'
    _order = 'date_order desc'
    
    
    id = fields.Integer("ID", readonly=True)
    invoice_id = fields.Many2one('account.move', 'Invoice #', readonly=True)
    
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    
    name = fields.Char('Invoice Reference', readonly=True)
    invoice_date = fields.Date('Invoice Date', readonly=True)
    product_id = fields.Many2one('product.product', 'Product Variant', readonly=True)
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)
    
    usd_total = fields.Monetary(string='USD Total', currency_field='currency_id', readonly=True)
    usd_untaxed_total =  fields.Monetary(string='USD Untaxed Total', currency_field='currency_id', readonly=True)
    mxn_total = fields.Monetary(string='MXN Total', currency_field='currency_id', readonly=True)
    mxn_untaxed_total = fields.Monetary(string='MXN Untaxed Total', currency_field='currency_id', readonly=True)
    
    product_tmpl_id = fields.Many2one('product.template', 'Product', readonly=True)
    categ_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    nbr = fields.Integer('# of Lines', readonly=True)
    team_id = fields.Many2one('crm.team', 'Sales Team', readonly=True)
    pao_old_sales_team_id = fields.Many2one('crm.team', 'Old Sales Team', readonly=True)
    country_id = fields.Many2one('res.country', 'Customer Country', readonly=True)
    industry_id = fields.Many2one('res.partner.industry', 'Customer Industry', readonly=True)
    commercial_partner_id = fields.Many2one('res.partner', 'Customer Entity', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)
    discount = fields.Float('Discount %', readonly=True)
    campaign_id = fields.Many2one('utm.campaign', 'Campaign')
    medium_id = fields.Many2one('utm.medium', 'Medium')
    source_id = fields.Many2one('utm.source', 'Source')
    shipper_id = fields.Many2one('pao.shippers', 'Shipper')
    office_id = fields.Many2one('pao.offices', 'Office')
    
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string="Invoice Status", readonly=True)
    
    date_order = fields.Datetime('Order Date', readonly=True)
    
    group_id = fields.Many2one('customergroups.group', 'Group')
    promotor_id = fields.Many2one('comisionpromotores.promotor', 'Promotor')
    invoice_origin = fields.Char('Invoice Source Document', readonly=True)
    
    order_start_date = fields.Date('Order Start Date', readonly=True)
    order_end_date = fields.Date('Order End Date', readonly=True)
    
    quantity = fields.Float('Invoiced Quantity', readonly=True)
    
    def _select(self, fields=None):
        if not fields:
            fields = {}
        select_ = """
            l.id as id,
            a.id as invoice_id,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.price_total / CASE COALESCE(r.rate, 0) WHEN 0 THEN 1.0 ELSE r.rate END) ELSE 0 END * CASE WHEN a.move_type = 'out_refund' THEN -1 ELSE 1 END as mxn_total,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.price_subtotal / CASE COALESCE(r.rate, 0) WHEN 0 THEN 1.0 ELSE r.rate END) ELSE 0 END * CASE WHEN a.move_type = 'out_refund' THEN -1 ELSE 1 END as mxn_untaxed_total,
            
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.price_total / CASE COALESCE(r.rate, 0) WHEN 0 THEN 1.0 ELSE r.rate END) * CASE WHEN prcr.rate IS NOT NULL THEN prcr.rate ELSE 1 END ELSE 0 END * CASE WHEN a.move_type = 'out_refund' THEN -1 ELSE 1 END as usd_total,
            CASE WHEN l.product_id IS NOT NULL THEN sum(l.price_subtotal / CASE COALESCE(r.rate, 0) WHEN 0 THEN 1.0 ELSE r.rate END) * CASE WHEN prcr.rate IS NOT NULL THEN prcr.rate ELSE 1 END ELSE 0 END * CASE WHEN a.move_type = 'out_refund' THEN -1 ELSE 1 END as usd_untaxed_total,
            
            l.product_id as product_id,
            t.uom_id as product_uom,
            
            count(*) as nbr,
            a.name as name,
            a.invoice_date as invoice_date,
            a.state as state,
            a.partner_id as partner_id,
            a.invoice_user_id as user_id,
            a.company_id as company_id,
            a.campaign_id as campaign_id,
            a.medium_id as medium_id,
            a.source_id as source_id,
            t.categ_id as categ_id,
            a.team_id as team_id,
            partner.pao_old_sales_team_id as pao_old_sales_team_id,
            p.product_tmpl_id,
            partner.country_id as country_id,
            partner.industry_id as industry_id,
            partner.commercial_partner_id as commercial_partner_id,
            l.discount as discount,
            partner.pao_shipper_id as shipper_id,
            partner.pao_office_id as office_id,
            so.invoice_status as invoice_status,
            so.date_order as date_order,
            partner.cgg_group_id as group_id,
            partner.promotor_id as promotor_id,
            a.invoice_origin,
            sl.service_start_date as order_start_date,
            sl.service_end_date as order_end_date,
            l.quantity * CASE WHEN a.move_type = 'out_refund' THEN -1 ELSE 1 END as quantity,
            c.id as currency_id
            
        """

        for field in fields.values():
            select_ += field
        return select_

    def _from(self, from_clause=''):
        from_ = """
                    account_move_line l
                      inner join account_move a on (l.move_id = a.id)
                        left join sale_order_line_invoice_rel rel on (rel.invoice_line_id = l.id)
                        left join sale_order_line sl on (sl.id = rel.order_line_id)
                        left join sale_order so on (so.id = sl.order_id)
                        join res_partner partner on a.partner_id = partner.id
                        inner join product_product p on (l.product_id = p.id)
                            left join product_template t on (p.product_tmpl_id = t.id)
                    inner join res_currency c on (c.id = l.currency_id)
                        left join res_currency_rate r on (c.id = r.currency_id) and r.name = a.invoice_date
                        left join res_currency_rate prcr on (prcr.name::date = a.invoice_date::date and prcr.currency_id = 2)
                %s
        """ % from_clause
        return from_

    def _group_by(self, groupby=''):
        groupby_ = """
            a.id,
            so.invoice_status,
            so.date_order,
            l.quantity,
            prcr.rate,
            partner.cgg_group_id,
            partner.promotor_id,
            sl.service_start_date,
            sl.service_end_date,
            l.product_id,
            t.uom_id,
            t.categ_id,
            a.name,
            a.invoice_date,
            a.partner_id,
            a.invoice_user_id,
            a.state,
            a.company_id,
            a.campaign_id,
            a.medium_id,
            a.source_id,
            partner.pao_shipper_id,
            partner.pao_office_id,
            a.team_id,
            partner.pao_old_sales_team_id,
            p.product_tmpl_id,
            partner.country_id,
            partner.industry_id,
            partner.commercial_partner_id,
            l.discount,
            c.id,
            l.id %s
        """ % (groupby)
        return groupby_

    def _select_additional_fields(self, fields):
        """Hook to return additional fields SQL specification for select part of the table query.

        :param dict fields: additional fields info provided by _query overrides (old API), prefer overriding
            _select_additional_fields instead.
        :returns: mapping field -> SQL computation of the field
        :rtype: dict
        """
        return fields

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        invoice_report_fields = self._select_additional_fields(fields)
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        return '%s (SELECT %s FROM %s WHERE a.state = \'posted\' AND a.move_type IN (\'out_invoice\', \'out_refund\') GROUP BY %s)' % \
                (with_, self._select(invoice_report_fields), self._from(from_clause), self._group_by(groupby))

    def init(self):
        # self._table = 'accounting_sales_report'
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query())) 
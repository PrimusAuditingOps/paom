from odoo import models, fields, tools, api

class InvoiceReport(models.Model):

    _name="invoice.report"
    _auto = False
    _rec_name = 'invoice_number'
    _order = 'invoice_number desc'
    _description='Invoice Report'
    
    # Extra required fields #
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    currency_rate = fields.Char('Currency Rate', compute='_get_rate', readonly=True)
    invoice_id = fields.Many2one('account.move', 'Invoice', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    
    id = fields.Integer("ID", readonly=True)
    invoice_number = fields.Char('Invoice number', readonly=True)
    client_id = fields.Integer('Client ID', readonly=True)
    group = fields.Many2one('customergroups.group', 'Group', readonly=True)
    promoter = fields.Many2one('comisionpromotores.promotor', 'Promoter', readonly=True)
    
    # Details of operations #        
    product = fields.Many2one('product.product','Product', readonly=True)
    product_category = fields.Many2one('product.category','Product Category', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    price_subtotal = fields.Monetary('Original Currency Subtotal', currency_field='currency_id', readonly=True)
    usd_subtotal = fields.Monetary(string='USD Subtotal', compute='_get_usd_price', currency_field='currency_id', readonly=True)
    mxn_subtotal = fields.Monetary(string='MXN Subtotal', compute='_get_mxn_price', currency_field='currency_id', readonly=True)
    registry_number_id = fields.Many2one('servicereferralagreement.registrynumber', 'Registry Number', readonly=True, compute='_get_sale_order')
    organization_id = fields.Many2one('servicereferralagreement.organization', 'Organization', readonly=True, compute='_get_sale_order')
    ship_date = fields.Date('Ship Date', readonly=True, compute='_get_sale_order')
    audit_date = fields.Date('Audit Date', readonly=True, compute='_get_sale_order')
    end_date = fields.Date('End Date', readonly=True, compute='_get_sale_order')
    sale_order_id = fields.Many2one('sale.order', 'Sale Order', readonly=True, compute='_get_sale_order')
    #########################

    invoice_partner_name = fields.Char('Invoice partner name', readonly=True)
    fiscal_folio = fields.Char(related='invoice_id.l10n_mx_edi_cfdi_uuid', readonly=True)
    invoice_date = fields.Date('Invoice Date', readonly=True)
    invoice_date_due = fields.Date('Invoice Date Due', readonly=True)
    invoice_salesperson = fields.Many2one('res.users','Invoice salesperson', readonly=True)
    sales_team = fields.Many2one('crm.team','Sales Team', readonly=True)
    category_id = fields.Many2one('res.partner.category', 'Category', readonly=True)
    scheme_id = fields.Many2one('paa.assignment.auditor.scheme', 'Scheme', readonly=True)
    origin = fields.Char('Origin', readonly=True)
    quotation_salesperson = fields.Many2one('res.users','Quotation salesperson', readonly=True)
    # amount_untaxed = fields.Monetary('Amount untaxed signed', currency_field='currency_id', readonly=True)
    # amount_total = fields.Monetary('Amount total signed', currency_field='currency_id', readonly=True)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', readonly=True)
    payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy')],
        string="Payment Status", readonly=True)
    # usd_net = fields.Monetary(related='invoice_id.ad_usd_neto', string="USD Net", readonly=True)
    # usd_total = fields.Monetary(related='invoice_id.ad_usd_total', string="USD Total", readonly=True)
    # mxn_net = fields.Monetary(related='invoice_id.ad_mxn_neto', string="MXN Net", readonly=True)
    # mxn_total = fields.Monetary(related='invoice_id.ad_mxn_total', string="MXN Total", readonly=True)
    
    def _get_sale_order(self):
        for record in self:
            
            record.sale_order_id = None
            record.registry_number_id = None
            record.organization_id = None
            record.ship_date = None
            record.end_date = None
            record.audit_date = None
            
            invoice = self.env['account.move'].browse(record.invoice_id.id)
            if invoice:
                # Get the related sale orders from the invoice
                sale_orders = self.env['sale.order'].search([('invoice_ids', 'in', invoice.ids)])
                if sale_orders:
                    first_sale_order = sale_orders[0]
                    
                    record.sale_order_id = first_sale_order.id
                    # Fetch the first sale order line
                    if first_sale_order.order_line:
                        first_line = first_sale_order.order_line[0]
                        
                        if first_line.registrynumber_id:
                            record.registry_number_id = first_line.registrynumber_id.id
                            record.organization_id = first_line.organization_id.id
                        record.ship_date = first_sale_order.date_order
                        record.audit_date = first_line.service_start_date
                        record.end_date = first_line.service_end_date
    
    def _get_rate(self):
        for rec in self:
            rec.currency_rate = -1
            dateinvoice = rec.invoice_date
            if dateinvoice:
                if rec.currency_id.name == 'USD':
                    currencyrate = rec.invoice_id._get_rates_currency(dateinvoice)
                    rec.currency_rate = round((1 / currencyrate.get('USD')),6)
                elif rec.currency_id.name == 'MXN':
                    rec.currency_rate = 1
    
    def _get_mxn_price(self):
        for rec in self:
            rec.mxn_subtotal = 0.00
            dateinvoice = rec.invoice_date
            if dateinvoice:
                if rec.currency_id.name == 'USD':
                    currencyrate = rec.invoice_id._get_rates_currency(dateinvoice)
                    if currencyrate:
                        rec.mxn_subtotal = round((rec.price_subtotal / currencyrate.get('USD')),2)
                elif rec.currency_id.name == 'MXN':
                    rec.mxn_subtotal = rec.price_subtotal
                
    def _get_usd_price(self):
        for rec in self:
            rec.usd_subtotal = 0.00
            dateinvoice = rec.invoice_date
            if dateinvoice:
                if rec.currency_id.name == 'MXN':
                    currencyrate = rec.invoice_id._get_rates_currency(dateinvoice)
                    if currencyrate:
                        rec.usd_subtotal = round((rec.price_subtotal * currencyrate.get('USD')),2)
                elif rec.currency_id.name == "USD":
                    rec.usd_subtotal = rec.price_subtotal
        
    def _select(self, fields=None):
        if not fields:
            fields = {}
        select_ = """
            l.id as id,
            a.name as invoice_number,
            a.company_id,
            r.id as client_id,
            r.cgg_group_id as group,
            r.promotor_id as promoter,
            
            --details of operations:
            l.product_id as product,
            pc.id as product_category,
            l.quantity as quantity,
            l.price_subtotal as price_subtotal,
            
            a.invoice_partner_display_name as invoice_partner_name,
            a.invoice_date as invoice_date,
            a.invoice_date_due as invoice_date_due,
            -- a.amount_untaxed as amount_untaxed,
            u.id as invoice_salesperson,
            t.id as sales_team,
            ct.id as category_id,
            ps.id as scheme_id,
            a.invoice_origin as origin,
            us.id as quotation_salesperson,
            -- a.amount_total as amount_total,
            a.state,
            a.payment_state,
            
            --extra required fields:
            c.id as currency_id,
            --cr.rate as currency_rate,
            a.id as invoice_id
        """

        for field in fields.values():
            select_ += field
        return select_

    def _from(self, from_clause=''):
        from_ = """
                	account_move_line l
                        INNER JOIN account_move a ON a.id = l.move_id
                    
                        INNER JOIN res_currency c ON a.currency_id = c.id
                        --JOIN res_currency_rate cr ON c.id = cr.currency_id AND cr.name = a.invoice_date
                        LEFT JOIN crm_team t ON t.id = a.team_id
                        LEFT JOIN res_users u ON u.id = a.invoice_user_id
                        
                        INNER JOIN sale_order s ON s.name = a.invoice_origin
                        LEFT JOIN res_users us ON us.id = s.user_id
                        
                        INNER JOIN res_partner r ON a.partner_id = r.id
                        LEFT JOIN res_partner_res_partner_category_rel rc ON rc.partner_id = r.id
                        LEFT JOIN res_partner_category ct ON ct.id = rc.category_id
                        
                        INNER JOIN product_product p ON p.id = l.product_id
                        LEFT JOIN product_template pt ON pt.id = p.product_tmpl_id
                        LEFT JOIN product_category pc ON pc.id = pt.categ_id
                        LEFT JOIN paa_assignment_auditor_scheme ps ON ps.id = pc.paa_schem_id
                %s
        """ % from_clause
        return from_

    def _group_by(self, groupby=''):
        groupby_ = """
            l.id
            ,a.name
            ,r.id
            ,a.company_id
            ,r.cgg_group_id
            ,r.promotor_id
            ,l.product_id
            ,pc.id
            ,a.invoice_partner_display_name
            ,a.invoice_date
            ,a.invoice_date_due
            ,a.amount_untaxed
            ,u.id
            ,t.id
            ,ct.id
            ,ps.id
            ,a.invoice_origin
            ,us.id
            ,a.amount_total
            ,a.state
            ,a.payment_state
            ,c.id
            --,cr.rate
            ,a.id
            %s
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
        return '%s (SELECT %s FROM %s WHERE a.move_type=\'out_invoice\' GROUP BY %s)' % \
                (with_, self._select(invoice_report_fields), self._from(from_clause), self._group_by(groupby))

    def init(self):
        # self._table = 'invoice_report'
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query())) 
    
    ####### FINAL QUERY #######
    #
    # SELECT
    #   l.id as id,
    # a.name as invoice_number,
    # r.cgg_group_id as group,
    # r.promotor_id as promoter,
    #             
    # --details of operations:
    # l.product_id as product,
    # l.quantity as quantity,
    # l.price_subtotal as price_subtotal,
    #             
    # a.invoice_partner_display_name as invoice_partner_name,
    # a.invoice_date as invoice_date,
    # a.invoice_date_due as invoice_date_due,
    # a.amount_untaxed as amount_untaxed,
    # u.id as salesperson,
    # t.id as sales_team,
    # ct.id as category_id,
    # ps.id as scheme_id,
    # a.invoice_origin as origin,
    # a.amount_total as amount_total,
    # a.state,
    # a.payment_state,
    #             
    # --extra required fields:
    # c.id as currency_id,
    # a.id as invoice_id
    # FROM 
    #   account_move_line l
    #       INNER JOIN account_move a ON a.id = l.move_id
    #       INNER JOIN res_currency c ON a.currency_id = c.id
    #       LEFT JOIN crm_team t ON t.id = a.team_id
    #       LEFT JOIN res_users u ON u.id = a.invoice_user_id
    #       
    #       INNER JOIN res_partner r ON a.partner_id = r.id
    #       LEFT JOIN res_partner_res_partner_category_rel rc ON rc.partner_id = r.id
    #       LEFT JOIN res_partner_category ct ON ct.id = rc.category_id
    #       
    #       INNER JOIN product_product p ON p.id = l.product_id
    #       LEFT JOIN product_template pt ON pt.id = p.product_tmpl_id
    #       LEFT JOIN product_category pc ON pc.id = pt.categ_id
    #       LEFT JOIN paa_assignment_auditor_scheme ps ON ps.id = pc.paa_schem_id
    # WHERE 
    #   a.move_type='out_invoice'
    # GROUP BY
    #   l.id
    #   ,a.name
    #   ,r.cgg_group_id
    #   ,r.promotor_id
    #   ,l.product_id
    #   ,a.invoice_partner_display_name
    #   ,a.invoice_date
    #   ,a.invoice_date_due
    #   ,a.amount_untaxed
    #   ,u.id
    #   ,t.id
    #   ,ct.id
    #   ,ps.id
    #   ,a.invoice_origin
    #   ,a.amount_total
    #   ,a.state
    #   ,a.payment_state
    #   ,c.id
    #   ,a.id
    #
    ###########################

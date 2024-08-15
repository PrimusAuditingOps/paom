from odoo import models, fields, tools, api

class SaleOrderCommissionsReport(models.Model):

    _name="sale.order.commissions.report"
    _auto = False
    _rec_name = 'order'
    _order = 'order desc'
    
    id = fields.Integer("ID", readonly=True)
    
    order = fields.Many2one('sale.order', 'Order')
    # invoice = fields.Many2one('account.move', 'Invoice')
    # invoice_status = fields.Char('Invoice Status')
    specialist = fields.Many2one('res.users', string='Sales Specialist', readonly=True)
    details = fields.Char('Details of operation', compute="_get_details", readonly=True)
    source = fields.Many2one('commissions.source', string="Source")
    date_order = fields.Date('Qutation Date', readonly=True)
    commission_percentage = fields.Float(string="Commission Percentage (%)",digits=(3, 2), readonly=True)
    amount = fields.Monetary(string="Payment Amount", compute="_get_amount", readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    company_id = fields.Many2one(
        'res.company', 'Company', copy=False,
        required=True, index=True)
    
    def _get_amount(self):
        for rec in self:
            rec.amount = -1
            total_commissionable = 0.0
            if rec.order:
                for line in rec.order.order_line:
                    if line.product_template_id.can_be_commissionable:
                        total_commissionable += line.price_subtotal
                    
                rec.amount = total_commissionable * (rec.commission_percentage/100)

    def _get_details(self):
        for rec in self:
            details = []
            rec.details = ''
            if rec.order:
                for line in rec.order.order_line:
                    if line.product_template_id.can_be_commissionable:
                        order_detail =  str(line.product_uom_qty) + ' ' + line.name
                        details.append(order_detail)
                    
                rec.details = ", ".join(details)
                
    def _select(self, fields=None):
        if not fields:
            fields = {}
        select_ = """
            c.id as id,
            s.id as order,
            s.company_id as company_id,
            s.date_order,
            c.user_id as specialist,
            c.source_id as source,
            c.commission_percentage as commission_percentage,
            s.currency_id as currency_id
        """

        for field in fields.values():
            select_ += field
        return select_

    def _from(self, from_clause=''):
        from_ = """
                pao_sale_order_commissions c
                    INNER JOIN sale_order s ON s.id = c.sale_order_id

                %s
        """ % from_clause
        return from_

    def _group_by(self, groupby=''):
        groupby_ = """
            c.id
            ,s.id
            ,s.date_order
            ,c.user_id
            ,c.source_id
            ,c.commission_percentage
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
        report_fields = self._select_additional_fields(fields)
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        return '%s (SELECT %s FROM %s GROUP BY %s)' % \
                (with_, self._select(report_fields), self._from(from_clause), self._group_by(groupby))


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query())) 

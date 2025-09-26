from odoo import models, fields, tools, api, _
from logging import getLogger
import re
from datetime import datetime

_logger = getLogger(__name__)

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
    date_order = fields.Date('Quotation Date', readonly=True)
    commission_percentage = fields.Float(string="Commission Rate (%)",digits=(3, 2), readonly=True)
    amount = fields.Monetary(string="Comission Amount", compute="_get_amounts", readonly=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', copy=False,required=True, index=True)
    
    
    
    scheme = fields.Char('Scheme', compute="_get_details", readonly=True)
    organization = fields.Char('Organization', compute="_get_details", readonly=True)
    registration_number = fields.Char('Registration Number', compute="_get_details", readonly=True)
    current_customer = fields.Char('Is Current Customer', compute="_get_customer_information", readonly=True)
    operation_type = fields.Char('Type of Operation', compute="_get_details", readonly=True)
    quantity = fields.Float('Quantity', compute="_get_details", readonly=True)
    # audit_date = fields.Date('Audit Date', compute="_get_details", readonly=True)
    audit_date = fields.Date('Audit Date', readonly=True)
    audit_amount = fields.Monetary('Audit Amount', compute="_get_amounts", readonly=True, currency_field='currency_id')
    opportunity_notes = fields.Html('Opportunity Notes', compute="_get_customer_information", readonly=True)
    invoice_paid = fields.Selection(
        selection=[("yes", "Yes"), ("no", "No")],
        string="Invoice Paid",
        compute="_compute_invoice_status",
        readonly=True
    )
    invoice_paid_date = fields.Date('Invoice Paid Date', compute="_compute_invoice_status", readonly=True)
    comission_paid = fields.Selection(
        selection=[("yes", "Yes"), ("no", "No")],
        string="Comission Paid",
        compute="_get_log_notes",
        readonly=True
    )
    comission_paid_date = fields.Date('Comission Paid Date',  compute="_get_log_notes", readonly=True)
    
    def _get_log_notes(self):
        for rec in self:
            rec.comission_paid = 'no'
            rec.comission_paid_date = None
            if rec.order:
                log_note = self.env['mail.message'].search([
                    ('model', '=', 'sale.order'),
                    ('res_id', '=', rec.order.id),
                    ('body', 'ilike', '#comissionpaid%')
                ], limit=1, order="id DESC") 

                company_country_code = rec.order.company_id.country_id.code
                if log_note:
                    rec.comission_paid = 'yes'
                    cleaned_body = re.sub(r'#comissionpaid', '', log_note.body, flags=re.IGNORECASE).strip()
                    
                    extracted_date = rec.extract_valid_date(cleaned_body, company_country_code)
                    rec.comission_paid_date = extracted_date or log_note.date.date()
                    
    def extract_valid_date(self, text, country_code):
        """Extracts and validates a date from text based on the country format."""
        date_pattern = r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b'  # Matches MM/DD/YYYY or DD/MM/YYYY
        matches = re.findall(date_pattern, text)

        if not matches:
            return None  # No date found

        # Determine the correct date format
        date_format = '%m/%d/%Y' if country_code == 'US' else '%d/%m/%Y'

        for match in matches:
            try:
                extracted_date = "/".join(match)  # Convert tuple to string
                return datetime.strptime(extracted_date, date_format).date()  # Convert to date object
            except ValueError:
                continue  # Skip invalid formats

        return None  # No valid date found
    
    def _get_customer_information(self):
        for rec in self:
            rec.opportunity_notes = ''
            if rec.order:
                customer_company = rec.order.partner_id if rec.order.partner_id.is_company else rec.order.partner_id.commercial_partner_id
                rec.current_customer = dict(customer_company._fields['pao_current_customer'].selection).get(customer_company.pao_current_customer, '')
                
                rec.opportunity_notes = rec.order.opportunity_id.description if rec.order.opportunity_id else ''
    
    @api.depends('order.invoice_ids.state', 'order.invoice_ids.payment_state', 'order.invoice_ids.line_ids.payment_id.date')
    def _compute_invoice_status(self):
        for rec in self:
            invoices = rec.order.invoice_ids.filtered(lambda inv: inv.state == 'posted')
            paid_invoices = invoices.filtered(lambda inv: inv.amount_residual <= 0)
            rec.invoice_paid = 'yes' if bool(paid_invoices) else 'no'
            
            rec.invoice_paid_date = None
            if paid_invoices:
                all_payments = self.env['account.payment'].search([('state', '=', 'posted')])

                payments = all_payments.filtered(lambda p: any(inv.id in p.reconciled_invoice_ids.ids for inv in paid_invoices))

                payment_dates = payments.mapped('date')
                rec.invoice_paid_date = max(payment_dates) if payment_dates else None
            
    def _get_amounts(self):
        for rec in self:
            rec.amount = -1
            rec.audit_amount = -1
            total_commissionable = 0.0
            if rec.order:
                for line in rec.order.order_line:
                    product = line.product_template_id
                    if product.can_be_commissionable and not product.is_travel_expenses:
                        total_commissionable += line.price_subtotal
                    
                rec.audit_amount = total_commissionable
                rec.amount = total_commissionable * (rec.commission_percentage/100)

    def _get_details(self):
        for rec in self:
            schemes = []
            organizations = []
            registration_numbers = []
            operation_types = []
            details = []
            
            rec.scheme = ''
            rec.organization = ''
            rec.registration_number = ''
            rec.details = ''
            rec.operation_type = ''
            rec.quantity = 0
            
            if rec.order:
                for line in rec.order.order_line:
                    product = line.product_template_id
                    if product.can_be_commissionable and not product.is_travel_expenses:
                        scheme = line.registrynumber_id.scheme_id.name if line.registrynumber_id and line.registrynumber_id.scheme_id else ''
                        organization = line.organization_id.name if line.organization_id else ''
                        registration_number = line.registrynumber_id.name if line.registrynumber_id else ''
                        order_detail =  str(line.product_uom_qty) + ' ' + line.name
                        rec.quantity += line.product_uom_qty
                        
                        schemes.append(scheme)
                        organizations.append(organization)
                        registration_numbers.append(registration_number)
                        operation_types.append(line.product_template_id.name)
                        details.append(order_detail)
                
                # rec.audit_date = rec.order.audit_date
                rec.scheme = ", ".join(list(set(schemes) - {''}))
                rec.organization = ", ".join(list(set(organizations) - {''}))
                rec.registration_number = ", ".join(list(set(registration_numbers) - {''}))
                rec.operation_type = ", ".join(list(set(operation_types) - {''}))
                rec.details = ", ".join(details)
                
    def _select(self, fields=None):
        if not fields:
            fields = {}
        select_ = """
            c.id as id,
            s.id as order,
            s.company_id as company_id,
            s.date_order,
            s.audit_date,
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
            ,s.audit_date
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

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import logging
_logger = logging.getLogger(__name__)


class ExpenseSheetInherit(models.Model):
    _inherit = 'hr.expense.sheet'
    
    purchase_order = fields.Many2one('purchase.order', string='Purchase Order')
    partner_id = fields.Many2one('res.partner', string='Contact')
    expense_scheme_id = fields.Many2one('expense.scheme', string='Scheme', default=None)
    country_code = fields.Char(related='company_id.country_code', string='Country Code')
    from_external_auditor = fields.Boolean(default=False)
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=False,  # This line disables the required constraint
        readonly=False,
        check_company=True,
        tracking=True,
    )
    
    has_receipts = fields.Boolean(
        compute='_compute_has_receipts',
        string='Has Receipts',
    )
    
    state_sequence = fields.Integer(
        compute='_compute_state_sequence',
        store=True
    )
    
    @api.depends('state')
    def _compute_state_sequence(self):
        order_map = {
            'draft': 1,
            'submit': 2,
            'approve': 3,
            'cancel': 4,
            'post': 5,
            'done': 6,
        }

        for record in self:
            record.state_sequence = order_map.get(record.state, 999)

    def _compute_has_receipts(self):
        attachment_model = self.env['ir.attachment'].sudo()
        for sheet in self:
            # Get all expense IDs in this sheet
            expense_ids = sheet.expense_line_ids.ids
            if not expense_ids:
                sheet.has_receipts = False
                continue
            # Check if any expense in the sheet has attachments
            sheet.has_receipts = attachment_model.search_count([
                ('res_model', '=', 'hr.expense'),
                ('res_id', 'in', expense_ids),
            ]) > 0
    
    def action_sheet_move_create(self):
        
        if not self.partner_id and not self.employee_id:
            raise ValidationError(_("You must define a Contact or Employee."))
        
        if self.partner_id and self.partner_id.ado_is_auditor and not self.partner_id.st_supplier_taxes_id:
            raise ValidationError(_("The Contact must have the supplier taxes defined."))
        
        result = super(ExpenseSheetInherit, self).action_sheet_move_create()
        
        if self.country_code == 'MX':
            for move in self.account_move_ids:
                for line in move.line_ids:
                    line.partner_id = line.expense_id.partner_id
            
        return result
    
    @api.model 
    def write(self, values):
        result = super(ExpenseSheetInherit, self).write(values)
        
        for record in self:
            if record.expense_line_ids and record.expense_scheme_id:
                for expense in record.expense_line_ids:
                    expense.sudo().account_id = record.expense_scheme_id.property_account_expense_id.id
            
        return result
    
    @api.model
    def _prepare_bills_vals(self):
        
        bills_vals = super(ExpenseSheetInherit, self)._prepare_bills_vals()
        
        if self.country_code == 'MX':
            partner_id = self.employee_id.sudo().work_contact_id.id if self.employee_id else self.partner_id.id
            # partner_id = self.partner_id.id
            bills_vals.update({'partner_id': partner_id})
        
        return bills_vals
    
    # @api.constrains('partner_id')
    # def _check_scheme(self):
    #     for record in self:
    #         if record.partner_id.ado_is_auditor and not record.expense_scheme_id:
    #             raise ValidationError(_("You must define a Scheme."))

class ExpenseInherit(models.Model):
    _inherit = "hr.expense"
    
    partner_id = fields.Many2one('res.partner', string='Contact', required=True, domain=[('ado_is_auditor', '=', False)])
    
    country_code = fields.Char(related='company_id.country_code', string='Country Code')
    
    from_external_auditor = fields.Boolean(default=False)

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=None,
        required=False,  # This line disables the required constraint
        readonly=False,
        check_company=True,
        domain=[('filter_for_expense', '=', True)],
        tracking=True,
    )
    
    uploaded_by_statement = fields.Boolean(default=False)
    
    is_complete = fields.Boolean(compute="_compute_is_complete", store=True)
    
    has_receipts = fields.Boolean(
        compute='_compute_has_receipts',
        string='Has Receipts',
    )
    
    state_sequence = fields.Integer(
        compute='_compute_state_sequence',
        store=True
    )
    
    end_date  = fields.Date(string='End Date', required=False)
    
    @api.depends('state')
    def _compute_state_sequence(self):
        order_map = {
            'draft': 1,
            'reported': 2,
            'submitted': 3,
            'refused': 4,
            'approved': 5,
            'done': 6,
        }

        for record in self:
            record.state_sequence = order_map.get(record.state, 999)

    def _compute_has_receipts(self):
        for expense in self:
            expense.has_receipts = self.env['ir.attachment'].sudo().search_count([
                ('res_model', '=', 'hr.expense'),
                ('res_id', '=', expense.id),
            ]) > 0
    
    @api.depends('name', 'product_id', 'date', 'nb_attachment')
    def _compute_is_complete(self):
        
        for record in self:
            
            if record.state != 'draft':
                record.is_complete = True
            else:
                required_fields_filled = all([
                    record.name,
                    record.product_id,
                    record.date,
                ])

                needs_attachment = (
                    record.partner_id.ado_is_auditor and
                    not record.partner_id.is_an_in_house_auditor and
                    record.product_id.display_name == "Auditor Travel: Meal"
                )

                record.is_complete = required_fields_filled and (
                    record.nb_attachment > 0 if needs_attachment else True
                )
    
    @api.model
    def _prepare_move_lines_vals(self):
        
        vals = super(ExpenseInherit, self)._prepare_move_lines_vals()
        
        if self.country_code == 'MX':
            expense_name = self.name.split('\n')[0][:64]
            vals.update({'name': f'{self.employee_id.name if self.employee_id else self.partner_id.name}: {expense_name}',})
        
        return vals
    
    @api.model
    def _prepare_payments_vals(self):
        
        vals = super(ExpenseInherit, self)._prepare_payments_vals()
        sheet = self.sheet_id
        vals['date'] = sheet.accounting_date or max(sheet.expense_line_ids.filtered(lambda exp: exp.date).mapped('date'), default=fields.Date.context_today(sheet))
        
        _logger.warning("Preparing payment vals for expense %s with context: %s", self.id, self.env.context)
        if self.total_amount_currency < 0:
            _logger.warning("Expense %s has negative amount, adjusting payment vals accordingly.", self.id)
            vals.update({
                'amount': abs(vals['amount']),
                'payment_type': 'inbound',
            })
                    
        return vals
    
    @api.model
    def write(self, values):
        show_warning = False
        for record in self:
            
            if 'sheet_id' in values:
                required_fields = ['product_id', 'date']
                missing_fields = []
            
                # Check which of the required fields are missing in the current record
                for field in required_fields:
                    if not values.get(field) and not getattr(record, field):
                        missing_fields.append(field)
                
                if missing_fields:
                    values['sheet_id'] = None
                    show_warning = True
                    
            result = super(ExpenseInherit, self).write(values)
            
            if ('state' in values and values['state'] == 'reported') or ('sheet_id' in values and values['sheet_id']):
                activities = self.env['mail.activity'].search([
                        ('res_model', '=', 'hr.expense'),
                        ('res_id', 'in', self.ids),
                        ('user_id', '=', self.env.user.id)
                    ])
                activities.action_done()
            
            if not record.employee_id and record.partner_id and not record.partner_id.ado_is_auditor:
                raise ValidationError(_("You must define an Employee."))
        
        if show_warning:
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'type': 'warning',
                'title': _("Warning"),
                'message': _('Expenses must be completed before adding them to a report.')
            })   
        return result
    
    def unlink(self):
        for record in self:
            if record.uploaded_by_statement and not self.env.user.has_group('base.group_system'):
                raise UserError(_("You cannot delete an expense that was uploaded via a bank statement."))
        return super(ExpenseInherit, self).unlink()
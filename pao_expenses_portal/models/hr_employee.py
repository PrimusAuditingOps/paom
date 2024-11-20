from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductProposalItem(models.Model):

    _inherit="hr.employee"
    
    expenses_manager =  fields.Boolean(string="Expenses Manager", default=False)
        
    
    @api.constrains('expenses_manager')
    def _check_unique_expenses_manager(self):
        for record in self:
            if record.expenses_manager:
                
                if not record.user_id:
                    raise ValidationError(_("An employee must have an associated user to be an expenses manager."))
                
                other_records = self.env['hr.employee'].search([('expenses_manager', '=', True)])
                if len(other_records) > 1 or (len(other_records) == 1 and other_records.id != record.id):
                    raise ValidationError(_("Only one employee can be expenses manager."))
                
    def upload_account_statement(self):
        return {
            'name': _('Upload Account Statement'),
            'type': 'ir.actions.act_window',
            'res_model': 'upload.expense.statement',
            'view_mode': 'form',
            'view_id': self.env.ref('pao_expenses_portal.view_upload_expense_statement_form').id,
            'context': {'default_employee_id': self.id},
            'target': 'new',
        }
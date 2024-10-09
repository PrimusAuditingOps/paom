from odoo import models, fields, api, _
import base64
import xlrd
import csv
from datetime import datetime, timedelta
import dateutil.parser
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class UploadExpenseStatement(models.TransientModel):
    _name = 'upload.expense.statement'
    _description = 'Upload Expense Statement'

    employee_id = fields.Many2one('hr.employee')
    statement_file = fields.Binary('Account Statement', required=True)
    statement_filename  = fields.Char('File Name')
    process_run = fields.Boolean(default=False)

    def write(self, vals):
        try:
            if 'statement_file' in vals:
                vals['statement_filename'] = vals.get('statement_file', '').split('/')[-1] or 'unknown_filename'
        except Exception as e:
            action= {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'title': _('Error Uploading Statement'),
                    'message': _('An error occurred while processing the file, please try again.'),
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
            return action
        return super(UploadExpenseStatement, self).write(vals)
    
    def action_import_statement(self):
        try:
            if self.process_run:
                return
            
            send_notification_to_user = False
            odoo_bot = self.env.ref('base.partner_root')
            
            if not self.employee_id:
                self.employee_id = self.env.user.employee_id.id
            else:
                send_notification_to_user = True
            
            if self.env.company.country_code not in ('MX', 'US', 'CR', 'CL'):
                raise UserError(_('This process is not available for your company. Please contact IT support.'))
            
            
            if '.csv' in self.statement_filename:
                expenses = self._process_csv_file(base64.b64decode(self.statement_file))
            elif '.xlsx' in self.statement_filename:
                expenses = self._process_excel_file(base64.b64decode(self.statement_file))
            else:
                raise UserError(_('Unsupported file format. Please upload a CSV or Excel file with a correct format.'))
            
            for expense in expenses:
                if send_notification_to_user:
                    self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'summary': _('New expense to complete and send for approval'),
                        'note': _('You have a new expense to complete and send for approval.'),
                        'res_model_id': self.env['ir.model'].search([('model', '=', 'hr.expense')], limit=1).id,
                        'res_id': expense.id,
                        'user_id': expense.employee_id.user_id.id,
                        'create_uid': odoo_bot.id,
                    })
        except UserError as e:
            _logger.warning(e)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'danger',
                    'title': _('Error Uploading Statement'),
                    'message': e,
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        self.process_run = True
        # return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    def _process_csv_file(self, file_content):
        reader = csv.reader(file_content.decode('utf-8').splitlines())  # Decode for CSV handling

        expenses = []

        if self.env.company.country_code == 'MX':
            first_row = 8
        elif self.env.company.country_code in ['US','CR', 'CL']:
            first_row = 1
            
        for x in range(first_row-1):
            next(reader)
        
        row_index=0
        for row in reader:
            
            row_index += 1
            if row_index == 1:
                headers = row
                if not self._check_format(headers):
                    raise UserError(_('The format of the uploaded file is incorrect, please try again'))
                continue
            
            if self.env.company.country_code == 'MX':
                expense = self._process_mexico_format(row)
            elif self.env.company.country_code in ['US','CR', 'CL']:
                expense = self._process_usa_format(row)
                
            if expense:   
                expenses.append(expense)

        return expenses

    def _process_excel_file(self, file_content):
        workbook = xlrd.open_workbook(file_contents=file_content)
        worksheet = workbook.sheet_by_index(0)  # Assuming data is in the first sheet
        
        expenses = []
        
        
        if self.env.company.country_code == 'MX':
            first_row = 8
        elif self.env.company.country_code in ['US','CR', 'CL']:
            first_row = 1
            
        headers = worksheet.row_values(first_row-1)
        
        if not self._check_format(headers):
            raise UserError(_('The format of the uploaded file is incorrect, please try again'))
        
        # Process the Excel data and create records
        for rownum in range(first_row, worksheet.nrows):
            row = worksheet.row_values(rownum)
            if self.env.company.country_code == 'MX':
                expense = self._process_mexico_format(row)
            elif self.env.company.country_code in ['US','CR', 'CL']:
                expense = self._process_usa_format(row)
                
            if expense:   
                expenses.append(expense)
        
        return expenses
    
    def _check_format(self, headers):
        if self.env.company.country_code == 'MX':
            placeholder = ['SEC','Concepto/Referencia','Cargo','Abono','Saldo']
        elif self.env.company.country_code in ['US','CR', 'CL']:
            placeholder = ['Date','Transaction','Name','Memo','Amount']
        
        for header, expected in zip(headers, placeholder):
            _logger.warning(header)
            _logger.warning(expected)
            if header.strip() != expected:
                return False
        
        return True

    
    def _process_mexico_format(self, row):
        expense = None
        
        if str(row[2]).strip() != '':
            expense = self.env['hr.expense'].sudo().create({
                'name': row[1],
                'product_id': None,
                'employee_id': self.employee_id.id,
                'partner_id': None,
                'total_amount_currency': float(str(row[2]).replace(',', '')) if row[2] else 0.0,  # Handle potential empty values
                'currency_id': self.env.company.currency_id.id,
                'payment_mode': 'company_account',
                'uploaded_by_statement': True,
                'date': None,
            })
        
        return expense
    
    def _process_usa_format(self, row):
        expense = None
        
        date_value = self._parse_date(row[0])
        
        if str(row[4]).strip() != '':
            expense = self.env['hr.expense'].sudo().create({
                'name': row[2],
                'product_id': None,
                'employee_id': self.employee_id.id,
                'partner_id': None,
                'total_amount_currency': abs(float(str(row[4]).replace(',', ''))) if row[4] else 0.0,  # Handle potential empty values
                'currency_id': self.env.company.currency_id.id,
                'payment_mode': 'company_account',
                'uploaded_by_statement': True,
                'date': date_value,
            })
        
        return expense
    
    def _parse_date(self, value):
        try:
            # Check if the value is a float (likely an Excel date serial number)
            if isinstance(value, float):
                if value > 40000:  # Basic filter for date serial numbers
                    excel_start_date = datetime(1899, 12, 30)
                    delta = timedelta(days=value)
                    return excel_start_date + delta
            elif isinstance(value, str):
                # Try to parse the string as a date
                return dateutil.parser.parse(value)
        except (ValueError, TypeError):
            # If parsing fails, return None
            return None

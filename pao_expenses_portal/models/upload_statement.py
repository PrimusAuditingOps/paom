from odoo import models, fields, api, _
import base64
import xlrd
import csv
from datetime import datetime, timedelta
import dateutil.parser
from odoo.exceptions import UserError



import tempfile
import subprocess
import base64
import re

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
            elif '.pdf' in self.statement_filename:
                _logger.warning("*************ES UN PDF*****************")
                expenses = self._process_pdf_file(base64.b64decode(self.statement_file))
            else:
                raise UserError(_('Unsupported file format. Please upload a CSV or Excel file with a correct format.'))
            
            
            _logger.warning("*************TERMINA PROCESO BANKSTMNT*****************")
            
            _logger.warning("*************"+ str(len(expenses)) +"*****************")
            
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
        return {'type': 'ir.actions.client', 'tag': 'reload'}
    
    def _process_pdf_file(self, file_binary):
        results = []

        with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
            pdf_file.write(file_binary)
            pdf_file.flush()

            try:
                output = subprocess.check_output(['pdftotext', '-layout', pdf_file.name, '-'], stderr=subprocess.STDOUT)
                text = output.decode('utf-8')
            except subprocess.CalledProcessError as e:
                _logger.error("pdftotext failed: %s", e.output.decode())
                return results

        # Split and clean lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        transaction_buffer = []
        expenses = []

        for line in lines:
            _logger.debug("LINE: %s", line)
            transaction_buffer.append(line)

            # Heuristic: if buffer has 6+ lines and ends with 'US$xx.xx', treat it as a complete block
            if len(transaction_buffer) >= 6 and re.search(r'US\$\d+\.\d{2}$', transaction_buffer[-1]):
                candidate = ' '.join(transaction_buffer)
                _logger.debug("CANDIDATE: %s", candidate)

                # Match general format: date (split), amount, tax, name, merchant, total
                match = re.search(
                    r'(?P<month_day_year>\d{2}/\d{2}/\d{2})\s+(\d{2})\s+US\$(?P<amount>\d+\.\d{2})\s+US\$[\d\.\s]*[A-Z]+, [A-Z]+ \*\d+ (?P<merchant>.+?)\s+1\s+US\$(?P=amount)',
                    candidate
                )

                if match:
                    data = match.groupdict()
                    try:
                        full_date = f"{data['month_day_year']}{match.group(2)}"  # e.g. 04/28/20 + 25
                        date_obj = datetime.strptime(full_date, '%m/%d/%y%y').date()
                        results.append({
                            'date': date_obj,
                            'amount': float(data['amount']),
                            'merchant': data['merchant'].strip()
                        })
                        _logger.info("Parsed expense: %s", results[-1])
                        transaction_buffer.clear()
                    except Exception as e:
                        _logger.warning("Failed to parse transaction: %s", e)
                        transaction_buffer.clear()
                else:
                    # Not a valid match, keep buffer but clear if too long
                    if len(transaction_buffer) > 10:
                        transaction_buffer.clear()

        # Create hr.expense records
        for rec in results:
            _logger.warning("************* CREATING EXPENSE *************")
            expense = self.env['hr.expense'].create({
                'name': rec['merchant'],
                'date': rec['date'],
                'unit_amount': rec['amount'],
                'employee_id': self.employee_id.id,
                'product_id': self.env.ref('hr_expense.product_product_expense').id,
                'quantity': 1,
            })
            expenses.append(expense)

        return expenses
    
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
from odoo import http
from odoo.http import request, content_disposition
import os

class DownloadTemplateController(http.Controller):

    @http.route('/download/pao-bank-statement-template/<int:employee_id>', type='http', auth='user')
    def download_excel_template(self, employee_id, **kwargs):
        employee = request.env['hr.employee'].sudo().browse(employee_id)

        if not employee.exists():
            return request.not_found()

        company = employee.company_id

        if company.country_code == 'MX':
            file_name = 'mx_bank_statement.xlsx'
        elif company.country_code in ['US','CR', 'CL']:
            file_name = 'usa_bank_statement_template.csv'
        else:
            return request.not_found()

        module_path = http.addons_manifest['pao_expenses_portal']['root']
        file_path = os.path.join(module_path, 'static', 'templates', file_name)

        if not os.path.isfile(file_path):
            return request.not_found()

        with open(file_path, 'rb') as f:
            content = f.read()

        return request.make_response(
            content,
            [
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(file_name))
            ]
        )

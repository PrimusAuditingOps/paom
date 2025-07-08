from odoo import http
from odoo.http import request, content_disposition
import os

class DownloadTemplateController(http.Controller):

    @http.route('/download/pao-bank-statement-template/<string:country_code>', type='http', auth='user')
    def download_excel_template(self, country_code, **kwargs):

        if country_code == 'MX':
            file_name = 'mx_bank_statement.xlsx'
        elif country_code in ['US','CR', 'CL']:
            file_name = 'usa_bank_statement_template.csv'
        else:
            return request.not_found()

        module_path = os.path.dirname(os.path.abspath(__file__))
        module_root = os.path.dirname(os.path.dirname(module_path))
        file_path = os.path.join(module_root, 'static', 'templates', file_name)


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

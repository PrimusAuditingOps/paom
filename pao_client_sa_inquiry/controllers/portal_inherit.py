from odoo import http, _
from odoo.http import request
from odoo.addons.purchase.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from collections import OrderedDict
import logging
import base64
import xlrd
from datetime import date

_logger = logging.getLogger(__name__)
class ServiceAgreementsPortal(http.Controller):
    
    def is_user_auditor(self):
        user = request.env.user
        return user.partner_id.is_an_in_house_auditor
    
    @http.route('/my/expense_reports', type='http', methods=['GET'], auth='user', website=True, sitemap=False)
    def my_expense_report(self, **kwargs):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        request.session.pop('error_expense', None)
        
        user = request.env.user
        
        if request.env.company.country_code == 'MX':
            expense_reports = request.env['hr.expense.sheet'].sudo().search([
                ('partner_id', '=', user.partner_id.id),
                ('company_id', '=', request.env.company.id)
            ])
        else:
            expense_reports = request.env['hr.expense.sheet'].sudo().search([
                ('employee_id', '=', user.employee_id.id),
                ('company_id', '=', request.env.company.id)
            ])
        
        return request.render('pao_expenses_portal.my_expense_reports_view', {'expense_reports': expense_reports, 'page_name': 'expense_reports'})
    
    
    def get_categories(self):
        categories = request.env['product.product'].sudo().search([
            ('category_for_auditors', '=', True),
            ('can_be_expensed', '=',True), '|',('company_id', '=', request.env.company.id),('company_id', '=', False)
        ])
        return categories

    def get_currencies(self):
        currencies = request.env['res.currency'].search([])
        return currencies
        
    def purchase_order_has_expense_report(self, purchase_order_id, report_id):
        
        if not purchase_order_id or not purchase_order_id.isdigit(): 
            return False
        report_id = "-1" if not report_id else report_id
        report = request.env['hr.expense.sheet'].sudo().search([
                    ('purchase_order', '=', int(purchase_order_id))
                ], limit=1)
        
        if report:
            return bool(report.id != int(report_id))
        else:
            return False
    
    @http.route(['/my/expense_reports/<int:report_id>', '/my/expense_reports/new'], type='http', auth='user', website=True)
    def portal_expense_report_detail(self, report_id=None, **kw):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        stages_options = request.env['hr.expense.sheet']._fields['state']._description_selection(request.env)
        today = date.today().strftime('%Y-%m-%d')
        values = {'page_name': 'expense_report_form_view', 'stages_options': stages_options, 'today': today}
        
        if report_id:
            report = request.env['hr.expense.sheet'].browse(report_id)
            if report.exists():
                submittable = report.state == 'draft'
                values.update({'report': report, 'submittable': submittable, 'categories': self.get_categories(), 'currencies': self.get_currencies()})
            else:
                return request.redirect('/my/expense_reports')
        else:
            values.update({'new_report': True, 'report': None})
        
        purchase_order_redirect  = kw.get("purchase_order")
        if purchase_order_redirect:
            if not self.purchase_order_has_expense_report(purchase_order_redirect, None):
                purchase_order = request.env['purchase.order'].sudo().browse(int(purchase_order_redirect))
                if purchase_order.exists() and purchase_order.state != 'cancel' and (purchase_order.ac_audit_status.name == 'Confirmada' or purchase_order.ac_audit_status.name == 'Confirmed') :
                    values.update({'purchase_order_redirect': purchase_order_redirect})
            else:
                referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
                return request.redirect(referer_url)
                    
        user = request.env.user
        purchase_orders_account = request.env['purchase.order'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '!=', 'cancel'),
            '|', ('ac_audit_status.name', '=', 'Confirmada'), ('ac_audit_status.name', '=', 'Confirmed')
        ])
        
        schemes = request.env['expense.scheme'].sudo().search([('company_id', '=', request.env.company.id)])
        
        values.update({'purchase_orders_account': purchase_orders_account, 'schemes': schemes, 'currency': request.env.company.currency_id.name})
        
        error_expense = request.session.get('error_expense')
        if error_expense:
            
            values.update({'error_expense': error_expense})
        request.session.pop('error_expense', None)
        
        return request.render('pao_expenses_portal.my_expenses_details_view', values)
    
    def _save_expense_sheet(self, kw):
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        request.session.pop('error_expense', None)
        
        id = kw.get('report_id')
        summary = kw.get('report_summary')
        purchase_order = kw.get('report_purchase_order')
        scheme = kw.get('scheme')

        scheme_id = int(scheme) if scheme and scheme.isdigit() else None
        purchase_order_id = int(purchase_order) if purchase_order and purchase_order.isdigit() else None

        
        values = {'name': summary,'purchase_order': purchase_order_id, 'payment_mode': 'company_account', 'expense_scheme_id': scheme_id} #{{DEJAR QUE AUDITOR SELECCIONE PAID BY?}}
        
        if self.purchase_order_has_expense_report(purchase_order, id):
            referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
            request.session['error_expense'] = _('This purchase order already has a related expense report.')
            return request.redirect(referer_url)
        
        if id:
            expense_sheet = request.env['hr.expense.sheet'].browse(int(id))
            expense_sheet.write(values)
        else:
            if request.env.company.country_code == 'MX':
                values.update({'partner_id': request.env.user.partner_id.id})
            else:
                employee = request.env.user.employee_id
                if not employee:
                    request.session['error_expense'] = _("The current user does not have an employee registered, it is necessary to have one to continue with the process.")
                values.update({'employee_id': employee.id})

            expense_sheet = request.env['hr.expense.sheet'].sudo().create(values)
            
        if purchase_order and purchase_order.isdigit():
            order = request.env['purchase.order'].sudo().browse(int(purchase_order))
            order.write({'sheet_id': expense_sheet.id})

        return expense_sheet
    
    @http.route(['/my/expense_reports/save'], type='http', auth='user', website=True, methods=['POST'])
    def portal_save_expense_sheet(self, **kw):
        
        expense_save_result = self._save_expense_sheet(kw)
        
        if isinstance(expense_save_result, request.env['hr.expense.sheet'].__class__):
            return request.redirect('/my/expense_reports/' + str(expense_save_result.id))
        else:
            return expense_save_result
    
    def _get_expense_manager(self):
        manager = request.env['hr.employee'].sudo().search([
            ('expenses_manager','=',True),
            ('company_id', '=', request.env.company.id)
        ], limit=1)
        return manager.user_id.id if manager else None
    
    @http.route(['/my/expense_reports/submit'], type='http', auth='user', website=True, methods=['POST'])
    def portal_submit_expense_report(self, **kw):
        
        self._save_expense_sheet(kw)
        
        request.session.pop('error_expense', None)
        report_id = kw.get("report_id")
        
        if not report_id:
            return request.redirect('/my/expense_reports')
        
        report = request.env['hr.expense.sheet'].browse(int(report_id))
        
        if not report.exists():
            return request.redirect('/my/expense_reports')
        
        if not report.expense_line_ids:
            request.session['error_expense'] = _('You need to add expenses to the report in order to submit it.')
        else:
            report.sudo().user_id = self._get_expense_manager()
            report.action_submit_sheet()
        
        return request.redirect('/my/expense_reports/' + str(report.id))
    
    
    @http.route(['/my/expense_reports/reset'], type='http', auth='user', website=True, methods=['POST'])
    def portal_reset_expense_report(self, **kw):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        report_id = kw.get("report_id")
        
        if report_id:
            report = request.env['hr.expense.sheet'].browse(int(report_id))
            
            if report.exists():
                # report.sudo()._check_can_reset_approval()
                if report.state == 'post':
                    report.sudo()._do_reverse_moves()
                report.sudo()._do_reset_approval()
            
        return request.redirect('/my/expense_reports/' + str(report.id))
    
    
    @http.route(['/my/expense_reports/delete'], type='http', auth='user', website=True, methods=['POST'])
    def portal_delete_expense_report(self, **kw):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        report_id = kw.get("report_id")
        
        if report_id:
            report = request.env['hr.expense.sheet'].browse(int(report_id))
            
            if report.exists():
                
                purchase_order_id = report.purchase_order.id if report.purchase_order else None
                if purchase_order_id:
                    order = request.env['purchase.order'].sudo().browse(int(purchase_order_id))
                    order.write({'sheet_id': None})

                report.expense_line_ids.sudo().unlink()
                report.sudo().unlink()

            
            return request.redirect('/my/expense_reports')


    @http.route(['/my/expense/new', '/my/wallet_expense/new'], type='http', auth='user', website=True, methods=['POST'])
    def portal_new_expense(self, **kw):
        
        request.session.pop('error_expense', None)
        
        current_route = request.httprequest.path
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        report_id = kw.get("report_id")
        description = kw.get("description")
        expense_category = kw.get("expense_category")
        expense_date = kw.get("expense_date")
        receipts = request.httprequest.files.getlist("receipt")
        total = kw.get("total")
        currency_id = kw.get("currency_id")
        
        partner = request.env.user.partner_id
        
        
        if partner.st_supplier_taxes_id:
            tax_ids = partner.st_supplier_taxes_id.taxes_id
        elif request.env.company.country_code != 'MX':
            tax_ids = None
        else:
            request.session['error_expense'] = _("You don't have supplier taxes defined. Please contact our team to resolve this issue.")
            referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
            return request.redirect(referer_url)
        
        values = {
            'name': description,
            'product_id': int(expense_category),
            'date': expense_date,
            'total_amount_currency': float(total),
            'payment_mode': 'company_account',
            'currency_id': int(currency_id),
            'tax_ids': tax_ids
            }
        
        if request.env.company.country_code == 'MX':
            values.update({'partner_id': partner.id})
        else:
            values.update({'employee_id': request.env.user.employee_id.id})

        if not report_id and "wallet" not in current_route:
            return request.redirect('/my/expense_reports')
        elif "wallet" not in current_route:
            values.update({'sheet_id': int(report_id)})
        
        expense = request.env['hr.expense'].create(values)
        
        if report_id and expense.sheet_id.expense_scheme_id:
            expense.sudo().write({'account_id': expense.sheet_id.expense_scheme_id.property_account_expense_id.id})
        
        for receipt in receipts:
            attachment_data = {
                'name': receipt.filename,
                'type': 'binary',
                'datas': base64.b64encode(receipt.read()),
                'res_model': 'hr.expense',
                'res_id': expense.id,
                'res_name': expense.name,
                'mimetype': receipt.content_type,
            }
            request.env['ir.attachment'].sudo().create(attachment_data)
        
        if report_id:
            return request.redirect('/my/expense_reports/' + str(report_id))
        else:
            return request.redirect('/my/wallet')
    
    @http.route(['/my/expense/delete'], type='http', auth='user', website=True, methods=['POST'])
    def portal_delete_expense(self, **kw):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        expense_id = kw.get("expense_id")
        unlink = kw.get("unlink")
        
        user = request.env.user
        
        if expense_id:
            expense = request.env['hr.expense'].browse(int(expense_id))
            
            if expense.exists() and user == expense.create_uid:
                
                if unlink == "1":
                    expense.sudo().unlink()
                else:
                    expense.sudo().write({'sheet_id': None, 'account_id': None})
            
            referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
            return request.redirect(referer_url)
        
    
    
    
    
    
    
    
    @http.route('/my/wallet', type='http', auth='user', website=True)
    def portal_my_wallet(self, **kw):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        user = request.env.user
        
        if request.env.company.country_code == 'MX':
            expenses = request.env['hr.expense'].sudo().search([
                ('partner_id', '=', user.partner_id.id)
            ])
            
            reports = request.env['hr.expense.sheet'].sudo().search([
                ('partner_id', '=', user.partner_id.id), ('state', '=', 'draft')
            ])
        else:
            expenses = request.env['hr.expense'].sudo().search([
                ('employee_id', '=', user.employee_id.id)
            ])
            
            reports = request.env['hr.expense.sheet'].sudo().search([
                ('employee_id', '=', user.employee_id.id), ('state', '=', 'draft')
            ])
        
        values = {
                    'reports': reports, 'expenses': expenses, 'page_name': 'wallet_expenses', 
                    'currency': request.env.company.currency_id.name, 
                    'categories': self.get_categories(), 'currencies': self.get_currencies()
                }
        
        error_expense = request.session.get('error_expense')
        if error_expense:
            
            values.update({'error_expense': error_expense})
        request.session.pop('error_expense', None)
        
        return request.render('pao_expenses_portal.my_wallet_expenses_view', values)
    
    
    @http.route('/my/wallet/add_expenses_to_report', type='http', auth='user', website=True, methods=['POST'])
    def portal_add_expense_to_report(self, **kw):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        request.session.pop('error_expense', None)
        
        report_id = kw.get("report_id")
        
        selected_expenses = request.httprequest.form.getlist('selected_expenses')
        
        invalid_expenses_list = []
        
        for expense_id in selected_expenses:
            expense = request.env['hr.expense'].sudo().browse(int(expense_id))
            if expense.nb_attachment < 1:
                invalid_expenses_list.append(expense.name)
            else:
                expense.sudo().write({'sheet_id': int(report_id)})
                if expense.sheet_id.expense_scheme_id:
                    expense.sudo().write({'account_id': expense.sheet_id.expense_scheme_id.property_account_expense_id.id})
                
        if len(invalid_expenses_list) > 0: 
            invalid_expenses = ', '.join(map(str, invalid_expenses_list))
            request.session['error_expense'] = _("The following expenses couldn't be added to the report because they do not have an attached receipt: %(invalid_expenses)s") % {'invalid_expenses': invalid_expenses}
        
        return request.redirect('/my/wallet')
    
    
    @http.route('/my/wallet/add_receipt_to_expense', type='http', auth='user', website=True, methods=['POST'])
    def portal_add_receipt_to_expense(self, **kw):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        request.session.pop('error_expense', None)
        
        receipts = request.httprequest.files.getlist("receipt")
        expense_id = kw.get("expense_id")
        
        expense = request.env['hr.expense'].browse(int(expense_id))
        
        _logger.warning(receipts)
        for receipt in receipts:
            attachment_data = {
                'name': receipt.filename,
                'type': 'binary',
                'datas': base64.b64encode(receipt.read()),
                'res_model': 'hr.expense',
                'res_id': expense.id,
                'res_name': expense.name,
                'mimetype': receipt.content_type,
            }
            request.env['ir.attachment'].sudo().create(attachment_data)
            
        
        return request.redirect('/my/wallet')
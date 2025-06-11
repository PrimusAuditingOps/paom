from odoo import http, _
from odoo.http import request
import logging
import base64
import xlrd
from datetime import date
from odoo.addons.portal.controllers.portal import pager
from collections import OrderedDict

_logger = logging.getLogger(__name__)
class ExpensesPortal(http.Controller):
    
    def is_user_auditor(self):
        user = request.env.user
        return user.partner_id.is_an_in_house_auditor
    
    def _get_expense_sheet_searchbar_sortings(self):
        return {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'state': {'label': _('State'), 'order': 'state'},
        }
        
    def _get_expense_sheet_searchbar_filters(self):
        return {
            'all': {'label': _('All'), 'domain': []},
            'to_submit': {'label': _('To Submit'), 'domain': [('state', '=', 'draft')]},
            'submitted': {'label': _('Submitted'), 'domain': [('state', '=', 'submitted')]},
            'approved': {'label': _('Approved'), 'domain': [('state', '=', 'approve')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
        }
    
    @http.route(['/my/expense_reports', '/my/expense_reports/page/<int:page>'], type='http', methods=['GET'], auth='user', website=True, sitemap=False)
    def my_expense_report(self, page=1, sortby=None, filterby=None, url='/my/expense_reports', purchase_order=None, **kwargs):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        request.session.pop('error_expense', None)
        
        searchbar_sortings = self._get_expense_sheet_searchbar_sortings()
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        searchbar_filters = self._get_expense_sheet_searchbar_filters()
        if not filterby:
            filterby = 'all'
        domain = searchbar_filters[filterby]['domain']
        
        user = request.env.user
        if request.env.company.country_code == 'MX':
            domain += [
                ('partner_id', '=', user.partner_id.id),
                ('company_id', '=', request.env.company.id)
            ]
        else:
            domain += [
                ('employee_id', '=', user.employee_id.id),
                ('company_id', '=', request.env.company.id)
            ]
        
        if purchase_order and purchase_order.isdigit():
            domain += [
                ('purchase_order', '=', int(purchase_order)),
            ]
        
        page_detail = pager(
            url = url,
            total = request.env['hr.expense.sheet'].sudo().search_count(domain),
            page = page,
            step = 20,
            url_args = {'sortby': sortby, 'filterby': filterby}
        )
        
        expense_reports = request.env['hr.expense.sheet'].sudo().search(domain, order=order, limit=20, offset=page_detail['offset'])
        
        return request.render('pao_expenses_portal.my_expense_reports_view', {
            'expense_reports': expense_reports, 
            'page_name': 'expense_reports', 
            'currency': request.env.company.currency_id.name,
            'pager': page_detail,
            'default_url': url,
            'searchbar_sortings': searchbar_sortings, 
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
        })
    
    
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
        
        user = request.env.user
        purchase_orders_account = request.env['purchase.order'].sudo().search([
            ('partner_id', '=', user.partner_id.id),
            ('state', '!=', 'cancel'),
            '|', ('ac_audit_status.name', '=', 'Confirmada'), ('ac_audit_status.name', '=', 'Confirmed')
        ])
        
        purchase_order_redirect  = kw.get("purchase_order")
        if purchase_order_redirect:
            # if not self.purchase_order_has_expense_report(purchase_order_redirect, None):
                purchase_order = request.env['purchase.order'].sudo().browse(int(purchase_order_redirect))
                if (purchase_order.exists() and 
                    purchase_order.state != 'cancel' and 
                    purchase_order.ac_audit_status.name in ('Confirmada', 'Confirmed') and
                    purchase_order in purchase_orders_account
                ):
                    values.update({'purchase_order_redirect': purchase_order_redirect})
            # else:
            #     referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
            #     return request.redirect(referer_url)
        
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

        
        values = {
                    'name': summary,
                    'purchase_order': purchase_order_id, 
                    # 'payment_mode': 'company_account', ##{{DEJAR QUE AUDITOR SELECCIONE PAID BY?}}
                    'expense_scheme_id': scheme_id
                } 
        
        # if self.purchase_order_has_expense_report(purchase_order, id):
        #     referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
        #     request.session['error_expense'] = _('This purchase order already has a related expense report.')
        #     return request.redirect(referer_url)
        
        if id:
            expense_sheet = request.env['hr.expense.sheet'].browse(int(id))
            expense_sheet.write(values)
        else:
            if request.env.company.country_code == 'MX':
                values.update({'partner_id': request.env.user.partner_id.id})
            else:
                employee = request.env.user.employee_id or request.env.user.employee_ids[:1]
                if not employee:
                    request.session['error_expense'] = _("The current user does not have an employee registered, it is necessary to have one to continue with the process.")
                values.update({'employee_id': employee.id})

            expense_sheet = request.env['hr.expense.sheet'].sudo().create(values)
            
        if purchase_order and purchase_order.isdigit():
            order = request.env['purchase.order'].sudo().browse(int(purchase_order))
            if order.exists():
                expense_sheet.write({'purchase_order': order.id})

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
        payment_mode = kw.get("payment_mode")
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
            'payment_mode': payment_mode if payment_mode else 'company_account',
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
        
    
    
    
    
    
    def _get_wallet_searchbar_sortings(self):
        return {
            'date': {'label': _('Date'), 'order': 'date desc'},
            'state': {'label': _('State'), 'order': 'state'},
        }
        
    def _get_wallet_searchbar_filters(self):
        return {
            'all': {'label': _('All'), 'domain': []},
            'to_submit': {'label': _('To Submit'), 'domain': [('state', '=', 'reported')]},
            'submitted': {'label': _('Submitted'), 'domain': [('state', '=', 'submitted')]},
            'approved': {'label': _('Approved'), 'domain': [('state', '=', 'approved')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
        }
    
    @http.route(['/my/wallet', '/my/wallet/page/<int:page>'], type='http', methods=['GET'], auth='user', website=True, sitemap=False)
    def portal_my_wallet(self, page=1, sortby=None, filterby=None, url='/my/wallet', **kw):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        searchbar_sortings = self._get_wallet_searchbar_sortings()
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        
        searchbar_filters = self._get_wallet_searchbar_filters()
        if not filterby:
            filterby = 'all'
        domain = searchbar_filters[filterby]['domain']
        
        
        user = request.env.user
        reports_domain = ''
        
        if request.env.company.country_code == 'MX':
            domain += [
                ('partner_id', '=', user.partner_id.id)
            ]
            
            reports_domain = [
                ('partner_id', '=', user.partner_id.id), ('state', '=', 'draft')
            ]
        else:
            domain += [
                ('employee_id', '=', user.employee_id.id)
            ]
            
            reports_domain = [
                ('employee_id', '=', user.employee_id.id), ('state', '=', 'draft')
            ]
            
        page_detail = pager(
            url = url,
            total = request.env['hr.expense'].sudo().search_count(domain),
            page = page,
            step = 20,
            url_args = {'sortby': sortby, 'filterby': filterby}
        )
        
        expenses = request.env['hr.expense'].sudo().search(domain, order=order, limit=20, offset=page_detail['offset'])
        reports = request.env['hr.expense.sheet'].sudo().search(reports_domain)
        
        today = date.today().strftime('%Y-%m-%d')
        values = {
                    'reports': reports, 
                    'expenses': expenses, 
                    'page_name': 'wallet_expenses', 
                    'currency': request.env.company.currency_id.name, 
                    'categories': self.get_categories(), 
                    'currencies': self.get_currencies(),
                    'today': today,
                    'pager': page_detail,
                    'default_url': url,
                    'searchbar_sortings': searchbar_sortings, 
                    'sortby': sortby,
                    'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
                    'filterby': filterby,
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
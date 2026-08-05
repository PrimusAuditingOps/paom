from odoo import http, _
from odoo.http import request
import logging
import base64
import xlrd
from datetime import date
from odoo.addons.portal.controllers.portal import pager
from collections import OrderedDict
import zipfile
import io


from odoo.http import request, content_disposition
import os

_logger = logging.getLogger(__name__)
class ExpensesPortal(http.Controller):
    
    def is_user_auditor(self):
        user = request.env.user
        # return user.partner_id.is_an_in_house_auditor
        return user.partner_id.ado_is_auditor
    
    def is_external_auditor(self):
        partner = request.env.user.partner_id
        return partner.ado_is_auditor and not partner.is_an_in_house_auditor
    
    def _get_expense_sheet_searchbar_sortings(self):
        return {
            'date': {'label': _('Date'), 'order': 'create_date desc'},
            'state': {'label': _('State'), 'order': 'state_sequence asc'},
        }
        
    def _get_expense_sheet_searchbar_filters(self):
        return {
            'all': {'label': _('All'), 'domain': []},
            'to_submit': {'label': _('To Submit'), 'domain': [('state', '=', 'draft')]},
            'submit': {'label': _('Submitted'), 'domain': [('state', '=', 'submit')]},
            'approved': {'label': _('Approved'), 'domain': [('state', '=', 'approve')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]},
            'post': {'label': _('Posted'), 'domain': [('state', '=', 'post')]},
            'cancel': {'label': _('Refused'), 'domain': [('state', '=', 'cancel')]},
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
        is_external_auditor = self.is_external_auditor()
        if request.env.company.country_code == 'MX' or is_external_auditor:
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
        
        is_external_auditor = self.is_external_auditor()
        
        stages_options = request.env['hr.expense.sheet']._fields['state']._description_selection(request.env)
        today = date.today().strftime('%Y-%m-%d')
        values = {'page_name': 'expense_report_form_view', 'stages_options': stages_options, 'today': today, 'is_external_auditor': is_external_auditor}
        
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
        
        taxes = request.env['account.tax'].sudo().search([
            ('type_tax_use', '=', 'purchase'),
            ('company_id', '=', request.env.company.id),
        ])
        
        values.update({'taxes': taxes, 'purchase_orders_account': purchase_orders_account, 'schemes': schemes, 'currency': request.env.company.currency_id.name})
        
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
        is_external_auditor = kw.get('is_external_auditor')

        scheme_id = int(scheme) if scheme and scheme.isdigit() else None
        purchase_order_id = int(purchase_order) if purchase_order and purchase_order.isdigit() else None

        
        values = {
                    'name': summary,
                    'purchase_order': purchase_order_id, 
                    # 'payment_mode': 'company_account', ##{{DEJAR QUE AUDITOR SELECCIONE PAID BY?}}
                    'expense_scheme_id': scheme_id,
                    'from_external_auditor': bool(is_external_auditor),
                }
        
        # if self.purchase_order_has_expense_report(purchase_order, id):
        #     referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
        #     request.session['error_expense'] = _('This purchase order already has a related expense report.')
        #     return request.redirect(referer_url)
        
        if id:
            expense_sheet = request.env['hr.expense.sheet'].browse(int(id))
            expense_sheet.write(values)
        else:
            if request.env.company.country_code == 'MX' or is_external_auditor:
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
        
        if not bool(is_external_auditor) and request.env.company.country_code == 'US':
            expenses = expense_sheet.expense_line_ids.filtered(
                lambda e: not e.analytic_distribution
            )
            if expenses:
                expenses.write({
                    'analytic_distribution': {
                        '344': 100
                    }
                })

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
        
        is_external_auditor = self.is_external_auditor()
        
        report_id = kw.get("report_id")
        expense_category = kw.get("expense_category")
        
        expense_category = request.env['product.product'].sudo().browse(int(expense_category))

        name = kw.get("name") or expense_category.name
                
        description = kw.get("description")
        expense_date = kw.get("expense_date")
        payment_mode = kw.get("payment_mode")
        receipts = request.httprequest.files.getlist("receipt")
        total = kw.get("total")
        currency_id = kw.get("currency_id")
        
        partner = request.env.user.partner_id
        
        if partner.st_supplier_taxes_id:
            tax_ids = partner.st_supplier_taxes_id.taxes_id
        elif request.env.company.country_code == 'CR':
            tax_ids = [
                int(tax)
                for tax in request.httprequest.form.getlist('tax_ids')
            ]
        elif request.env.company.country_code != 'MX':
            tax_ids = None
        else:
            request.session['error_expense'] = _("You don't have supplier taxes defined. Please contact our team to resolve this issue.")
            referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
            return request.redirect(referer_url)
        
        values = {
            'name': name,
            'description': description,
            'product_id': int(expense_category),
            'date': expense_date,
            'total_amount_currency': float(total),
            'payment_mode': payment_mode if payment_mode else 'company_account',
            'currency_id': int(currency_id),
            'tax_ids': tax_ids
            }
        
        if request.env.company.country_code == 'MX' or is_external_auditor:
            values.update({'partner_id': partner.id, 'from_external_auditor': bool(is_external_auditor)})
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
            if not receipt or not receipt.filename:
                continue
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
            referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
            return request.redirect(referer_url)
    
    @http.route(['/my/expense/delete'], type='http', auth='user', website=True, methods=['POST'])
    def portal_delete_expense(self, **kw):
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        expense_id = kw.get("expense_id")
        unlink = kw.get("unlink")
        
        user = request.env.user
        
        if expense_id:
            expense = request.env['hr.expense'].browse(int(expense_id))
            
            if expense.exists():
                
                if unlink == "1":
                    if not expense.uploaded_by_statement and user == expense.create_uid:
                        expense.sudo().unlink()
                    else:
                        request.session['error_expense'] = _("You are not allowed to delete this expense.")
                else:
                    expense.sudo().write({'sheet_id': None, 'account_id': None})
            
            referer_url = request.httprequest.environ.get('HTTP_REFERER', '/')
            return request.redirect(referer_url)
        
    @http.route('/my/expense/<int:expense_id>/download_receipts', type='http', auth='user', website=True)
    def download_expense_receipts(self, expense_id, **kwargs):
        
        request.session.pop('error_expense', None)
        
        if not self.is_user_auditor():
            return request.redirect('/my/home')
        
        expense = request.env['hr.expense'].sudo().browse(expense_id)
        
        is_external_auditor = self.is_external_auditor()
        
        if not expense.exists():
            return request.not_found()

        # Internal user - validate through employee
        if not is_external_auditor:
            if expense.employee_id.user_id != request.env.user:
                return request.not_found()
        # External partner - validate through partner_id
        else:
            if expense.partner_id != request.env.user.partner_id:
                return request.not_found()
        
        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.expense'),
            ('res_id', '=', expense_id),
        ])
        
        if not attachments:
            if expense.sheet_id:
                request.session['error_expense'] = _("The selected expense has no receipts attached.")
                return request.redirect('/my/expense_reports/' + str(expense.sheet_id.id))
            else:
                return request.redirect('/my/expense_reports/')
        
        if len(attachments) == 1:
            # Single file — return directly
            attachment = attachments[0]
            return request.make_response(
                attachment.raw,
                headers=[
                    ('Content-Type', attachment.mimetype or 'application/octet-stream'),
                    ('Content-Disposition', f'attachment; filename="{expense.name + "_" + attachment.name}"'),
                ]
            )
        
        # Multiple files — zip them
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for attachment in attachments:
                zip_file.writestr(expense.name + "_" + attachment.name, attachment.raw)
        
        zip_buffer.seek(0)
        return request.make_response(
            zip_buffer.read(),
            headers=[
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', f'attachment; filename="receipts_{str(expense.date) + "_" +expense.name}.zip"'),
            ]
        )
        
    @http.route('/my/expense_reports/<int:sheet_id>/download_receipts', type='http', auth='user', website=True)
    def download_expense_report_receipts(self, sheet_id, **kwargs):
        
        request.session.pop('error_expense', None)

        if not self.is_user_auditor():
            return request.redirect('/my/home')

        sheet = request.env['hr.expense.sheet'].sudo().browse(sheet_id)

        is_external_auditor = self.is_external_auditor()

        if not sheet.exists():
            return request.not_found()

        # Internal user - validate through employee
        if not is_external_auditor:
            if sheet.employee_id.user_id != request.env.user:
                return request.not_found()
        # External partner - validate through partner_id
        else:
            if sheet.partner_id != request.env.user.partner_id:
                return request.not_found()

        # Gather all attachments from all expenses in the sheet
        expense_ids = sheet.expense_line_ids.ids
        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.expense'),
            ('res_id', 'in', expense_ids),
        ])

        if not attachments:
            return request.redirect('/my/expense_reports/')

        if len(attachments) == 1:
            attachment = attachments[0]
            expense_name = request.env['hr.expense'].sudo().browse(attachment.res_id).name
            return request.make_response(
                attachment.raw,
                headers=[
                    ('Content-Type', attachment.mimetype or 'application/octet-stream'),
                    ('Content-Disposition', f'attachment; filename="{sheet.name}_{expense_name}_{attachment.name}"'),
                ]
            )

        # Multiple files — zip them all
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Group by expense for cleaner filenames
            expense_map = {e.id: e for e in sheet.expense_line_ids.sudo()}
            for attachment in attachments:
                expense = expense_map.get(attachment.res_id)
                expense_label = expense.name if expense else str(attachment.res_id)
                zip_file.writestr(f"{expense_label}_{attachment.name}", attachment.raw)

        zip_buffer.seek(0)
        return request.make_response(
            zip_buffer.read(),
            headers=[
                ('Content-Type', 'application/zip'),
                ('Content-Disposition', f'attachment; filename="receipts_{sheet.name}.zip"'),
            ]
        )
        
    
    
    
    def _get_wallet_searchbar_sortings(self):
        return {
            'date': {'label': _('Date'), 'order': 'date desc'},
            'state': {'label': _('State'), 'order': 'state_sequence asc'},
        }
        
    def _get_wallet_searchbar_filters(self):
        return {
            'all': {'label': _('All'), 'domain': []},
            'to_report': {'label': _('To Report'), 'domain': [('state', '=', 'draft')]},
            'to_submit': {'label': _('To Submit'), 'domain': [('state', '=', 'reported')]},
            'submitted': {'label': _('Submitted'), 'domain': [('state', '=', 'submitted')]},
            'refused': {'label': _('Refused'), 'domain': [('state', '=', 'refused')]},
            'approved': {'label': _('Approved'), 'domain': [('state', '=', 'approved')]},
            'done': {'label': _('Done'), 'domain': [('state', '=', 'done')]}
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
        
        is_external_auditor = self.is_external_auditor()
        
        user = request.env.user
        reports_domain = ''
        
        if request.env.company.country_code == 'MX' or is_external_auditor:
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
        
        taxes = request.env['account.tax'].sudo().search([
            ('type_tax_use', '=', 'purchase'),
            ('company_id', '=', request.env.company.id),
        ])
        
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
                    'taxes': taxes,
                    'is_external_auditor': is_external_auditor,
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
            if not expense.is_complete:
                invalid_expenses_list.append(expense.name)
            else:
                expense.sudo().write({'sheet_id': int(report_id)})
                if expense.sheet_id.expense_scheme_id:
                    expense.sudo().write({'account_id': expense.sheet_id.expense_scheme_id.property_account_expense_id.id})
                
        if len(invalid_expenses_list) > 0: 
            invalid_expenses = ', '.join(map(str, invalid_expenses_list))
            request.session['error_expense'] = _("The following expenses were not added to the report because they are missing required information. Please review and complete them before attempting to add them again: %(invalid_expenses)s") % {'invalid_expenses': invalid_expenses}
        
        return request.redirect(
            kw.get('redirect_url') or '/my/wallet'
        )
    
    
    @http.route('/my/wallet/add_receipt_to_expense', type='http', auth='user', website=True, methods=['POST'])
    def portal_add_info_to_expense(self, **kw):

        if not self.is_user_auditor():
            return request.redirect('/my/home')

        request.session.pop('error_expense', None)

        expense_category = kw.get("expense_category")
        receipts = request.httprequest.files.getlist("receipt")
        expense_id = kw.get("expense_id")
        description = kw.get("description")
        
        expense_category = request.env['product.product'].sudo().browse(int(expense_category))

        name = kw.get("name") or expense_category.name
            
        payment_mode = kw.get("payment_mode")
        expense_date = kw.get("expense_date")
        total = kw.get("total")
        currency_id = kw.get("currency_id")

        expense = request.env['hr.expense'].browse(int(expense_id))
        
        tax_ids = None
        if request.env.company.country_code == 'CR':
            tax_ids = [
                int(tax)
                for tax in request.httprequest.form.getlist('tax_ids')
            ]

        vals = {
            'product_id': int(expense_category),
            'description': description,
        }

        if name:
            vals['name'] = name

        if tax_ids is not None:
            vals['tax_ids'] = [(6, 0, tax_ids)]

        if payment_mode and not expense.sheet_id:
            vals['payment_mode'] = payment_mode

        if expense_date:
            vals['date'] = expense_date

        if total:
            vals['total_amount_currency'] = float(total)

        if currency_id:
            vals['currency_id'] = int(currency_id)

        expense.sudo().write(vals)

        # Remove existing receipts
        request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'hr.expense'),
            ('res_id', '=', expense.id),
        ]).unlink()

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

        return request.redirect(
            kw.get('redirect_url') or '/my/wallet'
        )

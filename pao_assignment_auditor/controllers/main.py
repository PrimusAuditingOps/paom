import datetime
import calendar as cal
from dateutil.relativedelta import relativedelta
import pytz
from babel.dates import format_datetime, format_date
import base64
from werkzeug.urls import url_encode
from math import acos, cos, sin, radians
from odoo import http, _, fields
from odoo.http import request
from odoo.tools import html2plaintext, DEFAULT_SERVER_DATETIME_FORMAT as dtf
from odoo.tools.misc import get_lang
from logging import getLogger
from odoo.addons.web.controllers.main import content_disposition
from functools import reduce

_logger = getLogger(__name__)
 
class webAuditorAssignment(http.Controller):
    
    @http.route(['/auditor_assignment'], type='json', auth='user', methods=['POST'])
    def test(self, dates=None, startdates=None, products=None, organizations= None, saleorderid = None, orderid=None, cityid=None, failed=False, **kwargs):
        user_id = request.env.context.get('uid')
        weightings = self._get_weighting()
        auditors_list = []
        scheme_rating_list = []
        audit_quantity_list = []
        audit_honorarium_list = []
        auditor_localization_list = []
        _logger.error(products)
        view_id = 0
        if weightings:
            auditors_list = self._get_approved_auditor(products)
            auditors_list = self._get_auditors_without_veto_organization(auditors_list,organizations)
            auditors_list = self._get_auditors_without_veto_customer(auditors_list,saleorderid)
            auditors_list = self._get_auditor_availability(auditors_list,dates,orderid)

            if auditors_list:
                schemes_ids = self._get_schemes(products)
                first_date_list = self._get_dates(startdates)
                first_start_date = datetime.datetime.strptime(startdates[0], '%Y-%m-%d')
                if weightings.scheme_ranking > 0:
                    scheme_rating_list = self._get_auditor_scheme_rating(auditors_list, schemes_ids, weightings.scheme_ranking)
                if weightings.location > 0:
                    auditor_localization_list = self._get_auditor_localization(auditors_list, cityid, weightings.location,first_start_date)
                if weightings.audit_quantity_target > 0:
                    audit_quantity_list = self._get_auditor_audit_quantity_target(auditors_list,weightings.audit_quantity_target,first_date_list, orderid)
                if weightings.audit_honorarium_target > 0:
                    audit_honorarium_list = self._get_auditor_audit_honorarium_target(auditors_list,weightings.audit_honorarium_target,first_date_list, orderid)



                sql = """DELETE FROM paoassignmentauditor_auditor_qualification WHERE ref_user_id = %(user_id)s"""
                params = {
                    'user_id': user_id,
                }
                request.env.cr.execute(sql,params)
                for auditor in auditors_list:
                    qualification = 0.00
                    scheme = 0.00
                    localization = 0.00
                    quantity = 0.00
                    honorarium = 0.00
                    objrate = filter(lambda x : x['id'] == auditor, scheme_rating_list) 
                    for r in objrate:
                        qualification += r['qualification']
                        scheme = round(r['qualification'],4)
                        break
                    objrate = filter(lambda x : x['id'] == auditor, auditor_localization_list) 
                    for r in objrate:
                        qualification += r['qualification']
                        localization = r['qualification']
                        break
                    objrate = filter(lambda x : x['id'] == auditor, audit_quantity_list) 
                    for r in objrate:
                        qualification += r['qualification']
                        quantity = round(r['qualification'],4)
                        break
                    
                    objrate = filter(lambda x : x['id'] == auditor, audit_honorarium_list) 
                    for r in objrate:
                        qualification += r['qualification']
                        honorarium = round(r['qualification'],4)
                        break

                    value = request.env['paoassignmentauditor.auditor.qualification'].sudo().create(
                        {
                            'auditor_id': auditor,
                            'scheme_qualification': scheme,
                            'localization_qualification': localization,
                            'audit_qty_qualification': quantity,
                            'audit_honorarium_qualification': honorarium,
                            'qualification': qualification,
                            'ref_user_id': user_id,
                        }
                    )
                    
        
        return {
            'auditors': auditors_list,
            'user_id': user_id
        }
        
    
    def _get_weighting(self):

        recweighting = request.env['paoassignmentauditor.weighting'].search([], limit=1)
        for rec in recweighting:
            return rec
        return {}

    def _get_approved_auditor(self, products_ids):

        auditor_ids = []
        
        product_len = len(products_ids)
        params = {}
        
        #Get Auditors
        sql = """
            SELECT id as id FROM res_partner WHERE ado_is_auditor = TRUE
        """
        request.env.cr.execute(sql, params)
        result = request.env.cr.dictfetchall()
        auditor_ids = [r['id'] for r in result]
        if product_len > 0 and len(auditor_ids) > 0:
            #Get Approved Auditors
            sql = """
                SELECT res_partner_id AS res_partner_id FROM 
                audit_assignment_product_res_partner_rel 
                WHERE res_partner_id IN %(partner_ids)s AND product_product_id IN %(products_ids)s 
                GROUP BY res_partner_id HAVING COUNT(res_partner_id) = %(products_lenght)s
            """
            params = {
                'partner_ids': tuple(auditor_ids),
                'products_ids': tuple(products_ids),
                'products_lenght': product_len,
            }
            request.env.cr.execute(sql, params)
            result = request.env.cr.dictfetchall()
            auditor_ids = [r['res_partner_id'] for r in result]
        return auditor_ids
    
    def _get_auditors_without_veto_organization(self,auditor_ids,organization_ids):
        

        organization_auditors = []

        if len(organization_ids) > 0 and len(auditor_ids) > 0:
            sql = """
                SELECT DISTINCT res_partner_id AS id FROM 
                servicereferralagreement_blocked_organizations_res_partner_rel 
                WHERE res_partner_id IN %(partner_ids)s AND 
                servicereferralagreement_blocked_organization_id IN %(organization_ids)s 
            """
            params = {
                'partner_ids': tuple(auditor_ids),
                'organization_ids': tuple(organization_ids),
            }
            request.env.cr.execute(sql, params)
            result = request.env.cr.dictfetchall()

            organization_auditors = [r['id'] for r in result]
           
        return [auditor for auditor in auditor_ids if auditor not in organization_auditors]
    
    def _get_auditors_without_veto_customer(self,auditor_ids,sale_order_id):
        customer_auditors = []
        if sale_order_id and len(auditor_ids) > 0:
            rec_sale_order = request.env['sale.order'].browse(sale_order_id)
            if rec_sale_order.partner_id:
                sale_partner_id = [rec_sale_order.partner_id.id]
                sql = """
                    SELECT DISTINCT res_partner_id AS id FROM 
                    assignment_auditor_blocked_company_res_partner_rel 
                    WHERE res_partner_id IN %(partner_ids)s AND 
                    assignment_blocked_company_id IN %(sale_partner_id)s 
                """
                params = {
                    'partner_ids': tuple(auditor_ids),
                    'sale_partner_id': tuple(sale_partner_id),
                }
                request.env.cr.execute(sql, params)
                result = request.env.cr.dictfetchall()

                customer_auditors = [r['id'] for r in result]
            
        return [auditor for auditor in auditor_ids if auditor not in customer_auditors]
    
    def _get_schemes(self,products_ids):
        schemes_list = []
        rec_products = request.env['product.product'].browse(products_ids)
        
        for product in rec_products:
            if product.categ_id.paa_schem_id and product.categ_id.paa_schem_id.id not in schemes_list:
                schemes_list.append(product.categ_id.paa_schem_id.id) 
        return schemes_list
    
    def _get_auditor_availability(self,auditor_ids,datelist,orderid):
     
        auditors_not_available_list = []
        if len(auditor_ids) > 0:

            for dates in datelist:
                sql = """
                    SELECT DISTINCT partner_id AS id FROM 
                    purchase_order_line 
                    WHERE partner_id IN %(partner_ids)s AND state != 'cancel' 
                    AND order_id <> %(order_id)s AND 
                    ((service_start_date >= %(star_date)s AND service_start_date <= %(end_date)s) OR
                    (service_end_date <= %(star_date)s AND service_end_date >= %(end_date)s) OR
                    (service_start_date <= %(star_date)s AND service_end_date >= %(star_date)s) OR
                    (service_start_date <= %(end_date)s AND service_end_date >= %(end_date)s))
                """
                params = {
                    'partner_ids': tuple(auditor_ids),
                    'star_date': dates["start_date"],
                    'end_date': dates["end_date"],
                    'order_id': orderid,
                }
                request.env.cr.execute(sql, params)
                result = request.env.cr.dictfetchall()
                auditors_not_available_list += [r['id'] for r in result if r['id'] not in auditors_not_available_list]


                sql = """
                    SELECT DISTINCT auditor_id AS id FROM 
                    auditordaysoff_days 
                    WHERE auditor_id IN %(partner_ids)s AND 
                    ((start_date >= %(star_date)s AND start_date <= %(end_date)s) OR
                    (end_date <= %(star_date)s AND end_date >= %(end_date)s) OR
                    (start_date <= %(star_date)s AND end_date >= %(star_date)s) OR
                    (start_date <= %(end_date)s AND end_date >= %(end_date)s))
                """
                params = {
                    'partner_ids': tuple(auditor_ids),
                    'star_date': dates["start_date"],
                    'end_date': dates["end_date"],
                }
                request.env.cr.execute(sql, params)
                result = request.env.cr.dictfetchall()
                auditors_not_available_list += [r['id'] for r in result if r['id'] not in auditors_not_available_list]

        return [auditor for auditor in auditor_ids if auditor not in auditors_not_available_list]
    
    def _get_auditor_scheme_rating(self,auditor_list, scheme_list, weighting):
        auditor_rating = []
        auditors = request.env['res.partner'].browse(auditor_list)
        for auditor in auditors:
            rating_list = []
            rating_sum = 0.00
            if scheme_list:
                for scheme in scheme_list:
                    rating_scheme = filter(lambda x : x['schem_id'].id == scheme, auditor.paa_rating_scheme_ids) 
                    if rating_scheme:
                        for r in rating_scheme:
                            rating_list.append(r.rating)
                            rating_sum += r.rating
                    else:
                        rating_list.append(0)
                        
                rating = round(rating_sum / len(rating_list),2) if rating_sum > 0 and len(rating_list) > 0 else 0
                qualification = 0 if rating <= 0 else round((rating * weighting) /100, 2)
                auditor_rating.append({'id': auditor.id, 'rating': rating, 'qualification': qualification})
            else:                
                auditor_rating.append({'id': auditor.id, 'rating': 0, 'qualification': 0})
        return auditor_rating
    
    def _get_auditor_localization(self,auditor_list, audit_city_id, weighting, first_start_date):
        auditor_localization_list = []
        auditor_localization_ranking_list = []
        localization_list = []
        auditor_ids = request.env['res.partner'].browse(auditor_list)

        if audit_city_id:
            reccity = request.env['res.city'].browse(audit_city_id)
            if not reccity.paa_city_latitude or not reccity.paa_city_longitude:
                citylang = reccity.with_context(lang='en_US')
                result = self._geo_localize(
                                citylang.name,
                                citylang.state_id.name,
                                citylang.country_id.name)
                if result:
                    reccity.write({
                        'paa_city_latitude': result[0],
                        'paa_city_longitude': result[1],
                    })
            
            if reccity.paa_city_latitude and reccity.paa_city_longitude:
                for auditor in auditor_ids:
                    purchase_order = self._get_localization_auditor_audit(auditor.id,first_start_date)
                    
                    if auditor.partner_latitude and auditor.partner_longitude:
                        point_1 = (reccity.paa_city_latitude, reccity.paa_city_longitude)
                        if purchase_order:
                            if purchase_order.audit_city_id.id == reccity.id:
                                point_2 = (reccity.paa_city_latitude, reccity.paa_city_longitude)

                            else:
                                point_2 = (purchase_order.audit_city_id.paa_city_latitude, purchase_order.audit_city_id.paa_city_longitude)
                        else:
                            point_2 = (auditor.partner_latitude, auditor.partner_longitude)
                        
                        distance = self._get_point_distances(point_1,point_2)
                        if distance <= 15:
                            distance = 15
                        localization_list.append(distance)
                        auditor_localization_list.append({'id': auditor.id,'distance': distance})
                    else:
                        auditor_localization_list.append({'id': auditor.id,'distance': 0})
            else:
                for auditor in auditor_ids:
                    auditor_localization_list.append({'id': auditor.id,'distance': 0})   
        else:
            for auditor in auditor_ids:
                auditor_localization_list.append({'id': auditor.id,'distance': 0})   
        

        if localization_list:
           localization_list.sort()
        else:
            localization_list.append(0)
        
        closest_distance = localization_list[0]
        for auditor_distances in auditor_localization_list:
            if closest_distance == 0:
                auditor_localization_ranking_list.append({'id': auditor_distances['id'], 'localization_ranking': 0, 'qualification': 0 })
            else:
                if auditor_distances['distance'] == 0:
                    ranking = 0
                    qualification = 0
                else:
                    ranking = (closest_distance/auditor_distances['distance']) * 100
                    qualification = (ranking * weighting) / 100
                auditor_localization_ranking_list.append({'id': auditor_distances['id'], 'localization_ranking': ranking, 'qualification': qualification })

        return auditor_localization_ranking_list
    
    def _get_localization_auditor_audit(self, auditor,first_start_date):
        orders_ids_list = []
        purchase_order = None

        end_date = first_start_date + relativedelta(days=-1)
        sql = """
            SELECT DISTINCT order_id AS order_id FROM 
            purchase_order_line 
            WHERE partner_id = %(partner_id)s AND 
            service_end_date = %(end_date)s AND state <> %(state)s
        """
        params = {
            'partner_id': auditor,
            'state': "cancel",
            'end_date':end_date,
        }
        request.env.cr.execute(sql, params)
        result = request.env.cr.dictfetchall()
        orders_ids_list += [r['order_id'] for r in result if r['order_id'] not in orders_ids_list]

        if orders_ids_list:
            rec_purchase_order = request.env["purchase.order"].browse(orders_ids_list)
            for rec_purchase in rec_purchase_order:
                if rec_purchase.audit_city_id:
                    if rec_purchase.audit_city_id.paa_city_latitude and rec_purchase.audit_city_id.paa_city_longitude:
                        purchase_order = rec_purchase
                        break
                    else:
                        citylang = rec_purchase.audit_city_id.with_context(lang='en_US')
                        result = self._geo_localize(
                                        citylang.name,
                                        citylang.state_id.name,
                                        citylang.country_id.name)
                        if result:
                            rec_purchase.audit_city_id.write({
                                'paa_city_latitude': result[0],
                                'paa_city_longitude': result[1],
                            })
                            purchase_order = rec_purchase
                            break
        return purchase_order
    
    def _geo_localize(self, city='', state='', country=''):
        geo_obj = request.env['base.geocoder']
        search = geo_obj.geo_query_address(city=city, state=state, country=country)
        result = geo_obj.geo_find(search, force_country=country)
        return result
    
    def _get_point_distances(self,point_1, point_2):
        point_1 = (radians(point_1[0]), radians(point_1[1]))
        point_2 = (radians(point_2[0]), radians(point_2[1]))

        distance = acos(sin(point_1[0])*sin(point_2[0]) + cos(point_1[0])*cos(point_2[0])*cos(point_1[1] - point_2[1]))

        return distance * 6371.01
    
    def _get_dates(self, startdates):
        dates_list = []
        first_date_list = []
        for dt in startdates:
            d = datetime.datetime.strptime(dt, '%Y-%m-%d')
            firsDayMonth = datetime.date(d.year, d.month, 1)
            if firsDayMonth not in first_date_list:
                first_date_list.append(firsDayMonth)
        return first_date_list

    def _get_auditor_audit_quantity_target(self, auditors_list, weighting, date_list, order_id):
        auditor_audit_quantity_target_list = []
        recconfiguration = self._get_configuration_audit_quantity()
        
        for rec in recconfiguration:
            season_start_month = int(rec.season_start_month)
            
            if rec.option == "auditor":
                auditor_audit_quantity_target_list = self._get_audits_quantity_per_auditor(auditors_list, weighting, date_list, season_start_month,order_id)
            elif rec.option == "month": 
                auditor_audit_quantity_target_list = self._get_audits_quantity_per_month(auditors_list, weighting, date_list, rec.audits_quantity_per_month_ids,order_id)
            elif rec.option == "trimester":
                auditor_audit_quantity_target_list = self._get_audits_quantity_per_trimester(auditors_list, weighting, date_list, season_start_month, rec, order_id)
            elif recconfiguration.option == "season":
                auditor_audit_quantity_target_list = self._get_audits_quantity_per_season(auditors_list, weighting, date_list, season_start_month,recconfiguration.audit_quantity, order_id)
            
        return auditor_audit_quantity_target_list
    
    def _get_configuration_audit_quantity(self):

        recauditconf = request.env['paoassignmentauditor.configuration.audit.quantity'].search([], limit=1)
        for rec in recauditconf:
            return rec
        return {}
    
    def _get_audits_quantity_per_auditor(self,auditors_list, weighting, date_list, season_start_month, order_id):
        auditor_audit_quantity_target_list = []
        season_dates_list = []
        
        
        products_ids = self._get_audit_products()
        for d in date_list:
            season_start_date = None
            if season_start_month <= d.month:
                season_start_date = datetime.date(d.year, season_start_month, 1)
            else:
                season_start_date = datetime.date(d.year - 1, season_start_month, 1)
            
            if season_start_date not in season_dates_list:
                season_dates_list.append(season_start_date)
        
        for auditor in auditors_list:
            total_audit = 0
            recpartner = request.env['res.partner'].browse(auditor)
            total_audit = recpartner.paa_audit_quantity
            count = 0
            qualification = 0.00
            for season_date in season_dates_list:
                season_end_date = season_date + relativedelta(years=1)
                qualification += self._get_calification_audit_quantity( products_ids, order_id, auditor, total_audit, season_date, season_end_date, weighting)
                count += 1
            qualification = qualification / count if count > 0 and qualification > 0 else weighting
            auditor_audit_quantity_target_list.append({'id': auditor,'qualification': qualification})
        return auditor_audit_quantity_target_list
    
    def _get_audits_quantity_per_month(self,auditors_list, weighting, date_list, months_list,order_id):
        auditor_audit_quantity_target_list = []
        season_dates_list = []

        products_ids = self._get_audit_products()

        for auditor in auditors_list:            
            count = 0
            qualification = 0.00
            for season_start_date in date_list:
                total_audit = 0
                month_date = filter(lambda x : x['month'] == str(season_start_date.month).rjust(2, '0'), months_list)
                for m in month_date:
                    total_audit = m['audit_quantity']
                season_end_date = season_start_date + relativedelta(months=1)
                audit_quantity_total = 0
                qualification+= self._get_calification_audit_quantity(products_ids, order_id, auditor, total_audit, season_start_date, season_end_date, weighting)
                count += 1
            qualification = qualification / count if count > 0 and qualification > 0 else weighting
            auditor_audit_quantity_target_list.append({'id': auditor,'qualification': qualification})
        
        return auditor_audit_quantity_target_list
    
    def _get_audits_quantity_per_trimester(self,auditors_list, weighting, date_list, season_start_month, configuration, order_id):
        auditor_audit_quantity_target_list = []
        season_dates_list = []
        date_list_aux = []

        products_ids = self._get_audit_products()

        #get first date of season
        for d in date_list:
            if season_start_month <= d.month:
                season_start_date = datetime.date(d.year, season_start_month, 1)
            else:
                season_start_date = datetime.date(d.year - 1, season_start_month, 1)
            break

        for d in date_list:
            season_start_date_aux = season_start_date
            count_trimester = 1
            while count_trimester <= 4:
                if d >= season_start_date_aux and d < (season_start_date_aux + relativedelta(months=3)):
                    if season_start_date_aux not in date_list_aux:
                        date_list_aux.append(season_start_date_aux)
                        if count_trimester == 1:
                            season_dates_list.append({'date': season_start_date_aux, 'quantity': configuration.first_month_audit_quantity})
                        elif count_trimester == 2:
                            season_dates_list.append({'date': season_start_date_aux, 'quantity': configuration.second_month_audit_quantity})
                        elif count_trimester == 3:
                            season_dates_list.append({'date': season_start_date_aux, 'quantity': configuration.third_month_audit_quantity})
                        elif count_trimester == 4:
                            season_dates_list.append({'date': season_start_date_aux, 'quantity': configuration.fourth_month_audit_quantity})
                    break
                if count_trimester == 4:
                    count_trimester = 1
                    season_start_date = season_start_date + relativedelta(years=1)
                    season_start_date_aux = season_start_date
                else:
                    count_trimester = count_trimester + 1
                    season_start_date_aux = season_start_date_aux + relativedelta(months=3)
        
        for auditor in auditors_list:
            count = 0
            qualification = 0.00
            for season_date_qty in season_dates_list:
                total_audit = 0
                trimester_start_date = season_date_qty['date']
                trimester_end_date = trimester_start_date + relativedelta(months=3)
                total_audit = season_date_qty['quantity']
                qualification += self._get_calification_audit_quantity(products_ids, order_id, auditor, total_audit, trimester_start_date, trimester_end_date, weighting)
                count += 1 
            qualification =  qualification / count if count > 0 and qualification > 0 else weighting
            auditor_audit_quantity_target_list.append({'id': auditor,'qualification': qualification})
        
        return auditor_audit_quantity_target_list
    
    def _get_audits_quantity_per_season(self,auditors_list, weighting, date_list, season_start_month,total_audit,order_id):
        auditor_audit_quantity_target_list = []
        season_dates_list = []

        products_ids = self._get_audit_products()

        for d in date_list:
            if season_start_month <= d.month:
                season_start_date = datetime.date(d.year, season_start_month, 1)
            else:
                season_start_date = datetime.date(d.year - 1, season_start_month, 1)
            
            if season_start_date not in season_dates_list:
                season_dates_list.append(season_start_date)

        for auditor in auditors_list:
            recpartner = request.env['res.partner'].browse(auditor)
            count = 0
            qualification = 0.00
            for season_start_date in season_dates_list:
                season_end_date = season_start_date + relativedelta(years=1)
                audit_quantity_total = 0
                qualification += self._get_calification_audit_quantity(products_ids, order_id, auditor, total_audit, season_start_date, season_end_date, weighting)
                count += 1                
            qualification = qualification / count if count > 0 and qualification > 0 else 0 if count > 0 and qualification <= 0 else  weighting
            auditor_audit_quantity_target_list.append({'id': auditor,'qualification': qualification})
        
        return auditor_audit_quantity_target_list
    
    def _get_audit_products(self):
        products_category_ids = []
        products_ids = []
        domain = [('paa_is_an_audit', '=', True)]
        rec_product_category = request.env['product.category'].search(domain)
        products_category_ids = [c.id for c in rec_product_category]
        if products_category_ids:
            domain = [('categ_id', 'in', products_category_ids)]
            rec_product = request.env['product.product'].search(domain)
            products_ids = [c.id for c in rec_product]
        
        return products_ids
    
    def _get_calification_audit_quantity(self, products_ids, order_id, auditor, total_audit, start_date, end_date, weighting):

        audit_quantity_total = 0
        percentage = 0
        qualification = 0
        domain = []
        if products_ids:                    
            domain = [('order_id', '<>', order_id),('partner_id','=',auditor), 
            ('state', '<>', 'cancel'),('product_id', 'in', products_ids),
            ('service_start_date', '>=', start_date),('service_start_date', '<', end_date)]
        
            rec_audit_quantity =  request.env['purchase.order.line'].read_group(domain,['partner_id', 'product_qty'], ['partner_id'])
            for audit_quantity in rec_audit_quantity:
                audit_quantity_total = audit_quantity['product_qty']
            percentage = (audit_quantity_total / total_audit) * 100 if audit_quantity_total > 0 and total_audit > 0 else 0
            percentage = 0 if percentage > 100 else 100 - percentage
            qualification = 0 if percentage <= 0 else (percentage * weighting) / 100
        else:
            qualification = weighting
        
        return qualification

    def _get_auditor_audit_honorarium_target(self, auditors_list, weighting, date_list, order_id):
        auditor_audit_honorarium_target_list = []

        recconfiguration = self._get_configuration_audit_honorarium()
        
        for rec in recconfiguration:
            season_start_month = int(rec.season_start_month)
            
            if rec.option == "auditor":
                auditor_audit_honorarium_target_list = self._get_audits_honorarium_per_auditor(auditors_list, weighting, date_list, season_start_month,order_id)
            
            elif rec.option == "month": 
                auditor_audit_honorarium_target_list = self._get_audits_honorarium_per_month(auditors_list, weighting, date_list, rec.audits_honorarium_per_month_ids,order_id)            
            
            elif rec.option == "trimester":
                auditor_audit_honorarium_target_list = self._get_audits_honorarium_per_trimester(auditors_list, weighting, date_list, season_start_month, rec,order_id)
            
            elif recconfiguration.option == "season":
                auditor_audit_honorarium_target_list = self._get_audits_honorarium_per_season(auditors_list, weighting, date_list, season_start_month,recconfiguration.audit_honorarium_total,recconfiguration.currency_id,order_id)
        
        return auditor_audit_honorarium_target_list
    
    def _get_configuration_audit_honorarium(self):

        recweighting = request.env['paoassignmentauditor.configuration.audit.honorarium'].search([], limit=1)
        for rec in recweighting:
            return rec
        return {}
    
    def _get_audits_honorarium_per_auditor(self,auditors_list, weighting, date_list, season_start_month, order_id):
        auditor_audit_honorarium_target_list = []
        season_dates_list = []
        products_ids = self._get_audit_products()
        
        for d in date_list:
            if season_start_month <= d.month:
                season_start_date = datetime.date(d.year, season_start_month, 1)
            else:
                season_start_date = datetime.date(d.year - 1, season_start_month, 1)
            
            if season_start_date not in season_dates_list:
                season_dates_list.append(season_start_date)

        for auditor in auditors_list:
            recpartner = request.env['res.partner'].browse(auditor)
            sum_honorarium = 0.00
            total = 0.00
            qualification =0
            audits_total_honorarium =  recpartner.paa_audits_honorarium_total
            qualification = 0.00
            count = 0
            for season_start_date in season_dates_list:
                season_end_date = season_start_date + relativedelta(years=1)
                qualification += self._get_calification_audit_honorarium(products_ids, order_id, auditor, audits_total_honorarium, season_start_date, season_end_date, weighting, recpartner.paa_currency_id.rate)
                count += 1
            qualification = qualification / count if count > 0 and qualification > 0 else weighting 
            auditor_audit_honorarium_target_list.append({'id': auditor,'qualification': qualification})
        return auditor_audit_honorarium_target_list
    
    def _get_calification_audit_honorarium(self, products_ids, order_id, auditor, audits_total_honorarium, start_date, end_date, weighting, partner_currency_rate):
        domain = []
        order_list = []
        percentage = 0
        qualification = 0
        if products_ids:
            domain = [('order_id', '<>', order_id),('partner_id','=',auditor),
            ('state', '<>', 'cancel'),('product_id', 'in', products_ids),
            ('service_start_date', '>=', start_date),
            ('service_start_date', '<', end_date)]

            recpurchaseordersline = request.env['purchase.order.line'].search(domain)
            if recpurchaseordersline:
                total = 0.00
                sum_honorarium = 0.00
                order_list = [ol.order_id.id for ol in recpurchaseordersline if ol.order_id.id not in order_list]
                domain = [('state', '!=', 'cancel'),('id','in',order_list)]
                purchase_order = request.env['purchase.order'].search(domain)
                for purchase in purchase_order:
                    sum_honorarium += purchase.amount_total / purchase.currency_id.rate
                total = sum_honorarium * partner_currency_rate

                percentage = (total / audits_total_honorarium) * 100 if total > 0 and audits_total_honorarium > 0 else 0
                percentage = 0 if percentage > 100 else 100 - percentage
                qualification = 0 if percentage <= 0 else (percentage * weighting) / 100
            else:
                qualification = weighting
        else:
            qualification = weighting

        return qualification
    
    def _get_audits_honorarium_per_month(self,auditors_list, weighting, date_list, months_list, order_id):
        auditor_audit_honorarium_target_list = []
        season_dates_list = []
        products_ids = self._get_audit_products()
        for auditor in auditors_list:            
            count = 0
            qualification = 0.00
            for season_start_date in date_list:
                audits_total_honorarium = 0.00
                audits_honorarium_currency = None
                month_date = filter(lambda x : x['month'] == str(season_start_date.month).rjust(2, '0'), months_list)
                for m in month_date:
                    audits_total_honorarium = m['audit_honorarium_total']
                    audits_honorarium_currency = m['currency_id']
                
                if audits_total_honorarium > 0:
                    season_end_date = season_start_date + relativedelta(months=1)
                    qualification += self._get_calification_audit_honorarium(products_ids, order_id, auditor, audits_total_honorarium, season_start_date, season_end_date, weighting, audits_honorarium_currency.rate)
                else:
                    qualification += weighting
                count = count + 1
             
            qualification = qualification / count if count > 0 and qualification > 0 else weighting 
            auditor_audit_honorarium_target_list.append({'id': auditor,'qualification': qualification})
        return auditor_audit_honorarium_target_list
    
    def _get_audits_honorarium_per_trimester(self,auditors_list, weighting, date_list, season_start_month, configuration,order_id):
        auditor_audit_honorarium_target_list = []
        season_dates_list = []
        date_list_aux = []
        products_ids = self._get_audit_products()
        #get first date of season
        for d in date_list:
            if season_start_month <= d.month:
                season_start_date = datetime.date(d.year, season_start_month, 1)
            else:
                season_start_date = datetime.date(d.year - 1, season_start_month, 1)
            
            break
        
        for d in date_list:
            season_start_date_aux = season_start_date
            count_trimester = 1
            while count_trimester <= 4:
                if d >= season_start_date_aux and d < (season_start_date_aux + relativedelta(months=3)):
                    if season_start_date_aux not in date_list_aux:
                        date_list_aux.append(season_start_date_aux)
                        if count_trimester == 1:
                            season_dates_list.append({'date': season_start_date_aux, 'honorarium': configuration.first_month_audit_honorarium})
                        elif count_trimester == 2:
                            season_dates_list.append({'date': season_start_date_aux, 'honorarium': configuration.second_month_audit_honorarium})
                        elif count_trimester == 3:
                            season_dates_list.append({'date': season_start_date_aux, 'honorarium': configuration.third_month_audit_honorarium})
                        elif count_trimester == 4:
                            season_dates_list.append({'date': season_start_date_aux, 'honorarium': configuration.fourth_month_audit_honorarium})
                    break
                if count_trimester == 4:
                    count_trimester = 1
                    season_start_date = season_start_date + relativedelta(years=1)
                    season_start_date_aux = season_start_date
                else:
                    count_trimester = count_trimester + 1
                    season_start_date_aux = season_start_date_aux + relativedelta(months=3)
        
        for auditor in auditors_list:
            count = 0
            qualification = 0.00
            for season_date_honorarium in season_dates_list:
                trimester_start_date = season_date_honorarium['date']
                trimester_end_date = trimester_start_date + relativedelta(months=3)
                audits_total_honorarium = season_date_honorarium['honorarium']
                
                if audits_total_honorarium > 0:
                    qualification += self._get_calification_audit_honorarium(products_ids, order_id, auditor, audits_total_honorarium, trimester_start_date, trimester_end_date, weighting, configuration.currency_id.rate)
                else:
                    qualification += weighting
                
                
                count = count + 1
                
            qualification =  qualification / count if count > 0 and qualification > 0 else weighting
            auditor_audit_honorarium_target_list.append({'id': auditor,'qualification': qualification})
        
        return auditor_audit_honorarium_target_list
    
    def _get_audits_honorarium_per_season(self,auditors_list, weighting, date_list, season_start_month,total_audit_honorarium,honorarium_currency,order_id):
        auditor_audit_honorarium_target_list = []
        season_dates_list = []
        products_ids = self._get_audit_products()
        for d in date_list:
            if season_start_month <= d.month:
                season_start_date = datetime.date(d.year, season_start_month, 1)
            else:
                season_start_date = datetime.date(d.year - 1, season_start_month, 1)
            
            if season_start_date not in season_dates_list:
                season_dates_list.append(season_start_date)

        for auditor in auditors_list:
            recpartner = request.env['res.partner'].browse(auditor)
            count = 0
            qualification = 0.00
            for season_start_date in season_dates_list:
                season_end_date = season_start_date + relativedelta(years=1)
                if total_audit_honorarium > 0:
                    qualification += self._get_calification_audit_honorarium(products_ids, order_id, auditor, total_audit_honorarium, season_start_date, season_end_date, weighting, honorarium_currency.rate)
                else:
                    qualification += weighting 
                count = count + 1
               
            qualification = qualification / count if count > 0 else weighting 
            auditor_audit_honorarium_target_list.append({'id': auditor,'qualification': qualification})
        return auditor_audit_honorarium_target_list
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
    def search_auditors(self, dates=None, startdates=None, products=None, organizations= None, saleorderid = None, orderid=None, cityid=None, stateid = None, auditquantity=0.00, languages = None, orderCountry = None, failed=False, **kwargs):
        user_id = request.env.context.get('uid')
        weightings = self._get_weighting()
        auditors_list = []
        scheme_rating_list = []
        audit_quantity_list = []
        audit_honorarium_list = []
        auditor_localization_list = []
        startdates = self._convert_startdates(startdates)
        _logger.error(stateid)
        view_id = 0
        if weightings:
            location = weightings.location
            scheme_ranking = weightings.scheme_ranking
            audit_quantity_target = weightings.audit_quantity_target
            audit_honorarium_target = weightings.audit_honorarium_target
            auditors_list = self._get_approved_auditor(products)
            auditors_list = self._get_auditor_languages(auditors_list, languages)
            auditors_list = self._get_auditors_without_veto_organization(auditors_list,organizations)
            auditors_list = self._get_auditors_without_veto_customer(auditors_list,saleorderid)
            auditors_list = self._get_auditor_availability(auditors_list,dates,orderid,orderCountry)

            if auditors_list:
                schemes_ids = self._get_schemes(products)
                first_date_list = self._get_dates(startdates)
                first_start_date = datetime.datetime.strptime(startdates[0], '%Y-%m-%d')
                if location > 0 and (not weightings.state_ids or stateid in weightings.state_ids.ids):
                    auditor_localization_list = self._get_auditor_localization(auditors_list, cityid, location,first_start_date)
                elif location > 0:
                    scheme_ranking = scheme_ranking + location
                    location = 0


                if scheme_ranking > 0:
                    scheme_rating_list = self._get_auditor_scheme_rating(auditors_list, schemes_ids, scheme_ranking)
                if audit_quantity_target > 0:
                    audit_quantity_list = self._get_auditor_audit_quantity_target(auditors_list,audit_quantity_target,first_date_list, orderid)
                if audit_honorarium_target > 0:
                    audit_honorarium_list = self._get_auditor_audit_honorarium_target(auditors_list,audit_honorarium_target,first_date_list, orderid)



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
                    
                    days = self._get_days_without_audits(auditor)


                    #total_to_pay = 0.00
                    in_house_auditor = False
                    recauditor = request.env['res.partner'].browse(auditor)
                    for recPartner in recauditor:
                        #total_to_pay = 0.00
                        in_house_auditor = recPartner.is_an_in_house_auditor

                        #recFee = request.env["servicereferralagreement.auditfees"].search([("default","=",True)])
                        #for fee in recFee:
                        #    for percentage in recPartner.audit_fee_percentages_ids.filtered_domain([('audit_fees_id', '=', fee.id)]):
                        #        total_to_pay = percentage.audit_percentage * price_total / 100

                    value = request.env['paoassignmentauditor.auditor.qualification'].sudo().create(
                        {
                            'auditor_id': auditor,
                            'scheme_qualification': scheme,
                            'localization_qualification': localization,
                            'audit_qty_qualification': quantity,
                            'audit_honorarium_qualification': honorarium,
                            'qualification': qualification,
                            'ref_user_id': user_id,
                            'day_without_audits': days,
                            'total_audits': 1 if auditquantity > 9 else 0,
                            'is_in_house': '0' if not in_house_auditor else '1',
                            'day_color': "blue" if days >= 22 and days <= 35 else "yellow" if days >= 36 and days <= 45 else "red" if days > 45 else "",
                        }
                    )
        res = {
            'auditors': auditors_list,
            'user_id': user_id
        }
        return res

    def _get_days_without_audits(self, auditor_id):
        requested_tz = pytz.timezone('America/Mexico_City')
        today = requested_tz.fromutc(datetime.datetime.utcnow())
        days = 0
        sql = """
            SELECT b.service_end_date as lastdate FROM 
            purchase_order AS a INNER JOIN purchase_order_line AS b ON a.id = b.order_id 
            WHERE a.partner_id = %(partner_id)s AND a.state != 'cancel' AND 
            b.service_end_date < %(today)s ORDER BY b.service_end_date DESC LIMIT 1
        """
        params = {
            'partner_id': auditor_id,
            'today': today,
        }
        request.env.cr.execute(sql, params)
        result = request.env.cr.dictfetchall()
        
        for last_service_date in result:
            diference = datetime.date(today.year, today.month, today.day) - last_service_date["lastdate"]
            days = int(diference.days)
            sql = """
                SELECT  CASE 
                WHEN start_date < %(star_date)s THEN %(star_date)s 
                ELSE start_date END AS startdate, 
                case 
                WHEN end_date > %(end_date)s THEN %(end_date)s 
                ELSE end_date END AS enddate 
                FROM 
                auditordaysoff_days 
                WHERE auditor_id = %(partner_id)s AND 
                ((start_date >= %(star_date)s AND start_date <= %(end_date)s) OR
                (end_date <= %(star_date)s AND end_date >= %(end_date)s) OR
                (start_date <= %(star_date)s AND end_date >= %(star_date)s) OR
                (start_date <= %(end_date)s AND end_date >= %(end_date)s))
            """
            params = {
                'partner_id': auditor_id,
                'star_date': last_service_date["lastdate"],
                'end_date': datetime.date(today.year, today.month, today.day),
            }
            request.env.cr.execute(sql, params)
            result_date = request.env.cr.dictfetchall()
            for rd in result_date:
                days_off = rd["enddate"] - rd["startdate"]
                lessday = days_off.days + 1
                days -= lessday
        
        return days


    def _get_weighting(self):

        recweighting = request.env['paoassignmentauditor.weighting'].search([], limit=1)
        for rec in recweighting:
            return rec
        return {}


    def _get_auditor_languages(self, auditors_list,lenguages_ids):
        
        auditor_ids = []
        if len(lenguages_ids) > 0:
            for auditor in auditors_list:
                recAuditor = request.env["res.partner"].browse(auditor)
                for l in lenguages_ids:
                    if l not in recAuditor.language_ids.ids:
                        auditor_ids.append(auditor)
                        break
        return [auditor for auditor in auditors_list if auditor not in auditor_ids]

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
    
    def _get_auditor_availability(self,auditor_ids,datelist,orderid,orderCountry):
     
        auditors_not_available_list = []
        if not orderid:
            orderid = 0
        _logger.error("orderCountry")
        _logger.error(orderCountry)
        if len(auditor_ids) > 0:

            for dates in datelist:
                if orderCountry != "US":
                    sql = """
                        SELECT DISTINCT pol.partner_id as id, po.shadow_id as shadow, po.assessment_id as assessment FROM 
                        purchase_order_line as pol inner join purchase_order as po on po.id = pol.order_id
                        WHERE (pol.partner_id IN %(partner_ids)s OR po.shadow_id IN %(partner_ids)s OR po.assessment_id IN %(partner_ids)s) AND pol.state != 'cancel' 
                        AND pol.order_id <> %(order_id)s AND po.id <> %(order_id)s AND 
                        ((pol.service_start_date >= %(star_date)s AND pol.service_start_date <= %(end_date)s) OR
                        (pol.service_end_date <= %(star_date)s AND pol.service_end_date >= %(end_date)s) OR
                        (pol.service_start_date <= %(star_date)s AND pol.service_end_date >= %(star_date)s) OR
                        (pol.service_start_date <= %(end_date)s AND pol.service_end_date >= %(end_date)s))
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
                    auditors_not_available_list += [r['shadow'] for r in result if r['shadow'] not in auditors_not_available_list]
                    auditors_not_available_list += [r['assessment'] for r in result if r['assessment'] not in auditors_not_available_list]

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
                        
                        
                        if point_1 == point_2:
                            distance = 15
                        else:
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

    def _convert_startdates(self, startdates):
        """ Remove the remain part of the date if exist 
        """
        formated_startdates = []
        for dt in startdates:
            sdt = str(dt)
            if 'T' in sdt:
                sdt = sdt.split('T')[0]
            formated_startdates.append(sdt)
        return formated_startdates

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
            if total_audit > 0:
                count = 0
                qualification = 0.00
                for season_date in season_dates_list:
                    season_end_date = season_date + relativedelta(years=1)
                    qualification += self._get_calification_audit_quantity( products_ids, order_id, auditor, total_audit, season_date, season_end_date, weighting)
                    count += 1
                qualification = qualification / count if count > 0 and qualification > 0 else 0
                auditor_audit_quantity_target_list.append({'id': auditor,'qualification': qualification})
            else:
                auditor_audit_quantity_target_list.append({'id': auditor,'qualification': 0})
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
            qualification = qualification / count if count > 0 and qualification > 0 else 0
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
            qualification =  qualification / count if count > 0 and qualification > 0 else 0
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
            qualification = qualification / count if count > 0 and qualification > 0 else 0 if count > 0 and qualification <= 0 else  0
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
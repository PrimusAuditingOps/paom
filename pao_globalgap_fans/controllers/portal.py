
from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers import portal
from logging import getLogger
from werkzeug.urls import url_join
import base64
import pytz
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import json

_logger = getLogger(__name__)

class CustomerPortal(portal.CustomerPortal):

  
    @http.route(['/pao_get_geolocation'], type='json', auth='public', methods=['POST'])
    def pao_get_geolocation(self, fan_id=False, fan_token=None, street=None, zip=None, city=None, state=None, country=None, **kwargs):
        latitude = 0.00
        longitude = 0.00
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', int(fan_id), access_token=str(fan_token))
            geo_obj = request.env['base.geocoder'].sudo()
            search = geo_obj.geo_query_address(street=street, zip=zip, city=city, state=state, country=country)
            result = geo_obj.geo_find(search, force_country=country)
            if result and result[0] and result[1]:
                latitude=result[0]
                longitude=result[1]
        except (AccessError, MissingError):
            latitude = 0.00
            longitude = 0.00
        
        return{
            'latitude': latitude,
            'longitude': longitude,
        }
        
    @http.route(['/pao/fillout/fans/<int:fan_id>/<string:fan_token>'], type='http', auth="public", website=True)
    def portal_fill_out_fans(self, fan_id=False, fan_token=None, **kw):
        
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', fan_id, access_token=fan_token)
        except (AccessError, MissingError):
            return request.redirect('/')

        
        if fan_sudo.request_status in ['review', 'signature_request', 'annulled']:
            return request.render(
                'pao_globalgap_fans.globalgap_fan_completed_cancel_page_view', {}
            )
        elif  fan_sudo.request_status == 'signed':
            url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') 
            documents = []
            documents.append({"name": fan_sudo.attachment_id.name, "url": url+"/web/content/"+str(fan_sudo.attachment_id.id)+"?download=true&access_token="+str(fan_sudo.attachment_id.access_token)})
            return request.render(
                'pao_globalgap_fans.globalgap_fan_signed_page_view', {"documents": documents}
            )


        lang = fan_sudo.capturist_id.lang or fan_sudo.create_uid.lang
        fan_sudo.with_context(lang=lang)

        countries = request.env['res.country'].sudo().with_context(lang=lang).search([])
        states = request.env['res.country.state'].with_context(lang=lang).sudo().search([])
        cities = request.env['res.city'].sudo().with_context(lang=lang).search([])
        versions = request.env['pao.globalgap.version'].sudo().with_context(lang=lang).search([])
        certificationOptions = request.env['pao.globalgap.certification.option'].sudo().with_context(lang=lang).search([])
        
        globalgapversion = request.env['pao.globalgap.organization'].sudo().with_context(lang=lang)._fields['globalgap_version'].selection
        certificationoption = request.env['pao.globalgap.organization'].sudo().with_context(lang=lang)._fields['certification_option'].selection
        evaluationtype = request.env['pao.globalgap.organization'].sudo().with_context(lang=lang)._fields['evaluation_type'].selection
        rightsofaccess = request.env['pao.globalgap.organization'].sudo().with_context(lang=lang)._fields['rights_of_access'].selection
        addons = request.env['pao.globalgap.addon'].sudo().with_context(lang=lang).search([])
        grasp_module = []
        for a in addons:
            if a.is_grasp_module:
                grasp_module.append(a.id)
        
        addon_list = []
        addon_list = [rec.id for rec in fan_sudo.organization_id.addons_ids]
        addon_string = ""
        if len(addon_list) > 0:
            for elem in addon_list:
                if addon_string == "":
                    addon_string += str(elem)
                else:
                    addon_string += "," + str(elem)
        return request.render(
            'pao_globalgap_fans.fan_portal_organization', 
            {
                "data": fan_sudo.organization_id, 
                "default_country": 57,
                "id": fan_id,
                "token": fan_token,
                "countries": countries, 
                "states": states, 
                "cities": cities,
                "certificationOptions": certificationOptions,
                "versions": versions,
                "glabalgapaddons": addons,
                "rightsofaccess": rightsofaccess,
                "certificationoption": certificationoption,
                "evaluationtype": evaluationtype,
                "globalgapversion": globalgapversion,
                "addon_string": addon_string,
                "addon": addon_list,
                "grasp_module": grasp_module,
            }
        )


    @http.route(['/pao/fillout/fans/products'], type='json', auth='public', methods=['POST'])
    def portal_fans_save_organization(self, fr_token, fr_id, unannounced, plmx, ggn, globalgap_version, 
    certification_option, evaluation_type, name, website, address, colony, city,state, country,
    zip, telephone, email, gln, vat, previous_cb, latitude, longitude, contact_name, contact_position,
    contact_telephone, contact_email, rights_of_access,addons,postal_address,previous_ggn,subcontracted_workers, hired_workers, **kw):

        try:
            fr_sudo = self._document_check_access('pao.globalgap.fans.request', int(fr_id), access_token=str(fr_token))
        except (AccessError, MissingError):
            return request.redirect('/')

        if fr_sudo.request_status in ['review', 'signature_request', 'signed', 'annulled']:
            return request.render(
                'pao_globalgap_fans.globalgap_fan_completed_cancel_page_view', {}
            )
        
        addon_list = []
        if addons != "":
            addon_list = [int(n) for n in addons.split(",")]
        organization_data = {
            "name": name,
            "website": website,
            "plmx": plmx,
            "ggn": ggn,
            'unannounced': unannounced,
            "number_of_hired_workers": subcontracted_workers,
            "number_of_subcontracted_workers": hired_workers,
            "version_id": globalgap_version,
            "certification_option_id": certification_option, 
            "addons_ids": [(6, 0, addon_list)],
            "evaluation_type": str(evaluation_type),
            "address": address,
            "colony": colony,
            "postal_address": postal_address,
            "previous_ggn": previous_ggn,
            "city_id": int(city),
            "state_id": int(state),
            "country_id": int(country),
            "zip": zip,
            "telephone": telephone,
            "email": email,
            "gln": gln,
            "vat": vat,
            "previous_cb": previous_cb,
            "latitude": latitude,
            "longitude": longitude,
            "contact_name": contact_name,
            "contact_telephone": contact_telephone,
            "contact_email": contact_email,
            "contact_position": contact_position,
            "rights_of_access": str(rights_of_access), 
        } 
    
        if fr_sudo.organization_id:
            fr_sudo.organization_id.write(organization_data)
        else:
            organization = request.env['pao.globalgap.organization'].sudo().create(organization_data)
            fr_sudo.write({"organization_id": organization.id})

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'redirect_url':  url_join(base_url, '/pao/fillout/fans/production_site/%s/%s' % (fr_id, fr_token))
        }

    @http.route(['/pao/fillout/fans/production_site/<int:fan_id>/<string:fan_token>'], type='http', auth="public", website=True)
    def portal_fill_out_fans_production_site(self, fan_id=False, fan_token=None, **kw):
        
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', fan_id, access_token=fan_token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        if fan_sudo.request_status in ['review', 'signature_request', 'signed', 'annulled']:
            return request.render(
                'pao_globalgap_fans.globalgap_fan_completed_cancel_page_view', {}
            )
        lang = fan_sudo.capturist_id.lang or fan_sudo.create_uid.lang
        fan_sudo.with_context(lang=lang)

        countries = request.env['res.country'].sudo().with_context(lang=lang).search([])
        states = request.env['res.country.state'].sudo().with_context(lang=lang).search([])
        cities = request.env['res.city'].sudo().with_context(lang=lang).search([])
        products = request.env['servicereferralagreement.auditproducts'].sudo().with_context(lang=lang).search([],order='name asc')
        certificate = request.env['pao.globalgap.production.site.product'].sudo().with_context(lang=lang)._fields['to_certificate'].selection
        pp = request.env['pao.globalgap.production.site.product'].sudo().with_context(lang=lang)._fields['parallel_production'].selection
        po = request.env['pao.globalgap.production.site.product'].sudo().with_context(lang=lang)._fields['parallel_property'].selection
        
        production_sites_list = []
        for rec in fan_sudo.organization_id.production_site_ids:
            product_list = []
            for p in rec.product_ids:
                
                product_obj = {
                    "product": p.product_id.name, 
                    "hectareas": p.hectares_in_production, 
                    "certify": p.to_certificate, 
                    "pp": p.parallel_production, 
                    "po": p.parallel_property, 
                    "productid": p.product_id.id,
                    "certify_text": dict(request.env['pao.globalgap.production.site.product'].sudo().with_context(lang=lang)._fields['to_certificate'].selection).get(p.to_certificate),
                    "pp_text": dict(request.env['pao.globalgap.production.site.product'].sudo().with_context(lang=lang)._fields['parallel_production'].selection).get(p.parallel_production),
                    "po_text": dict(request.env['pao.globalgap.production.site.product'].sudo().with_context(lang=lang)._fields['parallel_property'].selection).get(p.parallel_property),
                }
                product_list.append(product_obj)
            site_data = {
                "name": rec.name, 
                "type_name": dict(request.env['pao.globalgap.production.site'].sudo()._fields['type'].selection).get(rec.type), 
                "type": rec.type, 
                "address": rec.address, 
                "postal_address": rec.postal_address,
                "country_id": rec.country_id.id, 
                "state_id": rec.state_id.id, 
                "city_id": rec.city_id.id, 
                "zip": rec.zip, 
                "telephone": rec.telephone, 
                "email": rec.email, 
                "latitude": rec.latitude, 
                "longitude": rec.longitude, 
                "contactname": rec.contact_name, 
                "contactaddress": rec.contact_address, 
                "contactcountry": rec.contact_country_id.id, 
                "contactstate": rec.contact_state_id.id, 
                "contactcity": rec.contact_city_id.id, 
                "contactzip": rec.contact_zip, 
                "contacttelephone": rec.contact_telephone, 
                "contactemail": rec.contact_email,
                "products": product_list,
            }
            production_sites_list.append(site_data)
        return request.render(
            'pao_globalgap_fans.fan_portal_production_site', 
            {
                "data": fan_sudo.organization_id, 
                "id": fan_id,
                "token": fan_token,
                "back_url": "/pao/fillout/fans/" +str(fan_id) + "/" + fan_token,
                "countries": countries, 
                "states": states, 
                "cities": cities,
                "products": products,
                "certificate": certificate,
                "pp": pp,
                "po": po,
                "production_sites": json.dumps(production_sites_list),
            }
        )
    
    @http.route(['/pao/fillout/fans/production_site_phu'], type='json', auth='public', methods=['POST'])
    def portal_fans_save_production_sites(self, cr_token, cr_id, sites, **kw):
        try:
            fr_sudo = self._document_check_access('pao.globalgap.fans.request', int(cr_id), access_token=str(cr_token))
        except (AccessError, MissingError):
            return request.redirect('/')
        
        if fr_sudo.request_status in ['review', 'signature_request', 'signed', 'annulled']:
            return request.render(
                'pao_globalgap_fans.globalgap_fan_completed_cancel_page_view', {}
            )
        
        product_ids_list = []
        product_ids_hectares_list = []
        production_site = json.loads(sites)  
        request.env['pao.globalgap.production.site'].sudo().search([("organization_id","=",fr_sudo.organization_id.id)]).unlink()
        for obj in production_site:
            production_data = {
                "organization_id": fr_sudo.organization_id.id,
                "name": obj["name"],
                "type": obj["type"],
                "address": obj["address"],
                "postal_address": obj["postal_address"],
                "city_id": obj["city"],
                "state_id": obj["state"],
                "country_id": obj["country"],
                "zip": obj["zip"],
                "telephone": obj["telephone"],
                "email": obj["email"],
                "latitude": obj["latitude"],
                "longitude": obj["longitude"],
                "contact_name": obj["contactname"],
                "contact_telephone": obj["contacttelephone"],
                "contact_email": obj["contactemail"],
                "contact_address": obj["contactaddress"], 
                "contact_country_id": obj["contactcountry"], 
                "contact_state_id": obj["contactstate"], 
                "contact_city_id": obj["contactcity"], 
                "contact_zip": obj["contactzip"], 
            }
            production = request.env['pao.globalgap.production.site'].sudo().create(production_data)
            for product in obj["products"]:
                product_ids_list.append(int(product["productid"]))

                product_ids_hectares_list.append(
                    {
                        "id": int(product["productid"]),
                        "hect": float(product["hectareas"])
                    }
                )
                product_data = {
                    "production_site_id": production.id,
                    "parallel_production": product["pp"],
                    "parallel_property": product["po"],
                    "to_certificate": product["certify"],
                    "hectares_in_production": product["hectareas"],
                    "product_id": product["productid"],
                }
                product = request.env['pao.globalgap.production.site.product'].sudo().create(product_data)
                
            for p in product_ids_list:
                domain_create_product = [("organization_id","=",fr_sudo.organization_id.id),("product_id","=",p)]
                rec_product_information = request.env['pao.globalgap.production.site.product.information'].sudo().search(domain_create_product)
                if not rec_product_information:
                    total = 0.00
                    for e in product_ids_hectares_list:
                        if e['id']  == p:
                            total = float(float(total) + float(e['hect']))

                    request.env['pao.globalgap.production.site.product.information'].sudo().create(
                        {
                            "product_id": p, 
                            "organization_id":fr_sudo.organization_id.id,
                            "uncovered_production_area": total
                        }
                    )

            domain_product = [("organization_id","=",fr_sudo.organization_id.id), ("product_id","not in",product_ids_list)]
            request.env['pao.globalgap.production.site.product.information'].sudo().search(domain_product).unlink()
       
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        return {
            'redirect_url':  url_join(base_url, '/pao/fillout/fans/production_information/' + str(cr_id) + '/' + cr_token)
        }

    
    @http.route(['/pao/fillout/fans/production_information/<int:fan_id>/<string:fan_token>'], type='http', auth="public", website=True)
    def portal_fill_out_fans_product_information(self, fan_id=False, fan_token=None, **kw):
        product_ids = []
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', fan_id, access_token=fan_token)
            for rec in fan_sudo.organization_id.product_information_ids:
                product_ids.append(rec.product_id.id)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        if fan_sudo.request_status in ['review', 'signature_request', 'signed', 'annulled']:
            return request.render(
                'pao_globalgap_fans.globalgap_fan_completed_cancel_page_view', {}
            )
        lang = fan_sudo.capturist_id.lang or fan_sudo.create_uid.lang
        fan_sudo.with_context(lang=lang)
        return request.render(
            'pao_globalgap_fans.fans_portal_template_product_information', 
            {
                "data": fan_sudo.organization_id, 
                "id": fan_id,
                "token": fan_token,
                "product_ids": product_ids,
                "back_url": "/pao/fillout/fans/production_site/" +str(fan_id) + "/" + fan_token,
            }
        )

    @http.route(['/pao/fan/product_information'], type='json', auth='public', methods=['POST'])
    def pao_fan_product_information(self, fan_id=False, fan_token=None, **kwargs):
        data = []
        ids_list = []
        applicable_harvest = None
        harvest_type = None
        show_fsma = False
        product_handling = None
        product_manipulated_not_certificate = None
        organization_buys_product = None
        fsma = None
        countries = []
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', int(fan_id), access_token=str(fan_token))
            lang = fan_sudo.capturist_id.lang or fan_sudo.create_uid.lang
            fan_sudo.with_context(lang=lang)
            rec_countries = request.env['pao.globalgap.destination.countries'].sudo().with_context(lang=lang).search([])
            applicable_harvest = request.env['pao.globalgap.production.site.product.information'].sudo().with_context(lang=lang)._fields['applicable_harvest'].selection
            harvest_type = request.env['pao.globalgap.production.site.product.information'].sudo().with_context(lang=lang)._fields['harvest_type'].selection
            product_handling = request.env['pao.globalgap.production.site.product.information'].sudo().with_context(lang=lang)._fields['product_handling'].selection
            product_manipulated_not_certificate = request.env['pao.globalgap.production.site.product.information'].sudo().with_context(lang=lang)._fields['product_manipulated_not_certificate'].selection
            fsma = request.env['pao.globalgap.production.site.product.information'].sudo().with_context(lang=lang)._fields['fsma'].selection
            organization_buys_product = request.env['pao.globalgap.production.site.product.information'].sudo().with_context(lang=lang)._fields['organization_buys_product'].selection

            for recCountries in rec_countries:
                countries.append(
                    {
                        "id": recCountries.id,
                        "name": recCountries.name,
                    }
                )
            
            for addon in fan_sudo.organization_id.addons_ids:
                if addon.is_fsma_module:
                    show_fsma = True
                    break

            for rec in fan_sudo.organization_id.product_information_ids.with_context(lang=lang):
                ids_list.append(rec.product_id.id)
                countries_list = []
                for c in rec.countries_of_products:
                    countries_list.append(c.id)
                data.append(
                    {
                        "product_id": rec.product_id.id,
                        "product_name": rec.product_id.name,
                        "uncovered_production_area": rec.uncovered_production_area,
                        "covered_production_area": rec.covered_production_area,
                        "applicable_harvest": rec.applicable_harvest,
                        "harvest_type": rec.harvest_type,
                        "product_handling": rec.product_handling,
                        "outsourced_activities": rec.outsourced_activities,
                        "ggn_gln_outsourced": rec.ggn_gln_outsourced,
                        "product_manipulated_not_certificate": rec.product_manipulated_not_certificate,
                        "fsma": rec.fsma,
                        "organization_buys_product": rec.organization_buys_product,
                        "estimated_yield_in_tons": rec.estimated_yield_in_tons,
                        "dates_harvest_estimated": rec.dates_harvest_estimated,
                        "harvest_estimated_start_date": rec.harvest_estimated_start_date,
                        "harvest_estimated_end_date": rec.harvest_estimated_end_date,
                        "countries_of_products": countries_list,
                    }
                )
        except (AccessError, MissingError):
            data = []
            applicable_harvest = None
            harvest_type = None
            product_handling = None
            product_manipulated_not_certificate = None
            organization_buys_product = None
            countries = [],
            fsma = None

        
        return{
            "ids": ids_list,
            "data": data,
            "applicable_harvest": applicable_harvest,
            "harvest_type": harvest_type,
            "product_handling": product_handling,
            "fsma": fsma,
            "show_fsma": show_fsma,
            "product_manipulated_not_certificate": product_manipulated_not_certificate,
            "organization_buys_product": organization_buys_product,
            "countries": countries,
        }
    
    @http.route(['/pao/fan/register/product_information'], type='json', auth='public', methods=['POST'])
    def pao_fan_register_product_information(self, fan_id=False, fan_token=None, products=None, **kwargs):
        
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', int(fan_id), access_token=str(fan_token))
            for p in products:
                countries = []
                for c in p["countries_of_products"]:
                    countries.append(int(c))
                recProInfo = request.env['pao.globalgap.production.site.product.information'].sudo().search([("product_id","=",p["product_id"]),("organization_id","=", fan_sudo.organization_id.id)])
                recProInfo.write(
                    {
                        "uncovered_production_area": p["uncovered_production_area"],
                        "covered_production_area": p["covered_production_area"],
                        "applicable_harvest": p["applicable_harvest"],
                        "harvest_type": p["harvest_type"],
                        "product_handling": p["product_handling"],
                        "outsourced_activities": p["outsourced_activities"],
                        "ggn_gln_outsourced": p["ggn_gln_outsourced"],
                        "harvest_estimated_start_date": p["harvest_estimated_start_date"],
                        "harvest_estimated_end_date": p["harvest_estimated_end_date"],
                        "product_manipulated_not_certificate": p["product_manipulated_not_certificate"],
                        "organization_buys_product": p["organization_buys_product"],
                        "estimated_yield_in_tons": p["estimated_yield_in_tons"],
                        "dates_harvest_estimated": p["dates_harvest_estimated"],
                        "countries_of_products": [(6, 0, countries)],
                    }
                )
            


            fan_sudo.set_fill_out_message()
            """
            mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{fan_sudo.create_uid.id}">@{fan_sudo.create_uid.name}</a>'
            request_link = ('<a href="#" data-oe-model="pao.globalgap.fans.request" data-oe-id="%(request_id)d">%(name)s</a>'
                                    ) % {'name': fan_sudo.title, 'request_id': fan_sudo.id}

            message = _('Hello %(mention_html)s, the request %(request_link)s has been corrected.') % {'request_link': request_link, 'mention_html': mention_html} if fan_sudo.request_status == "correction" else _('Hello %(mention_html)s, the request %(request_link)s has been filled out.') % {'request_link': request_link, 'mention_html': mention_html}       
            message_id = fan_sudo.message_post(
                body=message,
                partner_ids=[fan_sudo.create_uid.partner_id.id],
            )
            fan_sudo.message_notify(
                message_id=message_id.id,
            )
            """

            fan_sudo.write({"request_status":"review"})


        except (AccessError, MissingError):
           return request.redirect('/')
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'redirect_url':  url_join(base_url, '/pao/fillout/fans/message/%s/%s' % (fan_id, fan_token))
        }
       
    

    @http.route(['/pao/fan/signature/<int:fr_id>/<string:fr_token>'], type='http', auth="public", website=True)
    def portal_fan_signature(self, report_type=None, fr_id=False, fr_token=None, **kw):
        
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', int(fr_id), access_token=str(fr_token))
        except (AccessError, MissingError):
            return request.redirect('/')
         
        if  fan_sudo.request_status == 'signed':
            url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') 
            documents = []
            documents.append({"name": fan_sudo.attachment_id.name, "url": url+"/web/content/"+str(fan_sudo.attachment_id.id)+"?download=true&access_token="+str(fan_sudo.attachment_id.access_token)})
            return request.render(
                'pao_globalgap_fans.globalgap_fan_signed_page_view', {"documents": documents}
            )
        elif fan_sudo.request_status != 'signature_request':
            return request.render(
                'pao_globalgap_fans.globalgap_fan_completed_cancel_page_view', {}
            )

        url = '/pao/fan/signature/'+str(fr_id)+'/'+fr_token+'/accept'
 
        #lang = sa_sudo.signer_id.lang or sa_sudo.create_uid.lang
        return request.render('pao_globalgap_fans.globalgap_application_portal_template', 
        {
            "fanrequest": fan_sudo, 
            "print": False, 
            "urlAccept": url
        })
    
    @http.route(['/pao/fan/signature/<int:fr_id>/<string:fr_token>/accept'], type='json', auth="public", website=True)
    def portal_fan_signature_accept(self, fr_id, fr_token, name=None, signature=None):
        try:
           fan_sudo = self._document_check_access('pao.globalgap.fans.request', int(fr_id), access_token=str(fr_token))
        except (AccessError, MissingError):
            return request.redirect('/')
        


        
        zone = fan_sudo.create_uid.tz
        requested_tz = pytz.timezone(zone)
        today = requested_tz.fromutc(datetime.utcnow())

        signature_date = today
        fan_sudo.write(
            {
                "signature": signature, 
                "signature_name": name, 
                "signature_date": signature_date,
                "request_status": "signed",
            }
        )
        lang = fan_sudo.capturist_id.lang or fan_sudo.create_uid.lang
        fan_sudo.with_context(lang=lang)
        old_attachment_id = None

        """

            filename = "%s-%s.%s" % (rn_sa.name,rn_sa.organization_name, "pdf")
            #pdf = request.env.ref('pao_sign_sa.report_service_agreements').sudo()._render_qweb_pdf([sa_id.id], data= {"values": rn_sa, "print": True})[0]
            pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf('pao_sign_sa.report_service_agreements', [sa_id], data= {"values": rn_sa, "print": True})[0]
            attachment = request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'datas': base64.b64encode(pdf),
                    'res_model': 'pao.sign.sa.agreements.sent',
                    'res_id': sa_id,
                    'type': 'binary',  # override default_type from context, possibly meant for another model!
                })
            attachment_list.append(attachment.id)
        


        """




        filename = "GLOBALGAP_Application_%s_%s.%s" % (fan_sudo.title,fan_sudo.organization_id.name, "pdf")
        pdf = request.env['ir.actions.report'].sudo()._render_qweb_pdf('pao_globalgap_fans.globalgap_application_report', [fr_id], data= {"fanrequest": fan_sudo,"print": True})[0]
        #pdf = request.env.ref('pao_globalgap_fans.globalgap_application_report').sudo()._render_qweb_pdf([fan_sudo], data= {"fanrequest": fan_sudo,"print": True})[0]
        attachment = request.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': base64.b64encode(pdf),
            'res_model': 'pao.globalgap.fans.request',
            'res_id': fan_sudo.id,
            'type': 'binary',  # override default_type from context, possibly meant for another model!
        })
        if fan_sudo.attachment_id:
            old_attachment_id = fan_sudo.attachment_id.id

        fan_sudo.write({"attachment_id": attachment.id})

        if not attachment.access_token:
            token = attachment._generate_access_token()
            attachment.write({"access_token": token})
        
        if old_attachment_id:
            request.env['ir.attachment'].sudo().search([("id","=",old_attachment_id),("res_id","=",fan_sudo.id),("res_model","=","pao.globalgap.fans.request")]).unlink()
        """
        mention_html = f'<a href="#" data-oe-model="res.users" data-oe-id="{fan_sudo.create_uid.id}">@{fan_sudo.create_uid.name}</a>'
        request_link = ('<a href="#" data-oe-model="pao.globalgap.fans.request" data-oe-id="%(request_id)d">%(name)s</a>'
                                ) % {'name': fan_sudo.title, 'request_id': fan_sudo.id}
        message = _('Hello %(mention_html)s, the request %(request_link)s has been signed.'
                    ) % {'request_link': request_link, 'mention_html': mention_html}
        message_id = fan_sudo.message_post(
            body=message,
            partner_ids=[fan_sudo.create_uid.partner_id.id],
        )

        fan_sudo.message_notify(
            message_id=message_id.id,
        )
        """
        
        fan_sudo.set_signature_message()



        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'force_refresh': True,
            'redirect_url':  url_join(base_url, '/pao/fillout/fans/message/signed/%s/%s' % (fr_id, fr_token))
        }

    @http.route(['/pao/fillout/fans/message/signed/<int:fan_id>/<string:fan_token>'], type='http', auth="public", website=True)
    def portal_fill_out_fans_message_signed(self, fan_id=False, fan_token=None, **kw):
        try:
           fan_sudo = self._document_check_access('pao.globalgap.fans.request', int(fan_id), access_token=str(fan_token))
        except (AccessError, MissingError):
            return request.redirect('/')
        
        url = request.env['ir.config_parameter'].sudo().get_param('web.base.url') 
        documents = []
        documents.append({"name": fan_sudo.attachment_id.name, "url": url+"/web/content/"+str(fan_sudo.attachment_id.id)+"?download=true&access_token="+str(fan_sudo.attachment_id.access_token)})
        return request.render(
            'pao_globalgap_fans.globalgap_fan_signed_page_view', {"documents": documents}
        )

    @http.route(['/pao/fillout/fans/message/<int:fan_id>/<string:fan_token>'], type='http', auth="public", website=True)
    def portal_fill_out_fans_message(self, fan_id=False, fan_token=None, **kw):
        try:
           fan_sudo = self._document_check_access('pao.globalgap.fans.request', int(fan_id), access_token=str(fan_token))
        except (AccessError, MissingError):
            return request.redirect('/')
        
        return request.render(
            'pao_globalgap_fans.globalgap_fan_registered_page_view', {}
        )
    

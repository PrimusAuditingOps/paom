
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

    """
    @http.route(['/sign/sa/<int:sa_id>/<string:sa_token>/accept'], type='json', auth="public", website=True)
    def portal_sa_accept(self, sa_id, sa_token, name=None, signature=None):
        try:
            sa_sudo = self._document_check_access('pao.sign.sa.agreements.sent', sa_id, access_token=sa_token)
        except (AccessError, MissingError):
            return request.redirect('/')
        
        lang = sa_sudo.signer_id.lang or sa_sudo.create_uid.lang
        sa_sudo.with_context(lang=lang)
        zone = sa_sudo.create_uid.tz
        requested_tz = pytz.timezone(zone)
        today = requested_tz.fromutc(datetime.utcnow())

        signature_date = today
        sa_sudo.write({"signature": signature, "signer_name": name, "signature_date": signature_date})

        
        attachment_list = []
        for rn_sa in sa_sudo.registration_number_to_sign_ids:
            

            filename = "%s-%s.%s" % (rn_sa.name,rn_sa.organization_name, "pdf")
            pdf = request.env.ref('pao_sign_sa.report_service_agreements').sudo()._render_qweb_pdf([sa_id], data= {"values": rn_sa, "print": True})[0]
            attachment = request.env['ir.attachment'].sudo().create({
                    'name': filename,
                    'datas': base64.b64encode(pdf),
                    'res_model': 'pao.sign.sa.agreements.sent',
                    'res_id': sa_id,
                    'type': 'binary',  # override default_type from context, possibly meant for another model!
                })
            attachment_list.append(attachment.id)
        
        #_logger.error(request.httprequest.remote_addr) 
        #_logger.error(request.session['geoip'].get('latitude') or 0.0)
        #_logger.error(request.session['geoip'].get('longitude') or 0.0)
        sa_sudo.write({"attachment_ids": [(6, 0, attachment_list)], "document_status": "sign"})
        msg = "Se ha firmado el acuerdo " + sa_sudo.title
        notification_ids = []
        notification_ids.append((0,0,{
            'res_partner_id':sa_sudo.create_uid.id,
            'notification_type':'inbox'
        }))
        sa_sudo.sale_order_id.message_post(body=msg)
    
        #.message_post(body=msg, partner_ids=[sa_sudo.create_uid.id]) 
        #sa_sudo.write({'signature_name': name, 'signature': signature, 'document_status': 'sign'})
        #signature_date 


        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return {
            'force_refresh': True,
            'redirect_url':  url_join(base_url, '/sign/sa/%s/%s' % (sa_id, sa_token))
        }
    """
    @http.route(['/pao_get_geolocation'], type='json', auth='public', methods=['POST'])
    def pao_get_geolocation(self, fan_id=False, fan_token=None, street=None, zip=None, city=None, state=None, country=None, **kwargs):
        latitude = 0.00
        longitude = 0.00
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', int(fan_id), access_token=str(fan_token))
            geo_obj = request.env['base.geocoder'].sudo()
            search = geo_obj.geo_query_address(street=street, zip=zip, city=city, state=state, country=country)
            result = geo_obj.geo_find(search, force_country=country)
            if result[0] and result[1]:
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
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        cities = request.env['res.city'].sudo().search([])
        versions = request.env['pao.globalgap.version'].sudo().search([])
        certificationOptions = request.env['pao.globalgap.certification.option'].sudo().search([])
        
        globalgapversion = request.env['pao.globalgap.organization'].sudo()._fields['globalgap_version'].selection
        certificationoption = request.env['pao.globalgap.organization'].sudo()._fields['certification_option'].selection
        evaluationtype = request.env['pao.globalgap.organization'].sudo()._fields['evaluation_type'].selection
        rightsofaccess = request.env['pao.globalgap.organization'].sudo()._fields['rights_of_access'].selection
        addons = request.env['pao.globalgap.addon'].sudo().search([])
        _logger.error(fan_sudo.organization_id.addons_ids)
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
            }
        )


    @http.route(['/pao/fillout/fans/products'], type='http', auth='public', methods=['POST'], website=True)
    def portal_fans_save_organization(self, fr_token, fr_id, plmx, ggn, globalgap_version, 
    certification_option, evaluation_type, name, address, city,state, country,
    zip, telephone, email, gln, vat, previous_cb, latitude, longitude, contact_name, contact_position,
    contact_telephone, contact_email, rights_of_access,addons, **kw):

        _logger.error("Entroons")
        try:
            fr_sudo = self._document_check_access('pao.globalgap.fans.request', int(fr_id), access_token=str(fr_token))
        except (AccessError, MissingError):
            return request.redirect('/')

       
        addon_list = []
        if addons != "":
            _logger.error("Entro a addons")
            addon_list = list(addons.split(","))
        organization_data = {
            "name": name,
            "plmx": plmx,
            "ggn": ggn,
            "version_id": globalgap_version,
            "certification_option_id": certification_option, 
            "addons_ids": [(6, 0, addon_list)],
            "evaluation_type": str(evaluation_type),
            "address": address,
            "city_id": city,
            "state_id": state,
            "country_id": country,
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

        return request.redirect('/pao/fillout/fans/production_site/' + fr_id + '/' + fr_token)

    @http.route(['/pao/fillout/fans/production_site/<int:fan_id>/<string:fan_token>'], type='http', auth="public", website=True)
    def portal_fill_out_fans_production_site(self, fan_id=False, fan_token=None, **kw):
        
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', fan_id, access_token=fan_token)
        except (AccessError, MissingError):
            return request.redirect('/')
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        cities = request.env['res.city'].sudo().search([])
        products = request.env['servicereferralagreement.auditproducts'].sudo().search([])
        certificate = request.env['pao.globalgap.production.site.product'].sudo()._fields['to_certificate'].selection
        pppo = request.env['pao.globalgap.production.site.product'].sudo()._fields['parallel_production_or_property'].selection
        production_sites_list = []
        for rec in fan_sudo.organization_id.production_site_ids:
            product_list = []
            for p in rec.product_ids:
                product_obj = {
                    "product": p.product_id.name, 
                    "hectareas": p.hectares_in_production, 
                    "certify": p.to_certificate, 
                    "pppo": p.parallel_production_or_property, 
                    "productid": p.product_id.id
                }
                product_list.append(product_obj)
            site_data = {
                "name": rec.name, 
                "type_name": dict(request.env['pao.globalgap.production.site'].sudo()._fields['type'].selection).get(rec.type), 
                "type": rec.type, 
                "address": rec.address, 
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
        _logger.error(production_sites_list)
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
                "pppo": pppo,
                "production_sites": json.dumps(production_sites_list),
            }
        )
    
    @http.route(['/pao/fillout/fans/production_site_phu'], type='http', auth='public', methods=['POST'], website=True)
    def portal_fans_save_production_sites(self, cr_token, cr_id, sites, **kw):
        try:
            fr_sudo = self._document_check_access('pao.globalgap.fans.request', int(cr_id), access_token=str(cr_token))
        except (AccessError, MissingError):
            return request.redirect('/')
        product_ids_list = []
        production_site = json.loads(sites)  
        _logger.error(production_site)
        request.env['pao.globalgap.production.site'].sudo().search([("organization_id","=",fr_sudo.organization_id.id)]).unlink()
        for obj in production_site:
            production_data = {
                "organization_id": fr_sudo.organization_id.id,
                "name": obj["name"],
                "type": obj["type"],
                "address": obj["address"],
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
                product_ids_list.append(product["productid"])
                product_data = {
                    "production_site_id": production.id,
                    "parallel_production_or_property": product["pppo"],
                    "to_certificate": product["certify"],
                    "hectares_in_production": product["hectareas"],
                    "product_id": product["productid"],
                }
                product = request.env['pao.globalgap.production.site.product'].sudo().create(product_data)
                
                #domain_create_product = [("organization_id","=",fr_sudo.organization_id.id),("product_id","=",product["productid"])]
                _logger.error(product_ids_list)
                #rec_product_information = request.env['pao.globalgap.production.site.product.information'].sudo().search(domain_create_product)
                #if not rec_product_information:
                #    request.env['pao.globalgap.production.site.product.information'].sudo().create({"product_id": product["productid"]})
            
            for p in product_ids_list:
                domain_create_product = [("organization_id","=",fr_sudo.organization_id.id),("product_id","=",p)]
                rec_product_information = request.env['pao.globalgap.production.site.product.information'].sudo().search(domain_create_product)
                if not rec_product_information:
                    request.env['pao.globalgap.production.site.product.information'].sudo().create({"product_id": p, "organization_id":fr_sudo.organization_id.id})

            domain_product = [("organization_id","=",fr_sudo.organization_id.id), ("product_id","not in",product_ids_list)]
            request.env['pao.globalgap.production.site.product.information'].sudo().search(domain_product).unlink()
           

        return request.redirect('/pao/fillout/fans/production_information/' + str(cr_id) + '/' + cr_token)

    
    @http.route(['/pao/fillout/fans/production_information/<int:fan_id>/<string:fan_token>'], type='http', auth="public", website=True)
    def portal_fill_out_fans_product_information(self, fan_id=False, fan_token=None, **kw):
        
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', fan_id, access_token=fan_token)
        except (AccessError, MissingError):
            return request.redirect('/')
        return request.render(
            'pao_globalgap_fans.fans_portal_template_product_information', 
            {
                "data": fan_sudo.organization_id, 
                "id": fan_id,
                "token": fan_token,
                "back_url": "/pao/fillout/fans/production_site/" +str(fan_id) + "/" + fan_token,
            }
        )

    @http.route(['/pao/fan/product_information'], type='json', auth='public', methods=['POST'])
    def pao_fan_product_information(self, fan_id=False, fan_token=None, **kwargs):
        data = []
        try:
            fan_sudo = self._document_check_access('pao.globalgap.fans.request', int(fan_id), access_token=str(fan_token))
            for rec in fan_sudo.organization_id.product_information_ids
                countries = []
                for c in rec.countries_of_products:
                    countries.append(c.id)
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
                        "organization_buys_product": rec.organization_buys_product,
                        "estimated_yield_in_tons": rec.estimated_yield_in_tons,
                        "dates_harvest_estimated": rec.dates_harvest_estimated,
                        "countries_of_products": countries,
                    }
                )
        except (AccessError, MissingError):
            data = []

        
        return{
            'data': data,
        }
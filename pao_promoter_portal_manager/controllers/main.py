from odoo import http, _
from odoo.http import request
from logging import getLogger

_logger = getLogger(__name__)

class ExternalImplements(http.Controller):
    
    @http.route('/external-implementers', auth="public", website=True)
    def external_implements(self):

        data = []
        domain = [('website_published','=',True)]
        promoters = request.env["pao.promoter.cv"].search(domain,order='name ASC')

        for rec in promoters:
            
            zones_list = []
            for zones in rec.work_zone_ids:
                zones_list.append(zones.name)   
            
            group_list = []
            group_image_list = []
            program_list = []
            for r in rec.service_ids:
                if r.service_group_id.id not in group_list:
                    program_list.append({'img':r.service_group_id.image, 'group': r.service_group_id.name })
                    group_list.append(r.service_group_id.id)
                    group_image_list.append(r.service_group_id.image)

            data.append({
                    'name': rec.name, 
                    'workzone': zones_list, 
                    'profiledescription': rec.promotor_description,
                    'telephone': rec.telephone,
                    'email': "mailto:" + rec.email if rec.email else None,
                    'whatsapp': "https://wa.me/" + rec.whatsapp if rec.whatsapp else None,
                    'profileimage': rec.profile_image,
                    'id': "/external-implementer/detail/" + str(rec.id),
                    'groupimages': group_image_list,
                    'programs': program_list
                }
            )
        if data:
            return request.render('pao_promoter_portal_manager.promoter_profiles',{'implementerdata': data})
        else:
            return request.redirect("/")
            
    @http.route('/external-implementer/detail/<int:promotorid>', auth="public", website=True)
    def external_implements_detail(self, promotorid):
        
        data = {}
        domain = [('id','=',promotorid),('website_published','=',True)]
        promoters = request.env["pao.promoter.cv"].search(domain)

        for rec in promoters:
            zones_list = []
            for zones in rec.work_zone_ids:
                zones_list.append(zones.name)   
            images_list = []
            cont = 0
            for img in rec.carousel_image_ids:
                images_list.append({
                    'img': img.image,
                    'slide': cont,
                    'active': "active" if cont == 0 else ""                    
                })
                cont += 1
            group_list = []
            for r in rec.service_ids:
                if r.service_group_id.name not in group_list:
                    group_list.append(r.service_group_id.name)

            service_obj = []
            countgroup = 0
            for group in group_list:
                accordionid = "accordion"+str(countgroup) 
                panelid = "panel"+str(countgroup)
                res_service = filter(lambda x : x['service_group_id'].name == group, rec.service_ids)
                services_list = [r.name for r in res_service]
                service_obj.append({'group': group, 'service': services_list, 'accordionid': accordionid, 'panelid': panelid})
                countgroup += 1

            history_list = []
            reverse = 0
            for r in rec.history_block_ids:

                history_list.append({'year': r.name, 'text': r.history_text, 'reverse': 'flex-row-reverse' if reverse == 1 else 'flex-row'})

                reverse = 1 if reverse == 0 else 0

            data = {
                    'name': rec.name,
                    'company': rec.company_name,
                    'image': rec.company_image if rec.company_image else rec.profile_image, 
                    'profession': rec.profession, 
                    'workzone': zones_list, 
                    'telephone': rec.telephone,
                    'email': rec.email,
                    'emailurl': "mailto:" + rec.email if rec.email else None,
                    'whatsapp': "https://wa.me/" + rec.whatsapp if rec.whatsapp else None,
                    'facebook': rec.facebook,
                    'instagram': rec.instagram,
                    'linkedin': rec.linkedin,
                    'website': rec.website,
                    'about': rec.about_html,
                    'carousel': images_list,
                    'services': service_obj,
                    'historyblock': history_list
            }
        
        if data:
            return request.render('pao_promoter_portal_manager.promoter_profiles_detail',{'data': data})
        else:
            return request.redirect("/")
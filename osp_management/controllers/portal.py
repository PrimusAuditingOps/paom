from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request

class OSPPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        # Forzamos la cuenta siempre, sin importar el optimizador de Odoo
        values['osp_count'] = request.env['osp.request'].search_count([
            ('partner_id', '=', request.env.user.partner_id.id)
        ])
        return values

    # 1. RUTA PRINCIPAL: LISTA DE FORMULARIOS
    @http.route(['/my/osp', '/my/osp/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_osps(self, page=1, **kw):
        partner = request.env.user.partner_id
        OSPRequest = request.env['osp.request']

        domain = [('partner_id', '=', partner.id)]
        osp_count = OSPRequest.search_count(domain)

        pager = portal_pager(
            url="/my/osp",
            total=osp_count,
            page=page,
            step=10
        )

        osps = OSPRequest.search(domain, limit=10, offset=pager['offset'], order='create_date desc')
        
        # Traer catálogos para el Modal "New Form"
        services = request.env['osp.service'].search([('active', '=', True)])
        templates = request.env['osp.form.template'].search([('active', '=', True)])

        values = {
            'osps': osps,
            'page_name': 'osp',
            'pager': pager,
            'default_url': '/my/osp',
            'services': services,
            'templates': templates,
        }
        return request.render("osp_management.portal_my_osps", values)

    # 2. RUTA: CREAR NUEVO BORRADOR (Desde el Modal)
    @http.route(['/my/osp/create'], type='http', auth="user", methods=['POST'], website=True)
    def portal_create_osp(self, service_id, template_id, **kw):
        new_osp = request.env['osp.request'].create({
            'partner_id': request.env.user.partner_id.id,
            'service_id': int(service_id),
            'form_template_id': int(template_id),
            'state': 'draft',
        })
        return request.redirect('/my/osp/form/%s' % new_osp.id)

    # 3. RUTA: DUPLICAR REGISTRO
    @http.route(['/my/osp/duplicate/<int:osp_id>'], type='http', auth="user", website=True)
    def portal_duplicate_osp(self, osp_id, **kw):
        original = request.env['osp.request'].browse(osp_id)
        if original.exists() and original.partner_id.id == request.env.user.partner_id.id:
            nuevo = original.copy({
                'state': 'draft',
                'review_status': 'pending',
                'app_azas': False,
                'audit_azas': False,
                'name': 'Copia de ' + original.name
            })
            return request.redirect('/my/osp')
        return request.redirect('/my/osp')

    # 4. RUTA: BORRAR BORRADOR
    @http.route(['/my/osp/delete/<int:osp_id>'], type='http', auth="user", website=True)
    def portal_delete_osp(self, osp_id, **kw):
        record = request.env['osp.request'].browse(osp_id)
        if record.exists() and record.partner_id.id == request.env.user.partner_id.id:
            if record.state == 'draft':
                record.unlink()
        return request.redirect('/my/osp')

    # 5. RUTA PANTALLA TEMPORAL DEL FORMULARIO (Esperando PDFs)
    @http.route(['/my/osp/form/<int:osp_id>'], type='http', auth="user", website=True)
    def portal_osp_form(self, osp_id, **kw):
        record = request.env['osp.request'].browse(osp_id)
        if not record.exists() or record.partner_id.id != request.env.user.partner_id.id:
            return request.redirect('/my/osp')
            
        return request.render("osp_management.portal_osp_form_placeholder", {'osp': record})
import base64

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request

class OSPPortal(CustomerPortal):

    # Campos "resumen" del registro que se sincronizan desde la Sección 1
    # del formulario, para que se vean directo en la lista/ficha del admin
    # sin abrir el JSON completo. Se usa desde CUALQUIER guardado que toque
    # esos datos (submit del cliente, o guardado del Administrador de OSP),
    # no solo desde el submit — de lo contrario, si el admin corrige un dato
    # de la Sección 1, la lista del admin queda desactualizada.
    def _sync_osp_summary_fields(self, record, form_data):
        vals = {}
        if form_data.get('1a_org_name'):
            vals['organization_name'] = form_data.get('1a_org_name')
        if form_data.get('1b_dba_name'):
            vals['dba_name'] = form_data.get('1b_dba_name')
        if form_data.get('1c_address'):
            vals['street'] = form_data.get('1c_address')
        if form_data.get('1d_city'):
            vals['city'] = form_data.get('1d_city')
        if form_data.get('1f_zip'):
            vals['zip_code'] = form_data.get('1f_zip')

        state_id = form_data.get('1e_state')
        if state_id:
            vals['state_id'] = int(state_id)

        country_id = form_data.get('1g_country')
        if country_id:
            vals['country_id'] = int(country_id)

        if vals:
            record.write(vals)

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'osp_count' in counters:
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

    # 5. RUTA PANTALLA DEL FORMULARIO (cliente dueño, o Administrador de OSP)
    @http.route(['/my/osp/form/<int:osp_id>'], type='http', auth="user", website=True)
    def portal_osp_form(self, osp_id, **kw):
        record = request.env['osp.request'].browse(osp_id)
        if not record.exists():
            return request.redirect('/my/osp')

        is_owner = record.partner_id.id == request.env.user.partner_id.id
        is_admin = request.env.user.has_group('osp_management.group_osp_administrator')

        # Solo el dueño (cliente de portal) o un Administrador de OSP pueden entrar
        if not is_owner and not is_admin:
            return request.redirect('/my/osp')

        admin_editing = is_admin and not is_owner
        # El cliente SIEMPRE puede seguir editando/guardando su formulario,
        # incluso después de haber hecho Submit (y el admin, por supuesto,
        # también). "submitted" ya no implica solo-lectura: solo indica que
        # el registro es visible para el Administrador de OSP. Ver
        # CONTEXT.md punto 6 para el detalle de esta decisión.
        readonly = False

        # Si el código técnico es 'form_crop', abrimos la plantilla oficial
        if record.form_template_id.technical_code == 'form_crop':
            countries = request.env['res.country'].search([], order='name asc')
            states = request.env['res.country.state'].search([], order='name asc')
            # Adjuntos ya subidos (punto 6): se listan para el cliente (dueño)
            # y para el Administrador de OSP; se leen con sudo() porque el
            # acceso real ya se validó arriba (is_owner / is_admin).
            attachments = request.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'osp.request'),
                ('res_id', '=', record.id),
            ], order='create_date desc')
            return request.render("osp_management.portal_osp_form_crop", {
                'osp': record,
                'countries': countries,
                'states': states,
                'is_admin': admin_editing,
                'readonly': readonly,
                'attachments': attachments,
                # El cliente dueño siempre puede subir/borrar adjuntos, sin
                # importar el estado (mismo criterio que la edición del
                # formulario en general — ver CONTEXT.md punto 6).
                'can_upload': is_owner and not admin_editing,
            })

        # Para otros formularios aún no construidos:
        return request.render("osp_management.portal_osp_form_placeholder", {'osp': record})

    # 6. RUTA AJAX PARA GUARDAR EL JSON EN SEGUNDO PLANO
    @http.route(['/my/osp/save/<int:osp_id>'], type='json', auth="user", methods=['POST'], website=True)
    def portal_save_osp(self, osp_id, form_data, is_submit=False, **kw):
        record = request.env['osp.request'].browse(osp_id)
        if not record.exists():
            return {'success': False}

        is_owner = record.partner_id.id == request.env.user.partner_id.id
        is_admin = request.env.user.has_group('osp_management.group_osp_administrator')
        admin_editing = is_admin and not is_owner

        if not is_owner and not admin_editing:
            return {'success': False}

        # El cliente SIEMPRE puede guardar/editar, sin importar el estado
        # del registro (draft o submitted) — ver CONTEXT.md punto 6.
        # "Save progress" sobre un formulario ya submitted queda guardado
        # únicamente en form_data (privado, no toca los campos resumen ni
        # notifica al admin) hasta que el cliente vuelva a hacer Submit.
        record.write({'form_data': form_data})

        if admin_editing:
            # El administrador nunca hace "submit": solo guarda cambios. Se
            # sincronizan igual los campos resumen (si tocó la Sección 1),
            # para que la lista del admin no quede desactualizada, y queda
            # registrado en el chatter para diferenciarlo de lo que
            # originalmente envió el cliente.
            self._sync_osp_summary_fields(record, form_data)
            record.message_post(
                body=_("El Administrador de OSP (%s) modificó el formulario web.") % request.env.user.name
            )
            return {'success': True}

        # A partir de aquí: flujo normal del cliente (dueño del registro)
        if is_submit:
            was_submitted = record.state == 'submitted'

            # Cada submit sincroniza los campos "resumen" con lo más
            # reciente de la Sección 1, y (re)marca el registro como
            # submitted para que sea visible en la lista del admin.
            self._sync_osp_summary_fields(record, form_data)
            record.write({'state': 'submitted'})

            # --- Notificación al Administrador de OSP (punto 4) ---
            # Se registra en el chatter del registro y, además, se manda
            # como notificación (needaction) a todos los usuarios del grupo
            # "Administrador de OSP", lo cual hace aparecer el aviso en la
            # campanita (icono de notificaciones) de su perfil de Odoo,
            # sin necesidad de que ya sigan el registro.
            verb = _("actualizó y volvió a enviar (submit)") if was_submitted else _("envió por primera vez (submit)")
            log_body = _("El cliente de portal %(partner)s %(verb)s el formulario '%(template)s'.") % {
                'partner': record.partner_id.name or request.env.user.name,
                'verb': verb,
                'template': record.form_template_id.name or record.form_template_id.technical_code or '',
            }

            # sudo(): quien llama esta ruta es el CLIENTE de portal, que no
            # tiene permiso de lectura sobre res.users (ni falta que le
            # hace) — resolver a qué administradores notificar es plomería
            # interna. Sin este sudo(), el submit entero fallaba con un
            # AccessError silencioso para el cliente (bug detectado 17/ago:
            # "Save progress" funcionaba porque no pasa por aquí, pero
            # "Submit" sí, y reventaba en este punto).
            admin_group = request.env.ref('osp_management.group_osp_administrator', raise_if_not_found=False)
            admin_partners = admin_group.sudo().users.partner_id if admin_group else request.env['res.partner']

            if admin_partners:
                record.sudo().message_notify(
                    partner_ids=admin_partners.ids,
                    subject=_("OSP %s") % (record.name or ''),
                    body=log_body,
                )
            else:
                # Sin destinatarios de campanita disponibles: al menos deja rastro en el chatter.
                record.sudo().message_post(body=log_body)

        return {'success': True}

    # 7. RUTA: SUBIR ARCHIVOS ADJUNTOS (punto 6)
    # Solo el cliente dueño del registro (sin importar el estado: draft o
    # submitted — mismo criterio que la edición del formulario en general).
    # Cada archivo se guarda como ir.attachment normal ligado al registro;
    # el widget de "Archivos Adjuntos" (icono de clip) del admin en el
    # backend ya los muestra automáticamente sin ningún código adicional.
    @http.route(['/my/osp/upload/<int:osp_id>'], type='http', auth="user", methods=['POST'], website=True)
    def portal_upload_osp_attachment(self, osp_id, **kw):
        record = request.env['osp.request'].browse(osp_id)
        if not record.exists():
            return request.redirect('/my/osp')

        is_owner = record.partner_id.id == request.env.user.partner_id.id
        if is_owner:
            files = request.httprequest.files.getlist('osp_files')
            for uploaded_file in files:
                if not uploaded_file or not uploaded_file.filename:
                    continue
                request.env['ir.attachment'].sudo().create({
                    'name': uploaded_file.filename,
                    'datas': base64.b64encode(uploaded_file.read()),
                    'res_model': 'osp.request',
                    'res_id': record.id,
                    'description': _("Subido por el cliente vía portal (%s)") % request.env.user.name,
                })

        return request.redirect('/my/osp/form/%s#sec21' % osp_id)

    # 8. RUTA: BORRAR UN ARCHIVO ADJUNTO YA SUBIDO (dueño, cualquier estado)
    @http.route(['/my/osp/attachment/delete/<int:attachment_id>'], type='http', auth="user", website=True)
    def portal_delete_osp_attachment(self, attachment_id, **kw):
        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
        if attachment.exists() and attachment.res_model == 'osp.request':
            record = request.env['osp.request'].browse(attachment.res_id)
            is_owner = record.exists() and record.partner_id.id == request.env.user.partner_id.id
            if is_owner:
                osp_id = record.id
                attachment.unlink()
                return request.redirect('/my/osp/form/%s#sec21' % osp_id)
        return request.redirect('/my/osp')

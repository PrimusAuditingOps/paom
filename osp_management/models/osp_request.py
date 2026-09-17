from odoo import models, fields, api, _

from .osp_attachment_markers import ATTACHMENT_MARKERS

# ==========================================
# MODELO PRINCIPAL (FORMULARIO OSP)
# ==========================================
class OSPRequest(models.Model):
    _name = 'osp.request'
    _description = 'Organic System Plans'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string='Active', default=True, tracking=True)
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')

    # --- CATÁLOGOS ---
    service_id = fields.Many2one('osp.service', string='Required Service', tracking=True)
    form_template_id = fields.Many2one('osp.form.template', string='Type (Form)', tracking=True)
    form_version = fields.Char(related='form_template_id.version', string='Version', readonly=True)

    # --- CLIENTE Y ORGANIZACIÓN ---
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True,
                                 help="If empty, the administrator can assign the customer here.")
    organization_name = fields.Char(string='Organization', tracking=True)
    dba_name = fields.Char(string='DBA name', tracking=True)

    # --- COMPAÑÍA (multi-compañía) ---
    # Se asigna automáticamente al crearse el registro, tomada del sitio web
    # (Website > Company) por el que el cliente entró a llenar el formulario
    # — ver controllers/portal.py (portal_save_osp_new y public_osp_submit).
    # No depende de qué compañía tenga seleccionada el administrador. Los
    # registros creados antes de que este campo existiera quedan con
    # company_id vacío: por convención de Odoo, un company_id vacío es
    # visible para cualquier compañía (ver osp_request_company_rule en
    # security/osp_security.xml), así que no hace falta backfill manual.
    company_id = fields.Many2one('res.company', string='Company', tracking=True,
                                 default=lambda self: self.env.company,
                                 help="Automatically set from the website the customer submitted the "
                                      "form through. Used to scope which OSP Administrators (when "
                                      "restricted to specific companies) can see this record.")

    # --- DIRECCIÓN ---
    street = fields.Char(string='Address')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    zip_code = fields.Char(string='Zip Code')
    country_id = fields.Many2one('res.country', string='Country')

    # --- ESTATUS ---
    review_status = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Complete (Done)')
    ], string='Review Status', default='pending', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft (In Portal)'),
        ('submitted', 'Submitted')
    ], string='Portal Status', default='draft')

    # --- REFERENCIAS NUMÉRICAS ---
    app_azas = fields.Integer(string='App AZAS', tracking=True)
    audit_azas = fields.Integer(string='Audit AZAS', tracking=True)

    # ========================================================
    # --- DATOS DINÁMICOS DEL FORMULARIO (JSON) ---
    # Aquí se guardan las respuestas de la plantilla web
    # ========================================================
    form_data = fields.Json(string="Form Responses", default={})

    # --- NOTAS DEL ADMINISTRADOR ---
    notes = fields.Html(string='Internal Notes')

    # --- CONTEO DE ADJUNTOS (Para el botón inteligente) ---
    attachment_count = fields.Integer(compute='_compute_attachment_count', string="Attachments")

    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])

    @api.model_create_multi
    def create(self, vals_list):
        # El título "New" (default del campo name) no dice nada útil en la
        # lista/ficha del admin. Como los registros solo nacen desde el
        # portal (portal_create_osp), ya siempre traen service_id y
        # form_template_id al crearse: se arma el nombre a partir de esos
        # dos catálogos, ej. "NOP/USDA - Crop".
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                service = self.env['osp.service'].browse(vals['service_id']) if vals.get('service_id') else None
                template = self.env['osp.form.template'].browse(vals['form_template_id']) if vals.get('form_template_id') else None
                parts = [p for p in [service and service.name, template and template.name] if p]
                if parts:
                    vals['name'] = ' - '.join(parts)
        return super().create(vals_list)

    # --- ACCIONES PARA LA BARRA DE ESTADO ---
    def action_set_done(self):
        for record in self:
            record.write({'review_status': 'done'})

    def action_set_pending(self):
        for record in self:
            record.write({'review_status': 'pending'})

    # OSP Administrator y OSP User tienen el mismo trato funcional para ver
    # y editar formularios OSP — la única diferencia entre ambos grupos es
    # el menú de Configuración (ver security/osp_security.xml y
    # views/osp_menu_views.xml). Mismo criterio que
    # controllers/portal.py:_is_osp_staff() (duplicado aquí porque este
    # método corre en contexto de modelo, sin acceso a `request`).
    def _is_osp_staff(self):
        user = self.env.user
        return user.has_group('osp_management.group_osp_administrator') or user.has_group('osp_management.group_osp_user')

    # Checklist de recordatorio de adjuntos pendientes (retro de usuario
    # piloto): qué casillas "Attach .../Adjunte ..." quedaron marcadas en el
    # formulario, para mostrarlo junto al pool único de adjuntos y que el
    # cliente no tenga que recordar de memoria qué dijo que iba a subir. Se
    # usa en la pantalla pública de "Thank you" (controllers/portal.py,
    # public_osp_thankyou) — el equivalente del formulario vivo (portal, o
    # público antes de enviar) se genera aparte, 100% en el navegador (ver
    # initAttachmentChecklist() en static/src/js/osp_form.js).
    def get_pending_attachment_checklist(self):
        self.ensure_one()
        technical_code = self.form_template_id.technical_code
        markers = ATTACHMENT_MARKERS.get(technical_code, [])
        result = []
        for field_key, text in markers:
            if not self.form_data.get(field_key):
                continue
            # El field_key siempre empieza con el código de la pregunta a
            # la que pertenece (ej. "2b_certificate_attachment_needed" ->
            # "2b") — se antepone al texto, mismo criterio que
            # initAttachmentChecklist() en osp_form.js, para que el
            # cliente identifique de inmediato a cuál pregunta se refiere.
            question_code = field_key.split('_')[0]
            result.append('%s. %s' % (question_code, text))
        return result

    # Acción para abrir los adjuntos
    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }

    # Acción para abrir el formulario web (cliente o administrador, según quién lo llame)
    def action_open_portal_form(self):
        self.ensure_one()

        # Administrador de OSP: se abre INCRUSTADO dentro del backend de Odoo
        # (mismo top menu / breadcrumbs) vía un client action con iframe hacia
        # el mismo formulario web que llena el cliente. No es una copia
        # reconstruida del formulario: es el mismo, por lo que el admin ve
        # exactamente las mismas capturas y el guardado usa el mismo endpoint
        # (sincronización garantizada, cero riesgo de que ambas vistas diverjan).
        if self._is_osp_staff():
            return {
                'type': 'ir.actions.client',
                'tag': 'osp_admin_form_view',
                'name': _('Web Form: %s') % (self.name or ''),
                'target': 'current',
                'params': {'osp_id': self.id},
            }

        # Cualquier otro caso (no debería ocurrir desde este botón, pero se
        # deja como respaldo): abre la URL del portal en una pestaña nueva.
        return {
            'type': 'ir.actions.act_url',
            'url': '/my/osp/form/%s' % self.id,
            'target': 'new',
        }

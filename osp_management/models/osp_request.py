from odoo import models, fields, api

# ==========================================
# MODELO PRINCIPAL (FORMULARIO OSP)
# ==========================================
class OSPRequest(models.Model):
    _name = 'osp.request'
    _description = 'Planes de manejo orgánico'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string='Activo', default=True, tracking=True)
    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default='Nuevo')

    # --- CATÁLOGOS ---
    service_id = fields.Many2one('osp.service', string='Servicio requerido', tracking=True)
    form_template_id = fields.Many2one('osp.form.template', string='Tipo (Formulario)', tracking=True)
    form_version = fields.Char(related='form_template_id.version', string='Versión', readonly=True)

    # --- CLIENTE Y ORGANIZACIÓN ---
    partner_id = fields.Many2one('res.partner', string='Cliente', tracking=True, 
                                 help="Si está vacío, el administrador puede asignar el cliente aquí.")
    organization_name = fields.Char(string='Organización', tracking=True)
    dba_name = fields.Char(string='Sitio', tracking=True)

    # --- DIRECCIÓN ---
    city = fields.Char(string='Ciudad')
    state_id = fields.Many2one('res.country.state', string='Estado')
    zip_code = fields.Char(string='Código Postal')
    country_id = fields.Many2one('res.country', string='País')

    # --- ESTATUS ---
    review_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('done', 'Completo (Hecho)')
    ], string='Estatus de revisión', default='pending', tracking=True)

    state = fields.Selection([
        ('draft', 'Borrador (En Portal)'),
        ('submitted', 'Enviado')
    ], string='Estado en Portal', default='draft')

    # --- REFERENCIAS NUMÉRICAS ---
    app_azas = fields.Integer(string='App AZAS', tracking=True)
    audit_azas = fields.Integer(string='Audit AZAS', tracking=True)

    # ========================================================
    # --- DATOS DINÁMICOS DEL FORMULARIO (JSON) ---
    # Aquí se guardan las respuestas de la plantilla web
    # ========================================================
    form_data = fields.Json(string="Respuestas del Formulario", default={})

    # --- NOTAS DEL ADMINISTRADOR ---
    notes = fields.Html(string='Notas Internas')

    # --- CONTEO DE ADJUNTOS (Para el botón inteligente) ---
    attachment_count = fields.Integer(compute='_compute_attachment_count', string="Archivos Adjuntos")

    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])

    # --- ACCIONES PARA LA BARRA DE ESTADO ---
    def action_set_done(self):
        for record in self:
            record.write({'review_status': 'done'})

    def action_set_pending(self):
        for record in self:
            record.write({'review_status': 'pending'})
            
    # Acción para abrir los adjuntos
    def action_view_attachments(self):
        self.ensure_one()
        return {
            'name': 'Archivos Adjuntos',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }
        
    # Acción para simular el acceso al portal externo
    def action_open_portal_form(self):
        self.ensure_one()
        # En el futuro, esto retornará la URL del formulario web.
        pass
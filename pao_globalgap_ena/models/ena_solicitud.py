# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import date
from werkzeug.urls import url_join


class EnaSolicitud(models.Model):
    _name = 'ena.solicitud'
    _description = 'Evaluación No Anunciada'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'consecutivo asc'
    _rec_name = 'display_name'

    # ─── Identificación ────────────────────────────────────────────────────────
    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo'),
    )
    consecutivo = fields.Integer(
        string='Consecutivo',
        tracking=True,
    )
    anio = fields.Integer(
        string='Año',
        default=lambda self: date.today().year,
        required=True,
        tracking=True,
    )
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    # ─── Productor (liga al modelo existente pao.globalgap.organization) ───────
    organization_id = fields.Many2one(
        comodel_name='pao.globalgap.organization',
        string='Organización',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    # Campos espejo del modelo de organización (readonly, para búsqueda/reporte)
    opcion = fields.Char(
        string='Opción',
        related='organization_id.certification_option_id.name',
        store=True,
        readonly=True,
    )
    num_sitios = fields.Integer(
        string='# Sitios de producción',
        compute='_compute_production_site',
        store=True,
        readonly=True,
    )
    num_phu = fields.Integer(
        string='# PHU',
        compute='_compute_phu',
        store=True,
        readonly=True,
    )
    product_ids= fields.One2many(
        related='organization_id.product_information_ids',
        string='Producto(s)',
        readonly=True,
    )

    # ─── Campos que captura CALIDAD ────────────────────────────────────────────
    shipper = fields.Char(
        string='Shipper',
        tracking=True,
    )
    obligaciones_mayores = fields.Float(
        string='Obligaciones mayores (%)',
        digits=(5, 2),
        tracking=True,
    )
    obligaciones_menores = fields.Float(
        string='Obligaciones menores (%)',
        digits=(5, 2),
        tracking=True,
    )
    sanciones_quejas = fields.Char(
        string='Sanciones/Quejas recibidas',
        default='N/A',
        tracking=True,
    )
    justificacion = fields.Text(
        string='Justificación del muestreo',
        required=True,
        tracking=True,
    )
    auditor_finca = fields.Char(
        string='Auditor (de la finca o del SGC)',
        tracking=True,
    )
    sanciones_falta_atencion = fields.Char(
        string='Sanciones por falta de atención a ENA',
        default='N/A',
        tracking=True,
    )

    # ─── Fechas ─────────────────────────────────────────────────────────────────
    fecha_vencimiento = fields.Date(
        string='Fecha de vencimiento del certificado',
        required=True,
        tracking=True,
    )
    inicio_ventana = fields.Date(
        string='Comienzo de ventana',
        compute='_compute_inicio_ventana',
        store=True,
        readonly=True,
        help='Se calcula automáticamente: 4 meses antes del vencimiento del certificado.',
    )
    dias_para_vencer = fields.Integer(
        string='Días para vencer ventana',
        compute='_compute_dias_para_vencer',
        store=False,
    )

    coordinadora_id = fields.Many2one(
        comodel_name='res.users',
        string='Coordinadora',
        tracking=True,
        domain=[('share', '=', False)],
    )
    qa_person_id = fields.Many2one(
        comodel_name='res.users',
        string='Calidad',
        tracking=True,
        domain=[('share', '=', False)],
    )
    fecha_real_ena = fields.Date(
        string='Fecha real de la ENA',
        tracking=True,
    )
    auditor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Auditor',
        tracking=True,
        compute='_compute_auditor_id',
        store=True,
    )
    purchase_order_id = fields.Many2one(
        'purchase.order', 
        string='Orden de Compra',      
        ondelete='set null'
    )
    audit_start_date = fields.Date(
        string="Fecha Inicio de Auditoria",
        compute='_compute_audit_date',
        store=True,
    )
    audit_end_date = fields.Date(
        string="Fecha Fin de Auditoria",
        compute='_compute_audit_date',
        store=True,
    )
    comentarios = fields.Text(
        string='Comentarios',
        tracking=True,
    )
    motivo_no_realizacion = fields.Char(
        
        string='Motivo de no realización',
        tracking=True,
    )
    notificacion_enviada = fields.Boolean(
        string='Notificación enviada',
        default=False,
        tracking=True,
    )
    fecha_notificacion = fields.Date(
        string='Fecha de notificación',
        readonly=True,
    )

    request_fan_id = fields.Many2one(
        'pao.globalgap.fans.request', 
        string='Solicitud de Fan',      
        ondelete='set null'
    )
    pao_lost_reason_wizard_ids = fields.One2many(
        comodel_name='ena.lost.reason.wizard',
        inverse_name='ena_id',
        string='Lost reason wizard',
    )
 
    # ─── Estado / Etapa ──────────────────────────────────────────────────────────
    stage = fields.Selection(
        selection=[
            ('candidato', 'Candidato registrado'),
            ('asignada', 'Asignada'),
            ('notificada', 'Notificación enviada'),
            ('programada', 'Programada'),
            ('realizada', 'Realizada'),
            ('no_realizada', 'No realizada'),
        ],
        string='Etapa',
        default='candidato',
        required=True,
        tracking=True,
        group_expand='_group_expand_stages',
    )
    kanban_state = fields.Selection(
        selection=[
            ('normal', 'En proceso'),
            ('done', 'Lista'),
            ('blocked', 'Bloqueada'),
        ],
        string='Estado Kanban',
        default='normal',
        tracking=True,
    )
    color = fields.Integer(
        string='Color',
        compute='_compute_color',
        store=True,
    )
    alerta_ventana = fields.Selection(
        selection=[
            ('ok', 'En tiempo'),
            ('proximo', 'Próximo a vencer'),
            ('vencido', 'Ventana vencida'),
        ],
        string='Alerta de ventana',
        compute='_compute_alerta_ventana',
        store=True,
    )
    lost_reason_id = fields.Many2one(
        comodel_name='ena.lost.reason',
        string='Motivo de no realización',
    )
    comments = fields.Char(
        string='comentarios de no realizaciónß'
    )

    month = fields.Integer(
        compute="_compute_month",
        store=True,
    )


    # ─── Compute methods ─────────────────────────────────────────────────────────
    @api.depends("audit_start_date")
    def _compute_month(self):
        for rec in self:
            rec.month = rec.audit_start_date.month if rec.audit_start_date else False

    @api.depends('purchase_order_id','purchase_order_id.order_line')
    def _compute_audit_date(self):
        for rec in self:
            rec.audit_start_date = None
            rec.audit_end_date = None
            if rec.purchase_order_id:
                for line in rec.purchase_order_id.order_line.filtered(lambda l: l.service_start_date).sorted(lambda l: l.service_start_date):
                    rec.audit_start_date = line.service_start_date
                    rec.audit_end_date = line.service_end_date
                    break
                if rec.audit_start_date:
                    break

    @api.depends('purchase_order_id','purchase_order_id.partner_id','purchase_order_id.assessment_id')
    def _compute_auditor_id(self):
        for rec in self:
            rec.auditor_id = None
            if rec.purchase_order_id:
                rec.auditor_id =  rec.purchase_order_id.assessment_id.id if rec.purchase_order_id.assessment_id else rec.purchase_order_id.partner_id.id                

    @api.depends('organization_id', 'consecutivo', 'anio')
    def _compute_display_name(self):
        for rec in self:
            org = rec.organization_id.name if rec.organization_id else _('Sin productor')
            rec.display_name = f"[{rec.anio}-{rec.consecutivo:03d}] {org}"

    @api.depends('fecha_vencimiento')
    def _compute_inicio_ventana(self):
        for rec in self:
            if rec.fecha_vencimiento:
                rec.inicio_ventana = rec.fecha_vencimiento - relativedelta(months=4)
            else:
                rec.inicio_ventana = False

    @api.depends('fecha_vencimiento')
    def _compute_dias_para_vencer(self):
        hoy = date.today()
        for rec in self:
            if rec.fecha_vencimiento:
                delta = rec.fecha_vencimiento - hoy
                rec.dias_para_vencer = delta.days
            else:
                rec.dias_para_vencer = 0

    @api.depends('stage', 'inicio_ventana', 'fecha_vencimiento')
    def _compute_alerta_ventana(self):
        hoy = date.today()
        for rec in self:
            if rec.stage in ('realizada', 'no_realizada', 'programada'):
                rec.alerta_ventana = 'ok'
                continue
            if not rec.fecha_vencimiento:
                rec.alerta_ventana = 'ok'
                continue
            dias = (rec.fecha_vencimiento - hoy).days
            if dias < 0:
                rec.alerta_ventana = 'vencido'
            elif dias <= 30:
                rec.alerta_ventana = 'proximo'
            else:
                rec.alerta_ventana = 'ok'

    @api.depends('stage', 'alerta_ventana')
    def _compute_color(self):
        """
        Colores Kanban:
        10 = verde (realizada/programada)
        3  = amarillo (no realizada)
        1  = rojo (vencido / bloqueado)
        6  = naranja (próximo a vencer)
        0  = sin color
        """
        for rec in self:
            if rec.alerta_ventana == 'vencido':
                rec.color = 1
            elif rec.alerta_ventana == 'proximo':
                rec.color = 6
            else:
                rec.color = 0

    # ─── Group expand para Kanban ─────────────────────────────────────────────
    @api.model
    def _group_expand_stages(self, stages, domain, order):
        return [
            'candidato', 'asignada', 'notificada', 'programada', 'no_realizada',
        ]

    # ─── Secuencia automática ─────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('ena.solicitud') or _('Nuevo')
            # Calcular consecutivo dentro del año
            anio = vals.get('anio', date.today().year)
            ultimo = self.search([('anio', '=', anio)], order='consecutivo desc', limit=1)
            vals['consecutivo'] = (ultimo.consecutivo + 1) if ultimo else 1
        return super().create(vals_list)

    # ─── Botones de acción ────────────────────────────────────────────────────
    def action_asignar_coordinadora(self):
        self.ensure_one()
        if not self.coordinadora_id:
            raise ValidationError(_('Debe asignar una coordinadora antes de continuar.'))
        self.stage = ''

    def action_enviar_notificacion(self):
        self.ensure_one()
        template = None
        if not self.request_fan_id:
            existing_organization = self.env["pao.globalgap.fans.request"].search(
                [("organization_id", "=", self.organization_id.id),],
                order="create_date desc",
                limit=1,)
            if existing_organization:
                request_fan = self.env["pao.globalgap.fans.request"].create(
                    {
                        "organization_id": existing_organization.organization_id.id,
                        "capturist_id": existing_organization.capturist_id.id,
                        "request_status": "sent",
                    }
                )
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                form_url = url_join(base_url, '/pao/fillout/fans/%s/%s' % (request_fan.id, request_fan.access_token))
                request_fan.write({"request_url": form_url})
                self.write({"request_fan_id": request_fan.id})



        

    
        template = self.env.ref(
            'pao_globalgap_ena.mail_template_ena_notificacion',
            raise_if_not_found=False
        )
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': self._name,
                'default_res_ids': [self.id],
                'default_composition_mode': 'comment',
                'default_template_id': template.id if template else False,
                'force_email': True,
            }
        }
   


    def action_marcar_no_realizada(self):
        self.ensure_one()
        
        self.stage = 'no_realizada'
    
    def action_restore(self):
        self.ensure_one()
        self.stage = 'asignada'

    @api.depends('organization_id')
    def _compute_production_site(self):
        for rec in self:
            rec.num_sitios = len(
                rec.organization_id.production_site_ids.filtered(lambda l: l.type == '1')
            )
    @api.depends('organization_id')
    def _compute_phu(self):
        for rec in self:
            rec.num_phu = len(
                rec.organization_id.production_site_ids.filtered(lambda l: l.type == '2')
            )
    

    def write(self, vals):
        user_changed = 'coordinadora_id' in vals
        res = super().write(vals)
        activity_type = self.env.ref('mail.mail_activity_data_todo')
        if user_changed:
            

            for record in self:
                act_date = date.today() if record.inicio_ventana < date.today() else record.inicio_ventana

                if record.coordinadora_id:
                    if record.stage == "candidato":
                        record.stage = 'asignada'

                    existing_activity = self.env["mail.activity"].search([
                    ("res_model", "=", "ena.solicitud"),
                    ("res_id", "=", record.id),
                    ("summary", "=", "Programar auditoria no anunciada"),
                    ], limit=1)
                    if not existing_activity:
                        record.activity_schedule(
                            activity_type_id=activity_type.id,
                            date_deadline=act_date,
                            summary="Programar auditoria no anunciada",
                            note=_(
                                "Favor de subir dar seguimiento a esta auditoria no anunciada."
                            ),
                            user_id=record.coordinadora_id.id,
                        )
        if 'stage' in vals:
            if vals.get('stage') and vals.get('stage') == "realizada":
                for record in self:
                    rec_activity = self.env['mail.activity'].search([
                        ("res_model", "=", "ena.solicitud"),
                        ("res_id", "=", record.id),
                        ("summary", "=", "Programar auditoria no anunciada"),
                        ('activity_type_id', '=', activity_type.id),
                    ])
                    for r in rec_activity:
                        r.action_done()

        return res
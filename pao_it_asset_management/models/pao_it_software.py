from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .hr_company_label import _company_label
from .pao_it_asset import check_analytic_distribution_total

# Días antes del fin del periodo en que la suscripción pasa a "por
# renovar" (auto-renew) o "por vencer" (sin auto-renew).
SUBSCRIPTION_EXPIRING_DAYS = 10

SUBSCRIPTION_STATES = [
    ('no_period', 'No Period'),
    ('active', 'Active'),
    ('renewing', 'Renewing Soon'),
    ('expiring', 'Expiring Soon'),
    ('expired', 'Expired'),
    ('cancelled', 'Cancelled'),
]


# ==========================================
# CATÁLOGO DE SOFTWARE (GLOBAL, sin compañía)
# ==========================================
class PaoItSoftware(models.Model):
    _name = 'pao.it.software'
    _description = 'Software'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    software_type_id = fields.Many2one('pao.it.software.type', string='Software Type', ondelete='restrict')
    # Texto libre a propósito: no crea contactos.
    publisher = fields.Char(string='Publisher')
    website = fields.Char(string='Website')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    subscription_ids = fields.One2many('pao.it.subscription', 'software_id', string='Subscriptions')
    subscription_count = fields.Integer(string='Subscription Count', compute='_compute_subscription_count')

    def _compute_subscription_count(self):
        for software in self:
            software.subscription_count = len(software.subscription_ids)

    def action_view_subscriptions(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'pao_it_asset_management.action_pao_it_subscription')
        action['domain'] = [('software_id', '=', self.id)]
        action['context'] = {'default_software_id': self.id, 'pao_it_show_company': True}
        return action


# ==========================================
# SUSCRIPCIÓN / LICENCIA (por compañía)
# ==========================================
# Equivale a cada fila del Excel "IT Platforms Pricing": un software + plan
# en una compañía. Sus cantidades y costos viven en los PERIODOS (ciclos de
# contrato); aquí se muestran los del periodo vigente.
class PaoItSubscription(models.Model):
    _name = 'pao.it.subscription'
    _description = 'Software Subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'analytic.mixin']
    _order = 'software_id, company_id'
    # Sin campo `name`: el nombre visible se arma (software – plan (país)) y
    # la búsqueda por nombre usa estos campos.
    _rec_names_search = ['software_id.name', 'plan']

    software_id = fields.Many2one('pao.it.software', string='Software', required=True,
                                  ondelete='restrict', tracking=True)
    software_type_id = fields.Many2one(related='software_id.software_type_id', store=True)
    plan = fields.Char(string='Plan / Edition', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True,
                                 default=lambda self: self.env.company, tracking=True)
    license_type = fields.Selection([
        ('per_user', 'Per User'),
        ('flat_fee', 'Flat Fee'),
        ('perpetual', 'Perpetual'),
    ], string='License Type', required=True, default='per_user', tracking=True)
    auto_renew = fields.Boolean(string='Auto-Renew', tracking=True)
    expected_increase_pct = fields.Float(
        string='Expected Increase at Renewal (%)',
        help="Optional. When the next period is created automatically (auto-renew), "
             "its cost is increased by this percentage.")
    description = fields.Text(string='Description')
    justification = fields.Text(string='Justification')
    notes = fields.Text(string='Notes')
    # SOLO administradores (restricción a nivel de campo: el perfil User no
    # la ve ni en formularios, listas ni exportaciones). Sin tracking, para
    # que no quede en el chatter. Nunca se guardan contraseñas (LastPass).
    license_keys = fields.Text(string='License Keys',
                               groups='pao_it_asset_management.group_it_asset_admin')

    # --- CANCELACIÓN ---
    cancelled = fields.Boolean(string='Cancelled', readonly=True, copy=False, tracking=True)
    cancel_date = fields.Date(string='Cancellation Date', readonly=True, copy=False)
    cancel_reason = fields.Text(string='Cancellation Reason', readonly=True, copy=False)

    period_ids = fields.One2many('pao.it.subscription.period', 'subscription_id', string='Periods')
    assignment_ids = fields.One2many('pao.it.license.assignment', 'subscription_id', string='Assignments')

    # --- DEL PERIODO VIGENTE ---
    current_period_id = fields.Many2one('pao.it.subscription.period', string='Current Period',
                                        compute='_compute_current_period')
    current_start_date = fields.Date(string='Current Start', compute='_compute_current_period')
    current_end_date = fields.Date(string='Current End', compute='_compute_current_period')
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_current_period')
    current_total = fields.Monetary(string='Current Period Total', currency_field='currency_id',
                                    compute='_compute_current_period')
    licenses_purchased = fields.Integer(string='Licenses Purchased', compute='_compute_current_period')
    allowed_users = fields.Integer(string='Allowed Users', compute='_compute_current_period')
    assigned_count = fields.Integer(string='Assigned Users', compute='_compute_assignment_counts')
    available_count = fields.Integer(string='Available Users', compute='_compute_assignment_counts')
    over_capacity = fields.Boolean(string='Over Capacity', compute='_compute_assignment_counts',
                                   search='_search_over_capacity')
    review_count = fields.Integer(string='Assignments to Review', compute='_compute_assignment_counts',
                                  search='_search_review_count')
    last_increase_unit_pct = fields.Float(string='Last Unit Price Increase (%)',
                                          compute='_compute_last_increase')
    last_increase_total_pct = fields.Float(string='Last Total Increase (%)',
                                           compute='_compute_last_increase')
    has_price_increase = fields.Boolean(string='Price Increased', compute='_compute_last_increase',
                                        search='_search_has_price_increase')

    state = fields.Selection(SUBSCRIPTION_STATES, string='Status', compute='_compute_state',
                             search='_search_state')

    # ==========================================
    # CÁLCULOS
    # ==========================================
    @api.depends('software_id', 'plan', 'company_id')
    def _compute_display_name(self):
        for subscription in self:
            name = subscription.software_id.name or ''
            if subscription.plan:
                name = f"{name} – {subscription.plan}"
            if subscription.company_id:
                name = f"{name} ({_company_label(subscription.company_id)})"
            subscription.display_name = name

    def _get_current_period(self, today=None):
        """Periodo que cubre hoy; si no hay, el más reciente."""
        self.ensure_one()
        today = today or fields.Date.context_today(self)
        periods = self.period_ids.sorted('start_date')
        covering = periods.filtered(
            lambda p: p.start_date <= today and (not p.end_date or p.end_date >= today))
        return covering[-1:] or periods[-1:]

    @api.depends('period_ids.start_date', 'period_ids.end_date', 'period_ids.total_amount',
                 'period_ids.licenses_purchased', 'period_ids.allowed_users')
    def _compute_current_period(self):
        for subscription in self:
            period = subscription._get_current_period()
            subscription.current_period_id = period
            subscription.current_start_date = period.start_date
            subscription.current_end_date = period.end_date
            subscription.currency_id = period.currency_id or subscription.company_id.currency_id
            subscription.current_total = period.total_amount
            subscription.licenses_purchased = period.licenses_purchased
            subscription.allowed_users = period.allowed_users

    @api.depends('assignment_ids.state', 'assignment_ids.to_review', 'period_ids.allowed_users')
    def _compute_assignment_counts(self):
        for subscription in self:
            active = subscription.assignment_ids.filtered(lambda a: a.state == 'active')
            allowed = subscription._get_current_period().allowed_users if subscription.period_ids else 0
            subscription.assigned_count = len(active)
            subscription.available_count = allowed - len(active)
            subscription.over_capacity = bool(subscription.period_ids) and len(active) > allowed
            subscription.review_count = len(active.filtered('to_review'))

    @api.depends('period_ids.unit_increase_pct', 'period_ids.total_increase_pct')
    def _compute_last_increase(self):
        for subscription in self:
            period = subscription.period_ids.filtered('increase_comparable').sorted('start_date')[-1:]
            subscription.last_increase_unit_pct = period.unit_increase_pct
            subscription.last_increase_total_pct = period.total_increase_pct
            subscription.has_price_increase = bool(period) and period.unit_increase_pct > 0

    @api.depends('cancelled', 'auto_renew', 'license_type', 'period_ids.start_date', 'period_ids.end_date')
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for subscription in self:
            subscription.state = subscription._get_state(today)

    def _get_state(self, today):
        self.ensure_one()
        if self.cancelled:
            return 'cancelled'
        if not self.period_ids:
            return 'no_period'
        if self.license_type == 'perpetual' or any(not p.end_date for p in self.period_ids):
            return 'active'
        end = max(self.period_ids.mapped('end_date'))
        if end < today:
            # Con auto-renew la tarea diaria crea el siguiente periodo; mientras
            # tanto no se considera vencida.
            return 'renewing' if self.auto_renew else 'expired'
        if end <= today + timedelta(days=SUBSCRIPTION_EXPIRING_DAYS):
            return 'renewing' if self.auto_renew else 'expiring'
        return 'active'

    # Búsquedas sobre campos calculados (volumen bajo: se evalúan en Python).
    def _search_by_python(self, predicate):
        return [('id', 'in', self.search([]).filtered(predicate).ids)]

    def _search_state(self, operator, value):
        values = value if isinstance(value, (list, tuple)) else [value]
        if operator in ('=', 'in'):
            return self._search_by_python(lambda s: s.state in values)
        if operator in ('!=', 'not in'):
            return self._search_by_python(lambda s: s.state not in values)
        raise UserError(_("Unsupported search on subscription status."))

    def _search_over_capacity(self, operator, value):
        wanted = (operator == '=') == bool(value)
        return self._search_by_python(lambda s: s.over_capacity == wanted)

    def _search_review_count(self, operator, value):
        ops = {'>': lambda a, b: a > b, '>=': lambda a, b: a >= b, '=': lambda a, b: a == b,
               '!=': lambda a, b: a != b, '<': lambda a, b: a < b, '<=': lambda a, b: a <= b}
        if operator not in ops:
            raise UserError(_("Unsupported search on assignments to review."))
        return self._search_by_python(lambda s: ops[operator](s.review_count, value))

    def _search_has_price_increase(self, operator, value):
        wanted = (operator == '=') == bool(value)
        return self._search_by_python(lambda s: s.has_price_increase == wanted)

    # ==========================================
    # VALIDACIONES / BORRADO
    # ==========================================
    @api.constrains('analytic_distribution')
    def _check_analytic_distribution_total(self):
        check_analytic_distribution_total(self)

    @api.ondelete(at_uninstall=False)
    def _unlink_only_empty(self):
        for subscription in self:
            if subscription.period_ids or subscription.assignment_ids:
                raise UserError(_(
                    "The subscription %s has periods or assignments and cannot be deleted. "
                    "Cancel it instead.", subscription.display_name))

    # ==========================================
    # ACCIONES
    # ==========================================
    def _prepare_renewal_vals(self, apply_expected_increase=False):
        """Siguiente periodo: fechas consecutivas, misma duración, mismas
        cantidades y costo (más el aumento esperado, si se pide)."""
        self.ensure_one()
        last = self.period_ids.sorted('start_date')[-1:]
        if not last:
            raise UserError(_("Register the first period of the subscription before renewing it."))
        if not last.end_date:
            raise UserError(_("The last period has no end date (perpetual license): there is nothing to renew."))
        duration = relativedelta(last.end_date + timedelta(days=1), last.start_date)
        start = last.end_date + timedelta(days=1)
        factor = 1 + (self.expected_increase_pct / 100.0) if apply_expected_increase else 1
        return {
            'subscription_id': self.id,
            'start_date': start,
            'end_date': start + duration - timedelta(days=1),
            'billing_frequency': last.billing_frequency,
            'licenses_purchased': last.licenses_purchased,
            'allowed_users': last.allowed_users,
            'currency_id': last.currency_id.id,
            'unit_cost': last.unit_cost * factor,
            'billing_amount': last.billing_amount * factor,
            'purchase_source': 'other' if last.purchase_source == 'other' else False,
            'purchase_method_id': last.purchase_method_id.id,
            'payment_details': last.payment_details,
        }

    def action_renew(self):
        self.ensure_one()
        period = self.env['pao.it.subscription.period'].create(self._prepare_renewal_vals())
        return {
            'type': 'ir.actions.act_window',
            'name': _('Renewal'),
            'res_model': 'pao.it.subscription.period',
            'res_id': period.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_cancel_subscription(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Subscription'),
            'res_model': 'pao.it.subscription.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_subscription_id': self.id},
        }

    def action_reactivate(self):
        self.write({'cancelled': False, 'cancel_date': False, 'cancel_reason': False})
        return True

    @api.model
    def _cron_auto_renew(self):
        """Tarea diaria: crea el siguiente periodo de las suscripciones con
        auto-renew cuyo último periodo ya terminó (aplica el aumento
        esperado). Se pone al corriente si faltan varios periodos."""
        today = fields.Date.context_today(self)
        subscriptions = self.sudo().search([('auto_renew', '=', True), ('cancelled', '=', False),
                                            ('license_type', '!=', 'perpetual')])
        Period = self.env['pao.it.subscription.period'].sudo()
        for subscription in subscriptions:
            for _i in range(36):  # tope de seguridad
                last = subscription.period_ids.sorted('start_date')[-1:]
                if not last or not last.end_date or last.end_date > today:
                    break
                Period.create(subscription._prepare_renewal_vals(apply_expected_increase=True))

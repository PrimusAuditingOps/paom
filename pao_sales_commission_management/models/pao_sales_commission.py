# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PaoSalesCommission(models.Model):
    _name = 'pao.sales.commission'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Sales Commission Payable'
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Folio', required=True, copy=False, readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'pao.sales.commission'
        ) or 'New',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order', string='Quotation',
        required=True, readonly=True, ondelete='cascade', index=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer',
        related='sale_order_id.partner_id', store=True, readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        related='sale_order_id.company_id', store=True, readonly=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users', string='Quote Salesperson',
        related='sale_order_id.user_id', store=True, readonly=True,
    )

    # -- Comisionista (snapshot al momento de generar el registro) --------
    promotor_id = fields.Many2one(
        comodel_name='comisionpromotores.promotor', string='Promoter',
        required=True, readonly=True,
    )
    promotor_type = fields.Selection(
        selection=[
            ('external', 'External'),
            ('sales', 'Salesperson'),
            ('coordination', 'Coordination'),
        ],
        string='Promoter Type', readonly=True,
    )
    related_user_id = fields.Many2one(
        comodel_name='res.users', string='Related User',
        readonly=True,
        
    )
    commission_percentage = fields.Float(
        string='% commission', readonly=True, digits=(5, 2),
    )

    # -- Montos -------------------------------------------------------------
    currency_cotizacion_id = fields.Many2one(
        comodel_name='res.currency', string='Currency quotation',
        related='sale_order_id.currency_id', store=True, readonly=True,
    )
    currency_mxn_id = fields.Many2one(
        comodel_name='res.currency', string='Payment Currency(MXN)',
        compute='_compute_currency_mxn_id', store=True,
    )
    commissionable_base = fields.Monetary(
        string='Commissionable Base (without taxes)', readonly=True,
        currency_field='currency_cotizacion_id',
    )
    commission_amount = fields.Monetary(
        string='Commission Amount', readonly=True,
        currency_field='currency_cotizacion_id',
    )
    applied_exchange_rate = fields.Float(
        string='Applied Exchange Rate', readonly=True, digits=(12, 6),
    )
    commission_amount_mxn = fields.Monetary(
        string='Commission Amount (MXN)', readonly=True,
        currency_field='currency_mxn_id',
    )
    reference_payment_id = fields.Many2one(
        comodel_name='account.payment', string='Reference Payment (E.R.)',
        readonly=True,
        help='Customer payment used to determine the exchange rate '
             '(it was the one with the highest amount in MXN equivalent).',
    )
    commission_line_ids = fields.Many2many(
        comodel_name='sale.order.line', string='Commissionable Product Lines',
        compute='_compute_commission_line_ids',
        help='Sale order lines this commission is actually being paid on: '
             'commissionable product, with a commission agent assigned at '
             'line level. Reflects the current state of the quotation.',
    )

    # -- Validación de servicio (sólo coordinadores) ------------------------
    requires_service_validation = fields.Boolean(
        string='Requires service validation.', 
        compute='_compute_requires_service_validation',
        store=True,
    )
    service_performed = fields.Boolean(
        string='Service Done', readonly=True,
    )
    service_performed_date = fields.Date(
        string='Service End Date', readonly=True,
    )

    # -- Estado / ciclo de pago ---------------------------------------------
    state = fields.Selection(
        selection=[
            ('pending_invoicing', 'Pending Invoicing'),
            ('pending_service', 'Pending Service (Coordinator)'),
            ('outstanding_payable', 'Outstanding / Payable'),
            ('paid', 'Paid'),
            ('under_review', 'Under Review'),
        ],
        string='State', default='pending_invoicing', tracking=True,
        readonly=True, copy=False,
    )
    generation_date = fields.Datetime(
        string='Generation Date', readonly=True,
        default=fields.Datetime.now,
    )
    payment_date = fields.Date(string='Payment Date', readonly=True, copy=False)
    paid_by = fields.Many2one(
        comodel_name='res.users', string='Paid by', readonly=True,
        copy=False,
    )
    finance_payment_reference = fields.Char(
        string='Finance Payment Reference', readonly=True, copy=False,
    )
    finance_notes = fields.Text(string='Finance Notes', copy=False)
    alert_reason = fields.Text(
        string='Alert Reason', readonly=True, copy=False,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('sale_order_uniq', 'unique(sale_order_id)',
         'A commission for this quote already exists.'),
    ]

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('sale_order_id.order_line.pao_promotor_id',
                 'sale_order_id.order_line.product_id')
    def _compute_commission_line_ids(self):
        for rec in self:
            rec.commission_line_ids = rec.sale_order_id._pao_commissionable_lines()

    @api.depends('promotor_type')
    def _compute_requires_service_validation(self):
        for rec in self:
            rec.requires_service_validation = rec.promotor_type == 'coordination'

    @api.depends()
    def _compute_currency_mxn_id(self):
        mxn = self.env['res.currency'].search([('name', '=', 'MXN')], limit=1)
        for rec in self:
            rec.currency_mxn_id = mxn

    # ------------------------------------------------------------------
    # Botones / acciones manuales
    # ------------------------------------------------------------------
    def action_view_sale(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
        }

    def action_recalculate(self):
        """Botón manual para forzar el recálculo de un registro puntual."""
        for rec in self:
            rec._update_from_sale_order(rec.sale_order_id)
        return True

    # ------------------------------------------------------------------
    # Cron: punto de entrada principal
    # ------------------------------------------------------------------
    @api.model
    def cron_generate_and_update_commissions(self):
        """Recorre las cotizaciones confirmadas con comisionista asignado y:
        1) Genera el registro de comisión si no existe.
        2) Actualiza su estado/montos si aún no está pagado.
        3) Revisa reversos/cancelaciones en registros ya generados o pagados.
        """
        domain = [
            ('state', '=', 'sale'),
            ('date_order', '>=', '2026-06-01 00:00:00'),
            ('pao_promotor_id', '!=', False),
            ('pao_promotor_id.commission_rate', '>', 0),
            ('pao_sales_commission_ids', '=', False),
            ('country_code', '=', 'MX'),
        ]
        sales = self.env['sale.order'].search(domain)
        for sale in sales:
            try:
                self._generate_for_sale_order(sale)
            except Exception:  # noqa: BLE001
                _logger.exception(
                    'Error generating commission for the sale %s',
                    sale.name,
                )

        rec_commissions = self.search(
            [('state', 'not in', ('under_review', 'paid'))]
        )
        for r in rec_commissions:
            try:
                r._update_for_sale_order()
            except Exception:  # noqa: BLE001
                _logger.exception(
                    'Error updating commission for the sale %s',
                    sale.name,
                )

        # Revisión de alertas sobre registros existentes (incluye los ya
        # pagados, para detectar reversos posteriores al pago).
        records = self.search([
            ('state', 'in', ('outstanding_payable', 'paid', 'pending_service')),
        ])
        for rec in records:
            try:
                rec._review_reverse_alert()
            except Exception:  # noqa: BLE001
                _logger.exception(
                    'Error checking commission reversal alert %s',
                    rec.name,
                )
        return True

    # ------------------------------------------------------------------
    # Generación / actualización por cotización
    # ------------------------------------------------------------------
    @api.model
    def _update_for_sale_order(self):
        lineas_comisionables = self.sale_order_id._pao_commissionable_lines()
        commissionable_base = sum(lineas_comisionables.mapped('price_subtotal'))
        if commissionable_base <= 0:
            # No hay nada comisionable en esta venta, no se genera registro.
            return

        if self.state in ('paid', 'under_review'):
            # No se recalcula automáticamente algo ya pagado o en revisión;
            # eso requiere intervención manual de finanzas.
            return

        self.commissionable_base = commissionable_base
        self.commission_amount = commissionable_base * (
            self.commission_percentage / 100.0
        )

        if not self.sale_order_id._commission_is_invoiced_and_paid():
            self.state = 'pending_invoicing'
            return

        invoices = self.sale_order_id._commission_get_invoices().filtered(
            lambda m: m.state == 'posted'
        )
        exchange_rate, better_pay = self._determine_exchange_rate(
            invoices, self.sale_order_id.company_id
        )
        self.applied_exchange_rate = exchange_rate
        self.reference_payment_id = better_pay.id if better_pay else False
        self.commission_amount_mxn = self.commission_amount * exchange_rate

        if self.promotor_type != 'coordination':
            self.state = 'outstanding_payable'
            return

        # Coordinador: validar que el servicio ya se haya realizado.
        done, end_date = self._check_service_performed(self.sale_order_id)
        self.service_performed = done
        self.service_performed_date = end_date or False
        self.state = 'outstanding_payable' if done else 'pending_service'

    @api.model
    def _generate_for_sale_order(self, sale_order):
        promotor = sale_order.pao_promotor_id
        if not promotor:
            return
        lineas_comisionables = sale_order._pao_commissionable_lines()
        commissionable_base = sum(lineas_comisionables.mapped('price_subtotal'))
        if commissionable_base <= 0:
            # No hay nada comisionable en esta venta, no se genera registro.
            return
        record = self.search(
            [('sale_order_id', '=', sale_order.id)], limit=1
        )
        if not record:
            record = self.create({
                'sale_order_id': sale_order.id,
                'promotor_id': promotor.id,
                'promotor_type': promotor.promotor_type,
                'related_user_id': promotor.user_id.id,
                'commission_percentage': promotor.commission_rate,
            })
            record._update_for_sale_order()


    def _update_from_sale_order(self, sale_order):
        """Wrapper de instancia usado por el botón 'Recalcular'."""
        self.ensure_one()
        if self.state in ('paid', 'under_review'):
            raise UserError(
                'A commission that has already been paid or is under review cannot be recalculated. '
                'Contact Finance if an adjustment is required.'
            )
        self._update_for_sale_order()

    # ------------------------------------------------------------------
    # Cálculo de tipo de cambio (pago de mayor monto en equivalente MXN)
    # ------------------------------------------------------------------
    def _get_related_payments(self, invoices):
        """Regresa los account.payment conciliados contra las líneas por
        cobrar (receivable) de las facturas indicadas."""
        if not invoices:
            return self.env['account.payment']
        receivable_lines = invoices.line_ids.filtered(
            lambda l: l.account_id.account_type in (
                'asset_receivable', 'liability_payable'
            )
        )
        partials = receivable_lines.matched_debit_ids | receivable_lines.matched_credit_ids
        other_lines = (
            partials.mapped('debit_move_id') | partials.mapped('credit_move_id')
        ) - receivable_lines
        payments = other_lines.mapped('move_id.payment_id')
        return payments.filtered(lambda p: p)

    def _determine_exchange_rate(self, invoices, company):
        """Devuelve (tipo_cambio_usd_mxn, account.payment) usando la fecha
        del pago de mayor monto, comparando los pagos ya convertidos a MXN."""
        self.ensure_one()
        mxn = self.env['res.currency'].search([('name', '=', 'MXN')], limit=1)
        usd = self.currency_cotizacion_id or self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1
        )
        if not mxn or not usd:
            _logger.warning(
                'USD/MXN currencies configured in the system were not found; '
                'the exchange rate for %s cannot be calculated',
                self.name,
            )
            return 0.0, self.env['account.payment']

        payments = self._get_related_payments(invoices)
        if not payments:
            return 0.0, self.env['account.payment']

        better_payment = self.env['account.payment']
        better_amount_mxn = -1.0
        for payment in payments:
            date = payment.date or fields.Date.context_today(self)
            amount_mxn = payment.currency_id._convert(
                payment.amount, mxn, company, date
            )
            if amount_mxn > better_amount_mxn:
                better_amount_mxn = amount_mxn
                better_payment = payment

        if not better_payment:
            return 0.0, self.env['account.payment']

        better_payment_date = better_payment.date or fields.Date.context_today(self)
        exchange_rate = usd._convert(1.0, mxn, company, better_payment_date)
        return exchange_rate, better_payment

    # ------------------------------------------------------------------
    # Validación de servicio realizado (coordinadores)
    # ------------------------------------------------------------------
    def _check_service_performed(self, sale_order):
        """Revisa las órdenes de compra relacionadas (purchase_order_id) y
        sus líneas (vía sra_sale_line_ids) para saber si el servicio
        contratado ya finalizó (service_end_date <= hoy), ignorando órdenes
        de compra canceladas.

        Devuelve (True/False, fecha_fin_relevante_o_False).
        """
        self.ensure_one()
        purchase_orders = sale_order.purchase_order_id.filtered(
            lambda po: po.state != 'cancel'
        )
        commissionable_sales_lines = sale_order._pao_commissionable_lines()
        if not purchase_orders or not commissionable_sales_lines:
            # No hay evidencia de servicio contratado: se deja pendiente
            # para revisión manual de finanzas en vez de aprobarlo solo.
            return False, False

        purchase_lines = purchase_orders.order_line.filtered(
            lambda pl: pl.sra_sale_line_ids & commissionable_sales_lines
        )
        if not purchase_lines:
            return False, False

        if any(not pl.service_end_date for pl in purchase_lines):
            return False, False

        today = fields.Date.context_today(self)
        if any(pl.service_end_date > today for pl in purchase_lines):
            return False, False

        date_max = max(purchase_lines.mapped('service_end_date'))
        return True, date_max

    # ------------------------------------------------------------------
    # Alertas por reverso/cancelación posterior a la generación o al pago
    # ------------------------------------------------------------------
    def _review_reverse_alert(self):
        self.ensure_one()
        sale = self.sale_order_id
        problem, reason = sale._commission_has_billing_issue()

        if not problem and sale.state == 'cancel':
            problem, reason = True, 'The quote/sale was cancelled.'

        if not problem and self.promotor_type == 'coordination' and \
                self.state == 'outstanding_payable':
            # Si ya se había marcado servicio realizado, pero la orden de
            # compra que lo sustentaba fue cancelada después, se re-valida.
            done, _fecha = self._check_service_performed(sale)
            if not done and self.service_performed:
                problem = True
                reason = ('The purchase order verifying the service performed '
                          'was cancelled or modified.')

        if problem:
            self.write({
                'state': 'under_review',
                'alert_reason': reason,
            })
            self.message_post(
                body=('⚠️ Commission alert: %s Review before proceeding '
                      'with the payment.') % reason
            )

# -*- coding: utf-8 -*-
from datetime import date, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models

MEXICO_CITY_TZ = pytz.timezone('America/Mexico_City')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pao_company_country_code = fields.Char(
        related='company_id.country_code', string='Company Country Code')

    customer_segment = fields.Selection([
        ('key', 'Cliente Clave'),
        ('promoter', 'Cliente de Promotor'),
        ('individual', 'Cliente Individual'),
    ], string='Segmento de Cliente', compute='_compute_customer_segment', store=True)

    sales_customer_type = fields.Selection([
        ('new', 'Cliente Nuevo'),
        ('recovered', 'Cliente Recuperado'),
        ('current', 'Cliente Actual'),
        ('lost', 'Cliente Perdido'),
    ], string='Tipo de Cliente de Venta', compute='_compute_sales_customer_type', store=True)

    @api.depends('cgg_group_id', 'promotor_id', 'company_id.country_code', 'is_company')
    def _compute_customer_segment(self):
        for partner in self:
            if not partner.is_company or partner.company_id.country_code != 'MX':
                partner.customer_segment = False
            elif partner.cgg_group_id:
                partner.customer_segment = 'key'
            elif partner.promotor_id:
                partner.customer_segment = 'promoter'
            else:
                partner.customer_segment = 'individual'

    def _get_today_mexico_city(self):
        # Hardcoded to Mexico City regardless of the executing user/context
        # (cron and module-install recomputes may run as a user/OdooBot with
        # no tz set, which would otherwise silently fall back to server time).
        utc_now = pytz.utc.localize(fields.Datetime.now())
        return utc_now.astimezone(MEXICO_CITY_TZ).date()

    def _get_current_season_start(self):
        today = self._get_today_mexico_city()
        year = today.year if today >= date(today.year, 9, 1) else today.year - 1
        return date(year, 9, 1)

    @api.depends(
        'invoice_ids.state', 'invoice_ids.invoice_date', 'invoice_ids.move_type',
        'company_id.country_code', 'is_company',
    )
    def _compute_sales_customer_type(self):
        for partner in self:
            partner.sales_customer_type = False
            if not partner.is_company or partner.company_id.country_code != 'MX':
                continue

            current_start = partner._get_current_season_start()
            prev_start = current_start - relativedelta(years=1)
            prev_end = current_start - timedelta(days=1)

            # invoice_ids is unfiltered (vendor bills, refunds, misc entries
            # can share the same partner_id), so move_type must be checked here.
            commissionable_invoices = partner.invoice_ids.filtered(
                lambda m: m.state == 'posted'
                and m.move_type == 'out_invoice'
                and m.invoice_date
                and any(l.product_id.can_be_commissionable for l in m.invoice_line_ids)
            )

            if commissionable_invoices:
                has_history_before_season = bool(
                    commissionable_invoices.filtered(lambda m: m.invoice_date < current_start))

                if not has_history_before_season:
                    partner.sales_customer_type = 'new'
                elif commissionable_invoices.filtered(lambda m: prev_start <= m.invoice_date <= prev_end):
                    partner.sales_customer_type = 'current'
                elif commissionable_invoices.filtered(lambda m: m.invoice_date >= current_start):
                    partner.sales_customer_type = 'recovered'
                else:
                    partner.sales_customer_type = 'lost'

    def cron_recompute_sales_customer_type(self):
        # Season rollover (Sept 1) doesn't touch any field this compute
        # depends on, so it never fires on its own — this cron is the only
        # way sales_customer_type reflects a new season, and it's meant to
        # be triggered manually (see data/pao_cs_ir_cron_data.xml).
        partners = self.search([
            ('invoice_ids', '!=', False),
            ('company_id.country_code', '=', 'MX'),
            ('is_company', '=', True),
        ])
        partners._compute_sales_customer_type()

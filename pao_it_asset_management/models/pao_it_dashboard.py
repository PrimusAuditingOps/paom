import calendar
from collections import defaultdict
from datetime import date

from odoo import models, fields, api, _

from .hr_company_label import _company_label
from .pao_it_costs import (to_usd, maintenance_cost_date, movement_shipping_date,
                           maintenance_shipping_date)


# ==========================================
# DATOS DEL TABLERO DE INICIO
# ==========================================
# El tablero (static/src/dashboard/) solo pinta lo que devuelven estos
# métodos. Todo se calcula aquí, con los permisos y las reglas
# multi-compañía del usuario, y las etiquetas ya van traducidas al idioma
# del usuario (el JS no traduce nada).
class PaoItDashboard(models.AbstractModel):
    _name = 'pao.it.dashboard'
    _description = 'IT Asset Management Dashboard'

    # ------------------------------------------
    # Filtros
    # ------------------------------------------
    @api.model
    def _clean_company_ids(self, company_ids):
        """Solo compañías que el usuario tiene seleccionadas."""
        allowed = self.env.companies.ids
        company_ids = [c for c in (company_ids or []) if c in allowed]
        return company_ids or allowed

    @api.model
    def _range(self, date_from, date_to):
        today = fields.Date.context_today(self)
        start = fields.Date.to_date(date_from) if date_from else date(today.year, 1, 1)
        end = fields.Date.to_date(date_to) if date_to else date(today.year, 12, 31)
        return start, end

    @staticmethod
    def _in_range(value, start, end):
        return bool(value) and start <= value <= end

    # ------------------------------------------
    # Datos principales
    # ------------------------------------------
    @api.model
    def get_dashboard_data(self, company_ids=None, date_from=None, date_to=None, kind='hardware'):
        company_ids = self._clean_company_ids(company_ids)
        start, end = self._range(date_from, date_to)
        today = fields.Date.context_today(self)
        company_domain = [('company_id', 'in', company_ids)]
        Asset = self.env['pao.it.asset']
        Maintenance = self.env['pao.it.asset.maintenance']
        Movement = self.env['pao.it.asset.movement']
        Period = self.env['pao.it.subscription.period']
        Subscription = self.env['pao.it.subscription']
        Assignment = self.env['pao.it.license.assignment']

        assets = Asset.search(company_domain)
        active_assets = assets.filtered(lambda a: a.state not in ('retired', 'lost'))

        # --- Gasto del periodo por concepto (USD) ---
        spend = defaultdict(float)
        purchased = assets.filtered(lambda a: self._in_range(a.purchase_date, start, end))
        spend['acquisition'] = sum(purchased.mapped('cost_acquisition_usd'))
        for maintenance in Maintenance.search(company_domain + [('state', '!=', 'cancelled')]):
            concept = 'warranty' if maintenance.maintenance_type == 'warranty' else 'maintenance'
            cost_date = maintenance_cost_date(maintenance)
            if maintenance.cost and self._in_range(cost_date, start, end):
                spend[concept] += to_usd(self.env, maintenance.cost, maintenance.currency_id,
                                         maintenance.company_id, cost_date)
            ship_date = maintenance_shipping_date(maintenance)
            if maintenance.shipping_cost and self._in_range(ship_date, start, end):
                spend['shipping'] += to_usd(self.env, maintenance.shipping_cost, maintenance.shipping_currency_id,
                                            maintenance.company_id, ship_date)
        for movement in Movement.search(company_domain + [('shipping_cost', '!=', 0)]):
            ship_date = movement_shipping_date(movement)
            if self._in_range(ship_date, start, end):
                spend['shipping'] += to_usd(self.env, movement.shipping_cost, movement.shipping_currency_id,
                                            movement.company_from_id or movement.company_id, ship_date)
        periods = Period.search(company_domain + [('start_date', '>=', start), ('start_date', '<=', end)])
        software_by_type = defaultdict(float)
        for period in periods:
            usd = to_usd(self.env, period.total_amount, period.currency_id, period.company_id, period.start_date)
            spend['software'] += usd
            software_by_type[period.subscription_id.software_type_id.name or _("Undefined")] += usd

        # --- Uso de licencias (suscripciones vigentes) ---
        subscriptions = Subscription.search(company_domain).filtered(
            lambda s: s.state in ('active', 'renewing', 'expiring'))
        allowed_users = sum(subscriptions.mapped('allowed_users'))
        assigned_users = sum(subscriptions.mapped('assigned_count'))

        # --- Conteos ---
        to_review = Assignment.search(company_domain + [('to_review', '=', True)])
        overdue = Maintenance.search(company_domain + [('is_overdue', '=', True)])
        delayed_assets = active_assets.filtered(lambda a: a.state == 'in_transit' and self._shipment_delayed(a, today))

        # --- Gráfica ---
        if kind == 'software':
            chart = sorted(software_by_type.items(), key=lambda kv: -kv[1])
            chart_title = _("Software Spend by Type (period)")
        else:
            by_category = defaultdict(float)
            for asset in active_assets:
                by_category[asset.category_id.name or _("Undefined")] += asset.cost_acquisition_usd
            chart = sorted(by_category.items(), key=lambda kv: -kv[1])
            chart_title = _("Asset Value by Category (acquisition cost)")

        return {
            'companies': [{'id': c.id, 'name': c.name, 'label': _company_label(c)}
                          for c in self.env.companies],
            'company_ids': company_ids,
            'date_from': fields.Date.to_string(start),
            'date_to': fields.Date.to_string(end),
            'kind': kind,
            'labels': self._labels(),
            'cards': {
                'active_assets': len(active_assets),
                'total_assets': len(assets),
                'asset_value': sum(active_assets.mapped('cost_acquisition_usd')),
                'purchases_amount': spend['acquisition'],
                'purchases_count': len(purchased),
                'software_spend': spend['software'],
                'assigned_users': assigned_users,
                'allowed_users': allowed_users,
            },
            'counts': {
                'to_review': {'value': len(to_review), 'model': 'pao.it.license.assignment',
                              'domain': [('id', 'in', to_review.ids)]},
                'overdue': {'value': len(overdue), 'model': 'pao.it.asset.maintenance',
                            'domain': [('id', 'in', overdue.ids)]},
                'delayed': {'value': len(delayed_assets), 'model': 'pao.it.asset',
                            'domain': [('id', 'in', delayed_assets.ids)]},
            },
            'spend': [
                {'key': key, 'label': label, 'value': spend[key]}
                for key, label in (
                    ('acquisition', _("Acquisitions")), ('maintenance', _("Maintenance")),
                    ('warranty', _("Warranties")), ('shipping', _("Shipping")), ('software', _("Software")))
            ],
            'spend_total': sum(spend.values()),
            'chart_title': chart_title,
            'chart': [{'label': label, 'value': value} for label, value in chart if value],
        }

    @api.model
    def _shipment_delayed(self, asset, today):
        shipment = asset._get_last_movement(('assign', 'reassign')).filtered('requires_shipping')
        return bool(shipment.estimated_delivery_date) and shipment.estimated_delivery_date < today

    @api.model
    def _labels(self):
        return {
            'title': _("IT Asset Management"),
            'companies': _("Companies"), 'date_from': _("From"), 'date_to': _("To"),
            'hardware': _("Hardware"), 'software': _("Software"),
            'active_assets': _("Active Assets"), 'total_assets': _("Total assets"),
            'asset_value': _("Asset Value (acquisition cost)"),
            'asset_value_note': _("Complementary costs (maintenance, warranty, shipping) are shown in each asset, "
                                  "Costs tab."),
            'purchases': _("Purchases in Period"), 'purchases_count': _("assets"),
            'software_spend': _("Software Spend in Period"),
            'software_spend_note': _("By period start date."),
            'license_usage': _("License Usage"), 'license_usage_note': _("assigned / allowed users"),
            'to_review': _("Assignments to Review"), 'overdue': _("Overdue Preventives"),
            'delayed': _("Delayed Shipments"),
            'spend_title': _("Spend in Period by Concept (USD)"), 'total': _("Total"),
            'calendar_title': _("Alerts"),
            'weekdays': [_("Sun"), _("Mon"), _("Tue"), _("Wed"), _("Thu"), _("Fri"), _("Sat")],
            'no_data': _("No data for the selected filters."),
            'event_types': {
                'maintenance': _("Maintenance Due"), 'warranty': _("Warranty Expiring"),
                'subscription': _("Subscription Renewal / Expiring"), 'transit': _("In Transit"),
            },
        }

    # ------------------------------------------
    # Calendario de alertas (un mes)
    # ------------------------------------------
    @api.model
    def get_calendar_events(self, company_ids=None, year=None, month=None):
        company_ids = self._clean_company_ids(company_ids)
        today = fields.Date.context_today(self)
        year, month = int(year or today.year), int(month or today.month)
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        company_domain = [('company_id', 'in', company_ids)]
        events = []

        for maintenance in self.env['pao.it.asset.maintenance'].search(company_domain + [
                ('state', 'in', ('scheduled', 'in_progress')),
                ('scheduled_date', '>=', start), ('scheduled_date', '<=', end)]):
            events.append(self._event('maintenance', maintenance.scheduled_date,
                                      f"{maintenance.asset_id.asset_tag} · {maintenance.name}",
                                      'pao.it.asset.maintenance', maintenance.id))

        for asset in self.env['pao.it.asset'].search(company_domain + [
                ('state', 'not in', ('retired', 'lost')),
                ('warranty_end', '>=', start), ('warranty_end', '<=', end)]):
            events.append(self._event('warranty', asset.warranty_end, asset.asset_tag, 'pao.it.asset', asset.id))

        for subscription in self.env['pao.it.subscription'].search(company_domain + [('cancelled', '=', False)]):
            end_date = subscription.current_end_date
            if end_date and start <= end_date <= end and subscription.license_type != 'perpetual':
                events.append(self._event('subscription', end_date, subscription.display_name,
                                          'pao.it.subscription', subscription.id))

        for asset in self.env['pao.it.asset'].search(company_domain + [('state', '=', 'in_transit')]):
            shipment = asset._get_last_movement(('assign', 'reassign')).filtered('requires_shipping')
            eta = shipment.estimated_delivery_date
            if eta and start <= eta <= end:
                events.append(self._event('transit', eta, asset.asset_tag, 'pao.it.asset', asset.id))

        return {
            'year': year, 'month': month,
            'month_label': fields.Date.to_date(start).strftime('%Y-%m'),
            'first_weekday': (start.weekday() + 1) % 7,  # 0 = domingo
            'days': calendar.monthrange(year, month)[1],
            'today': fields.Date.to_string(today),
            'events': events,
        }

    @api.model
    def _event(self, event_type, event_date, title, model, res_id):
        return {'type': event_type, 'date': fields.Date.to_string(event_date), 'day': event_date.day,
                'title': title, 'model': model, 'res_id': res_id}

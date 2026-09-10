# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaoAbcCategory(models.Model):
    _name = 'pao.abc.category'
    _description = 'Categoría ABC de Clientes'
    _order = 'amount_from'

    name = fields.Char(required=True)
    amount_from = fields.Float(
        string='Monto desde (USD)', required=True, digits=(16, 2),
    )
    amount_to = fields.Float(
        string='Monto hasta (USD)', digits=(16, 2),
        help='Límite superior del rango, no incluido. Déjalo en 0 para '
             'indicar "en adelante" (sin límite superior).',
    )
    color = fields.Integer(string='Color')

    _sql_constraints = [
        ('amount_from_positive', 'CHECK(amount_from >= 0)',
         'El monto "desde" debe ser mayor o igual a 0.'),
    ]

    @api.constrains('amount_from', 'amount_to')
    def _check_amount_range(self):
        for rec in self:
            if rec.amount_to and rec.amount_to <= rec.amount_from:
                raise ValidationError(
                    'En la categoría "%s", el monto "hasta" debe ser mayor '
                    'al monto "desde".' % rec.name
                )

    @api.model
    def _get_category_for_amount(self, amount):
        """Regresa el registro de categoría cuyo rango [desde, hasta)
        contiene `amount`, o un recordset vacío si no cae en ninguno
        (por ejemplo, ventas en 0)."""
        for category in self.search([], order='amount_from'):
            if amount >= category.amount_from and (
                not category.amount_to or amount < category.amount_to
            ):
                return category
        return self.browse()

    # ------------------------------------------------------------------
    # Cron: recategorización anual (rollover de temporada sep-ago)
    # ------------------------------------------------------------------
    def _sum_usd_by(self, groupby_field, record_ids, season_start, season_end):
        """Suma usd_untaxed_total de sales.invoicing.report, agrupado por
        `groupby_field`, para la temporada [season_start, season_end] y
        solo productos comisionables."""
        if not record_ids:
            return {}
        domain = [
            (groupby_field, 'in', record_ids),
            ('product_tmpl_id.can_be_commissionable', '=', True),
            ('invoice_date', '>=', season_start),
            ('invoice_date', '<=', season_end),
        ]
        groups = self.env['sales.invoicing.report'].read_group(
            domain, ['usd_untaxed_total:sum'], [groupby_field]
        )
        return {
            g[groupby_field][0]: g['usd_untaxed_total']
            for g in groups if g[groupby_field]
        }

    def _write_customers_one_by_one(self, customers, values):
        """Escribe registro por registro (no en lote): varios módulos de
        terceros/enterprise instalados (p.ej. referenciasbancarias) tienen
        constraints en res.partner que asumen un solo registro (ensure_one)
        y truenan si se les hace write() sobre un recordset múltiple."""
        for customer in customers:
            try:
                customer.write(values)
            except Exception:  # noqa: BLE001
                _logger.exception(
                    'Error al escribir la Categoría ABC en el cliente %s (id %s)',
                    customer.display_name, customer.id,
                )

    @api.model
    def cron_recompute_abc_categories(self):
        """1) Categoriza cada Grupo y sus clientes por las ventas del grupo.
        2) Categoriza cada Promotor y sus clientes por las ventas del promotor
           (si un cliente tiene grupo y promotor a la vez, este paso corre
           después y su categoría es la que prevalece).
        3) Categoriza individualmente a los clientes sin grupo ni promotor.
        """
        partner_model = self.env['res.partner']
        season_start = partner_model._get_current_season_start()
        prev_start = season_start - relativedelta(years=1)
        prev_end = season_start - timedelta(days=1)
        season_label = '%s-%s' % (prev_start.year, season_start.year)

        # 1) Grupos
        groups = self.env['customergroups.group'].search([])
        group_sales = self._sum_usd_by(
            'group_id', groups.ids, prev_start, prev_end
        )
        for group in groups:
            amount = group_sales.get(group.id, 0.0)
            category = self._get_category_for_amount(amount)
            values = {
                'categoria_abc_id': category.id,
                'abc_sales_amount': amount,
                'abc_season': season_label,
            }
            group.write(values)
            self._write_customers_one_by_one(
                group.customer_ids.filtered('is_company'), values
            )

        # 2) Promotores
        promotores = self.env['comisionpromotores.promotor'].search([])
        promotor_sales = self._sum_usd_by(
            'promotor_id', promotores.ids, prev_start, prev_end
        )
        for promotor in promotores:
            amount = promotor_sales.get(promotor.id, 0.0)
            category = self._get_category_for_amount(amount)
            values = {
                'categoria_abc_id': category.id,
                'abc_sales_amount': amount,
                'abc_season': season_label,
            }
            promotor.write(values)
            self._write_customers_one_by_one(
                promotor.cliente_id.filtered('is_company'), values
            )

        # 3) Clientes sin grupo ni promotor: categorización individual
        individuals = partner_model.search([
            ('is_company', '=', True),
            ('cgg_group_id', '=', False),
            ('promotor_id', '=', False),
        ])
        individual_sales = self._sum_usd_by(
            'partner_id', individuals.ids, prev_start, prev_end
        )
        for partner in individuals:
            amount = individual_sales.get(partner.id, 0.0)
            category = self._get_category_for_amount(amount)
            self._write_customers_one_by_one(partner, {
                'categoria_abc_id': category.id,
                'abc_sales_amount': amount,
                'abc_season': season_label,
            })

        _logger.info(
            'Categoría ABC recalculada para la temporada %s: %s grupos, '
            '%s promotores, %s clientes individuales.',
            season_label, len(groups), len(promotores), len(individuals),
        )
        return True

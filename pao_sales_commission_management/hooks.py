# -*- coding: utf-8 -*-

_BACKFILL_LINE_PROMOTOR_SQL = """
    UPDATE sale_order_line sol
    SET pao_promotor_id = so.pao_promotor_id
    FROM sale_order so, product_product pp, product_template pt
    WHERE sol.order_id = so.id
      AND pp.id = sol.product_id
      AND pt.id = pp.product_tmpl_id
      AND so.pao_promotor_id IS NOT NULL
      AND pt.pao_commission_payment IS TRUE
      AND sol.pao_promotor_id IS NULL
"""

_BACKFILL_COMMISSION_RATE_SQL = """
    UPDATE comisionpromotores_promotor
    SET commission_rate = porcentaje
    WHERE commission_rate IS NULL OR commission_rate = 0
"""


def post_init_hook(env):
    """Runs once, right after a fresh install of this module (e.g. the first
    install in an environment, such as production, that never had it before).

    Backfills:
    - sale.order.line.pao_promotor_id for quotations that were already
      confirmed before this module existed, so in-flight commissions keep
      computing their commissionable base correctly instead of suddenly
      seeing 0 commissionable lines.
    - comisionpromotores.promotor.commission_rate (new decimal field) from
      the existing integer "porcentaje" field, for every promoter that
      already existed, so their commission rate isn't 0 until someone
      manually re-enters it."""
    env.cr.execute(_BACKFILL_LINE_PROMOTOR_SQL)
    env.cr.execute(_BACKFILL_COMMISSION_RATE_SQL)

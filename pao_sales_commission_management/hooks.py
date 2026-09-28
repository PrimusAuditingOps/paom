# -*- coding: utf-8 -*-

_BACKFILL_COMMISSION_RATE_SQL = """
    UPDATE comisionpromotores_promotor
    SET commission_rate = porcentaje
    WHERE commission_rate IS NULL OR commission_rate = 0
"""


def post_init_hook(env):
    """Runs once, right after a fresh install of this module (e.g. the first
    install in an environment, such as production, that never had it before).

    Backfills comisionpromotores.promotor.commission_rate (new decimal field)
    from the existing integer "porcentaje" field, for every promoter that
    already existed, so their commission rate isn't 0 until someone manually
    re-enters it.

    Quotations are intentionally NOT backfilled: sale.order.pao_commission_agent_id
    starts empty, so only quotations where a salesperson sets a Commission
    Agent from now on generate commissions (older ones were already paid
    outside the system)."""
    env.cr.execute(_BACKFILL_COMMISSION_RATE_SQL)

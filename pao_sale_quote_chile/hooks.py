# -*- coding: utf-8 -*-
from .models.pao_quote_config import default_format_template


def post_init_hook(env):
    """Create the Chile quotation format configuration and a sample quotation template per Chilean company.

    Both start with the content of the manual GLOBALG.A.P. quotations (data/pao_quote_default_format.html)
    and are adjusted afterwards by the sales department.
    """
    Config = env['pao.quote.config'].with_context(active_test=False)
    companies = env['res.company'].search([('country_id.code', '=', 'CL')])
    for company in companies:
        if Config.search_count([('company_id', '=', company.id)]):
            continue
        Config.create({
            'name': company.name,
            'company_id': company.id,
        })
        env['sale.order.template'].create({
            'name': 'GLOBALG.A.P. (Chile)',
            'company_id': company.id,
            'pao_quote_format_template': default_format_template(),
        })

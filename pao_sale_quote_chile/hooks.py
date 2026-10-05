# -*- coding: utf-8 -*-


def post_init_hook(env):
    """Create the quotation format configuration for every Chilean company.

    The default texts live on the field defaults of ``pao.quote.config``, so the
    configuration starts with the content of the current manual quotations and
    can be adjusted afterwards from Sales > Configuration.
    """
    Config = env['pao.quote.config'].with_context(active_test=False)
    companies = env['res.company'].search([('country_id.code', '=', 'CL')])
    for company in companies:
        if not Config.search_count([('company_id', '=', company.id)]):
            Config.create({
                'name': company.name,
                'company_id': company.id,
            })

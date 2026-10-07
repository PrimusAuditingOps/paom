# -*- coding: utf-8 -*-


def post_init_hook(env):
    """Create the Chile quotation format configuration of every Chilean company, and assign the
    initial rate sheets (data/pao_quote_rate_data.xml) to the Chilean company when there is only one.
    """
    Config = env['pao.quote.config'].with_context(active_test=False)
    companies = env['res.company'].search([('country_id.code', '=', 'CL')])
    for company in companies:
        if not Config.search_count([('company_id', '=', company.id)]):
            Config.create({
                'name': company.name,
                'company_id': company.id,
            })
    if len(companies) == 1:
        rates = env['pao.quote.rate'].with_context(active_test=False).search([('company_id', '=', False)])
        rates.write({'company_id': companies.id})

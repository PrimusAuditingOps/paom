from odoo import fields, models, api

class PaoCrVisitsReport(models.Model):
    
    _name = 'pao.cr.visits.report'
    _description = 'pao cr visits report'

    audit_scheme = fields.Char(
        string= "Audit scheme",
    )

    coordinator_name = fields.Char(
        string= "Coordinator",
    )

    audit_id = fields.Char(
        string= "Audit ID",
    )

    audit_date = fields.Date(
        string= "Audit date",
    )

    registration_number = fields.Char(
        string= "Registration number",
    )

    organization_name = fields.Char(
        string= "Organization name",
    )
    operation_type = fields.Char(
        string= "Type",
    )
    operation_short_type = fields.Char(
        string= "Short type",
    )


    commodities = fields.Text(
        string= "commodities",
    )

    contact_name = fields.Char(
        string= "Contact name",
    )

    email = fields.Char(
        string= "Email",
    )

    locations = fields.Char(
        string= "Locations",
    )

    shipper = fields.Char(
        string= "Shipper",
    )

    cb = fields.Char(
        string= "CB",
        compute='_get_cb',
        store=True,
    )
    
    country = fields.Char(
        string= "Country",
        compute='_get_city_state_country',
        store=True, 
    )

    state = fields.Char(
        string= "State",
        compute='_get_city_state_country',
        store=True,
    )

    city = fields.Char(
        string= "City",
        compute='_get_city_state_country',
        store=True,
    )

    month = fields.Char(
        string= "Month",
        compute='_get_month',
        store=True,
    )

    year = fields.Char(
        string= "Year",
        compute='_get_year',
        store=True,
    )

    value = fields.Float(
        string= "Value",
        compute='_get_value',
        store=True,
    )
    customer_search_status = fields.Selection(
        selection=[
            ('0', "Not found"),
            ('1', "Found"),
            ('2', "Non-Customer"),
        ],
        string="Customer Search Status", 
        readonly=True, 
        copy=False,
        default='2',
    )

    @api.depends('operation_type')
    def _get_value(self):
        for rec in self:
            rec.value = 0
            price_default = 0
            service_name = None
            product_ids = []
            cb = ""
            #get CB
            if rec.registration_number:
                indice = -1
                indice = rec.registration_number.find("-")
                if indice > -1:
                    cb = rec.registration_number[:indice]

            #get Azzule's service name
            service_list = rec.operation_type.split(";")
            for s in service_list:
                service_name = s[2:].strip()
                break
            #Get the odoo's products relate to Azzule's service name
            if service_name:
                recService = rec.env["pao.cr.visits.report.services"].search([("name","=", service_name)])
                for p in recService.products_ids.sorted(key=lambda r: (r.sequence)):
                    rec.write({"operation_short_type": recService.short_name})
                    if price_default == 0:
                        price_default = p.list_price_product
                    product_ids.append(p.product_id.id)



            if len(product_ids) > 0 and cb == "PA":
                company = rec.organization_name.strip()
                companyID = None
                #get customer in Odoo 
                recCustomer = rec.env["res.partner"].search([("company_type","=", "company"),("name","=", company)], limit=1)
                if recCustomer:
                    for rc in recCustomer:
                        companyID = rc.id
                        rec.write({"customer_search_status": "1"})
                else:
                    rec.write({"customer_search_status": "0"})
                """
                else:
                    company = company.replace(" ","%")
                    company = company.replace(".", "%")
                    company = company.replace(",", "%")
                    recCustomer = rec.env["res.partner"].search([("company_type","=", "company"),("name","ilike", company)], limit=1)
                    if recCustomer:
                        for rc in recCustomer:
                            companyID = rc.id
                            rec.write({"customer_search_status": "2"})
                """
                if companyID:
                    sql = """
                        SELECT a.id, b.price_unit FROM sale_order as a inner join sale_order_line as b on a.id = b.order_id 
                        WHERE a.state <> 'cancel' AND b.product_id IN %(product_ids)s AND a.partner_id = %(partner_id)s 
                        ORDER BY a.id desc, b.sequence ASC limit 1
                    """
                    params = {
                        'product_ids': tuple(product_ids),
                        'partner_id': companyID,
                    }
                    rec.env.cr.execute(sql, params)
                    result = rec.env.cr.dictfetchall()
                    for r in result:
                        price_default = r["price_unit"]

            rec.value = price_default

    @api.depends('registration_number')
    def _get_cb(self):
        for rec in self:
            rec.cb = ""

            if rec.registration_number:
                indice = -1
                indice = rec.registration_number.find("-")
                if indice > -1:
                    if rec.registration_number[:indice] == "PA":
                        rec.cb = "PAO"
                    else:
                        rec.cb = rec.registration_number[:indice]

    @api.depends('locations')
    def _get_city_state_country(self):
        for rec in self:
            rec.city = ""
            rec.state = ""
            rec.country = ""

            location_list = rec.locations.split(",")
            if location_list[0]:
                rec.country = location_list[0]
            if location_list[1]:
                rec.state = location_list[1]
            if location_list[2]:
                rec.city = location_list[2]
    
    @api.depends('audit_date')
    def _get_year(self):
        for rec in self:
            if rec.audit_date:
                rec.year = str(rec.audit_date.year)
    
    @api.depends('audit_date')
    def _get_month(self):
        months = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
        for rec in self:
            rec.month = ""
            if rec.audit_date:
                rec.month = "{}-{}".format(str(rec.audit_date.month).rjust(2, '0'), months[int(rec.audit_date.month) - 1])
    

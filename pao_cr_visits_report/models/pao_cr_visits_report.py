from odoo import fields, models, api

class PaoCrVisitsReport(models.Model):
    
    _name = 'pao.cr.visits.report'
    _description = 'Model for...'

    audit_scheme = fields.Char(
        string= "Audit scheme",
    )

    coordinator_name = fields.Char(
        string= "Coordinator",
    )

    audit_id = fields.Integer(
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

    year = fields.Integer(
        string= "Year",
        compute='_get_year',
        store=True,
    )

    value = fields.Float(
        string= "Value",
        compute='_get_value',
        store=True,
    )

    @api.depends('operation_type')
    def _get_value(self):
        for rec in self:
            rec.value = 123

    @api.depends('registration_number')
    def _get_cb(self):
        for rec in self:
            rec.cb = ""

            if rec.registration_number_azzule:
                indice = -1
                indice = rec.registration_number_azzule.find("-")
                if indice > -1:
                    rec.cb = rec.registration_number_azzule[indice+1:]

    @api.depends('locations')
    def _get_city_state_country(self):
        for rec in self:
            rec.city = ""
            rec.state = ""
            rec.country = ""

            location_list = rec.locations.split(",")
            if location_list[0]:
                rec.city = location_list[0]
            if location_list[1]:
                rec.state = location_list[1]
            if location_list[2]:
                rec.country = location_list[2]
    
    @api.depends('audit_date')
    def _get_year(self):
        for rec in self:
            if rec.audit_date:
                rec.year = int(rec.audit_date.year)
    
    @api.depends('audit_date')
    def _get_month(self):
        months = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
        for rec in self:
            rec.month = ""
            if rec.audit_date:
                rec.month = "{}-{}".format(str(rec.audit_date.month), months[int(rec.audit_date.month) - 1])
    

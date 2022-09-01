from odoo import fields, models
from datetime import datetime

class ResCityInherit(models.Model):
    _inherit='res.city'

    paa_city_latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    paa_city_longitude = fields.Float(string='Geo Longitude', digits=(10, 7))
    paa_date_localization = fields.Date(string='Geolocation Date',default=datetime.today())
    
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit="res.partner"

    pao_geolocation_allowed = fields.Boolean(compute='_compute_is_geolocation_allowed')
            
    def _compute_is_geolocation_allowed(self):
        self.pao_geolocation_allowed = self.env.user.has_group("pao_contact_geolocation_restriction.allow_geolocation_modification")

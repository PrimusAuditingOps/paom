from odoo import fields, models, api

class ResPartner(models.Model):
    _inherit = 'res.partner'


    def _get_followup_responsible(self):
        result = super(ResPartner,self)._get_followup_responsible()

        if self.company_id.country_code == "US":
            result = self.env.user

        return result
from odoo import fields,models,api

class PaoAuditContact(models.Model):

    _name = "pao.audit.contact"
    _description = "PAO Audit Contact"
    _rec_name = 'name'

    abbreviation= fields.Char("Abbreviation")
    name = fields.Char("Name")
    address = fields.Text("Address")
    mailingAddress= fields.Text("Mailing Address")
    country_id = fields.Many2one('res.country', string='Country', required=True)
    state_id = fields.Many2one('res.country.state', string="State", domain="[('country_id', '=', country_id)]")
    city_id = fields.Many2one('res.city', string="City", domain="[('state_id', '=', state_id)]")
    postalCode= fields.Char("Postal Code")
    phone_number= fields.Char("Phone Number")
    fax= fields.Char("Fax")
    email= fields.Char("Email")
    job= fields.Char("Job")
    
    property_id= fields.Many2one("pao.audit.property",string="Property")
    legal_entity_id= fields.Many2one("pao.audit.legal.entity",string="Legal Entity")


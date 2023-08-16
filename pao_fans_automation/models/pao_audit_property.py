from odoo import fields,models,api

class PaoAuditProperty(models.Model):

    _name = "pao.audit.property"
    _description = "PAO Audit Property"
    _rec_name = 'name'

    type= fields.Selection(
        string='Property Type',
        selection=[('site','Site'), ('phu','PHU')],
        help="The type of property where the audit will be made", default= 'site'
        )
    name= fields.Char("Name of Property")
    address = fields.Text("Address")
    mailingAddress= fields.Text("Mailing Address")
    country_id = fields.Many2one('res.country', string='Country', required=True)
    state_id = fields.Many2one('res.country.state', string="State", domain="[('country_id', '=', country_id)]")
    city_id = fields.Many2one('res.city', string="City", domain="[('state_id', '=', state_id)]")
    postalCode= fields.Char("Postal Code")
    phone_number= fields.Char("Phone Number")
    fax= fields.Char("Fax")
    email= fields.Char("Email")
    latitude= fields.Char("Latitude")
    longitude= fields.Char("Longitude")
    audit_contact_id = fields.Many2one('pao.audit.contact', 'Property Contact')
    product_ids= fields.One2many("pao.audit.product.detail","audit_property_id")
    hired_workers= fields.Integer("Hired Workers")
    outsourced_workers= fields.Integer("Outsourced Workers")


    legal_entity_id = fields.Many2one("pao.audit.legal.entity",string="Legal Entity")
    #property_ids= fields.One2many("pao.audit.contact","property_id")


    

    @api.depends('property_ids')
    def compute_stage(self):
        if len(self.property_ids) > 0:
            self.audit_contact_id = self.property_ids[0]

    def stage_inverse(self):
        if len(self.property_ids) > 0:
            # delete previous reference
            property = self.env['pao.audit.property'].browse(self.property_ids[0].id)
            asset.stage_id = False
        # set new reference
        self.audit_contact_id.property_id = self

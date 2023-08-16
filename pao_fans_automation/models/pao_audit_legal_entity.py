from odoo import fields,models,api

class PaoAuditLegalEntity(models.Model):

    _name = "pao.audit.legal.entity"
    _description = "PAO Audit Legal Entity"
    _rec_name = 'name'

    name= fields.Char("Name")
    address = fields.Text("Address")
    mailingAddress= fields.Text("Mailing Address")
    country_id = fields.Many2one('res.country', string='Country', required=True)
    state_id = fields.Many2one('res.country.state', string="State", domain="[('country_id', '=', country_id)]")
    city_id = fields.Many2one('res.city', string="City", domain="[('state_id', '=', state_id)]")
    postalCode= fields.Char("Postal Code")
    phone_number= fields.Char("Phone Number")
    fax= fields.Char("Fax")
    email= fields.Char("Email")
    gln= fields.Char("GLN")
    rfc= fields.Char("RFC")
    previus_ggn= fields.Char("Previus GGN")
    cb_name= fields.Char("CB Name")
    latitude= fields.Char("Latitude")
    longitude= fields.Char("Longitude")
    audit_property_ids= fields.One2many('pao.audit.property',"legal_entity_id")
    audit_contact_id = fields.Many2one('pao.audit.contact', 'Legal Entity Contact')
    
    #legal_entity_ids= fields.One2many("pao.audit.contact","legal_entity_id")
    global_gap_application_id= fields.Many2one('pao.global.gap.application',"GLOBALG.A.P. Application")

    

    @api.depends('legal_entity_ids')
    def compute_stage(self):
        if len(self.legal_entity_ids) > 0:
            self.audit_contact_id = self.legal_entity_ids[0]

    def stage_inverse(self):
        if len(self.legal_entity_ids) > 0:
            # delete previous reference
            legal_entity = self.env['pao.audit.legal.entity'].browse(self.legal_entity_ids[0].id)
            asset.stage_id = False
        # set new reference
        self.audit_contact_id.legal_entity_ids = self
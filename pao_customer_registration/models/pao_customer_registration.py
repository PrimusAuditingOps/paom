from odoo import fields, models, api, _
import uuid
from logging import getLogger
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, formataddr, config, get_lang
from odoo.addons.l10n_mx_edi.models.res_company import FISCAL_REGIMES_SELECTION
_logger = getLogger(__name__)

class PaoCustomerRegistration(models.Model):
    _name='pao.customer.registration'
    _description = 'Customer Registration'
    

    @api.model
    def _default_access_token(self):
        return uuid.uuid4().hex
    name = fields.Char(
        string="Name",
    )
    vat = fields.Char(
        string="VAT",
    )
    country_id = fields.Many2one(
        string="Country",
        comodel_name='res.country',
        ondelete='set null',
    )
    state_id = fields.Many2one(
        string="State",
        comodel_name='res.country.state',
        ondelete='set null',
    )
    city_id = fields.Many2one(
        string="City",
        comodel_name='res.city',
        ondelete='set null',
    )
    street_name = fields.Char(
        string="Street name",
    )
    street_number = fields.Char(
        string="Street number",
    )
    asesor = fields.Char(
        string="Asesor",
    )
    zip = fields.Char(
        string="ZIP",
    )
    phone = fields.Char(
        string="Phone",
    )
    email = fields.Char(
        string="Email",
    )
    fiscal_regime = fields.Selection(
        selection=FISCAL_REGIMES_SELECTION,
        string="Fiscal Regime",
        readonly=False,
        help="Fiscal Regime is required for all partners (used in CFDI)")
    #cfdi_use = fields.Char(
    #    string="CFDI use",
    #)

    form_url = fields.Char(
        string="Form URL",
    )
    follower_ids = fields.Many2many('res.partner', string="Copy to")
    subject = fields.Char(
        string="Subject", 
    )

    message = fields.Html(
        string="Message",
    )
    attachment_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment',
        ondelete='restrict',
        copy=False,
    )
    attachment_datas = fields.Binary(
        related='attachment_id.datas',
        string="Constancy",
    )
    attachment_name = fields.Char(
        related='attachment_id.name',
    )
    attachment_proof_of_address_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment Proof of address',
        ondelete='restrict',
        copy=False,
    )
    attachment_proof_of_address_datas = fields.Binary(
        related='attachment_proof_of_address_id.datas',
        string="Proof of address",
    )
    attachment_proof_of_address_name = fields.Char(
        related='attachment_proof_of_address_id.name',
    )
    attachment_bank_account_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment Bank account statement cover',
        ondelete='restrict',
        copy=False,
    )
    attachment_bank_account_datas = fields.Binary(
        related='attachment_bank_account_id.datas',
        string="Bank account statement cover",
    )
    attachment_bank_account_name = fields.Char(
        related='attachment_bank_account_id.name',
    )
    attachment_sat_compliance_opinion_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Attachment SAT compliance opinion',
        ondelete='restrict',
        copy=False,
    )
    attachment_sat_compliance_opinion_datas = fields.Binary(
        related='attachment_sat_compliance_opinion_id.datas',
        string="SAT compliance opinion",
    )
    attachment_sat_compliance_opinion_name = fields.Char(
        related='attachment_sat_compliance_opinion_id.name',
    )



    res_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        ondelete='cascade',
        required=True,
    )
    
    contact_id = fields.Many2one(
        'res.partner', 
        string="Contact",
        required=True,
    )
    request_status = fields.Selection(
        selection=[
            ('sent', "Sent"),
            ('complet', "Completed"),
            ('cancel', "Cancelled"),
            ('exception', "Mail Failed"),
            ('done', "Done"),
        ],
        string="Request Status",
        readonly=True, copy=False, index=True,
        default='sent'
    )
    access_token = fields.Char(
        'Security Token', 
        default=_default_access_token,
        copy=False,
    )

    child_ids = fields.One2many(
        comodel_name='pao.customer.registration.contact',
        inverse_name='customer_registration_id',
        string='Contacts',
    )

    def action_resend(self):
        self.ensure_one()
       
        self.write(
            {
                "request_status": "sent"
            }
        )

    def action_cancel(self):
        self.ensure_one()
        self.write({"request_status": "cancel"})

    def action_update_contact(self):
        self.ensure_one()

        self.write(
            {
                "request_status": "done"
            }
        )
        partner = self.res_partner_id
        partner.write(
            {
                "name": self.name,
                "vat": self.vat,
                "country_id": self.country_id.id,
                "state_id": self.state_id.id,
                "city_id": self.city_id.id,
                "street": self.street_name,
                "zip": self.zip,
                "phone": self.phone,
                "email": self.email,
                "l10n_mx_edi_fiscal_regime": self.fiscal_regime,
            }
        )
        attachment_list = []
        if self.attachment_id:
            attachment_list.append(self.attachment_id.id)
        if self.attachment_proof_of_address_id:
            attachment_list.append(self.attachment_proof_of_address_id.id)
        if self.attachment_bank_account_id:
            attachment_list.append(self.attachment_bank_account_id.id)
        if self.attachment_sat_compliance_opinion_id:
            attachment_list.append(self.attachment_sat_compliance_opinion_id.id)

        contact = self.env["res.partner"]
        for rec in self.child_ids:
            contact.create(
                {
                    "type": "contact",
                    "name": rec.name,
                    "function": rec.occupation,
                    "email": rec.email,
                    "phone": rec.phone,
                    "parent_id": partner.id,
                }
            )
        partner.message_post(body=_("The fiscal certificate has been added."), attachment_ids= attachment_list)


    def write(self, vals):
        for rec in self:
            if vals.get('request_status') == "complet":
                channel_id = rec.env['discuss.channel'].sudo().search([('name', 'ilike', "Actualización Catálogos")]) 
                if channel_id:

                    notification = ('<a href="#" data-oe-model="pao.customer.registration" class="o_redirect" data-oe-id="%s">#%s</a>') % (rec.id, rec.res_partner_id.name,)
                    channel_id.sudo().message_post(body=_('Customer registration has been completed: ') + notification, message_type='comment', body_is_html = True)

        result = super(PaoCustomerRegistration, self).write(vals)
        return result
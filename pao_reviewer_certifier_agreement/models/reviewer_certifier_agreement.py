from odoo import fields, models, api, _
import base64
import uuid
import pytz

class PaoReviewerCertifierAgreement(models.Model):
    _name = "pao.reviewer.certifier.agreement"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "PAO Reviewer Certifier Agreement"
    _rec_name = 'title'


    @api.model
    def _default_access_token(self):
        return uuid.uuid4().hex

    title = fields.Char(
        string='name', 
        compute='_get_name_agreement'
    )
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Purchase Order',
        ondelete='cascade',
        required=True,
    )

    signer_id = fields.Many2one(
        'res.partner', 
        string="Signer",
        required=True,
    )

    document_type = fields.Selection(
        selection=[
            ('reviewer', "Reviewer Agreement"),
            ('certifier', "Certifier Agreement"),
        ],
        string="Document Type",
    )
    document_status = fields.Selection(
        selection=[
            ('sent', "Sent"),
            ('cancelled', "Cancelled"),
            ('done', "Done"),
        ],
        string="Document Status",
    )

    access_token = fields.Char(
        'Security Token', 
        default=_default_access_token,
        copy=False,
    )
    signature_name = fields.Char(
        'Signature name',
        copy=False,
    )

    signature = fields.Binary(
        string="Signature", 
        copy=False,
    )
    signature_date = fields.Date(
        string="Signer's signature date", 
        copy=False,
    )
    sign_url = fields.Char(
        string="URL para firmar",
    )
    attachment_id = fields.Many2one(
        string="Document",
        comodel_name='ir.attachment',
        ondelete='restrict',
        copy=False,
        tracking=True,
    )
    attachment_datas = fields.Binary(
        related='attachment_id.datas',
        string="Agreement",
    )
    attachment_name = fields.Char(
        related='attachment_id.name',
    )
    scheme_manager = fields.Many2one(
        'res.users', 
        string="Scheme Manager",
        ondelete='set null', 
        index=True,
        domain = [('share','=',False)]
    )
    start_date = fields.Date(
        string="Start Date", 
        copy=False,
    )
    end_date = fields.Date(
        string="End Date", 
        copy=False,
    )
    decision_start_date = fields.Date(
        string="Decision Start Date", 
        copy=False,
    )
    decision_end_date = fields.Date(
        string="Decision End Date", 
        copy=False,
    )

    organization_id = fields.Many2one(
        comodel_name='servicereferralagreement.organization',
        string='Organization',
        ondelete='set null',
    )
    registration_number_id = fields.Many2one(
        comodel_name='servicereferralagreement.registrynumber',
        string='Registration Number',
        ondelete='set null',
    )
    customer_id = fields.Many2one(
        'res.partner', 
        string="Customer",
        ondelete='set null',
    )


    @api.depends('purchase_order_id')
    def _get_name_agreement(self):
        for rec in self:
            rec.title = rec.purchase_order_id.name + "-" + str(rec.id)
    
    def action_cancel(self):
        self.ensure_one()
        self.write({"document_status": "cancel"})

    
    def notify_agreement_accept(self, message):
        odoo_bot = self.env.ref('base.partner_root')
        self.message_post(
            body=message,
            message_type='notification',
            author_id=odoo_bot.id
        )
from odoo import fields, models, api, _
from logging import getLogger
import uuid
import base64

_logger = getLogger(__name__)

class PaoGlobalgapFansRequest(models.Model):
    _name = "pao.globalgap.fans.request"
    _description = "GlobalGAP fans request"
    _rec_name = 'title'

    @api.model
    def _default_access_token(self):
        return uuid.uuid4().hex

    def _get_name_request(self):
        for rec in self:
            rec.title = "FR" + str(rec.id)

    title = fields.Char(
        string='name', 
        compute='_get_name_request'
    )
    capturist_id = fields.Many2one(
        'res.partner', 
        string="Capturist customer",
    )
    capturist_email = fields.Char(
        string="Capturist customer Email",
    )
    follower_ids = fields.Many2many('res.partner', string="Copy to")
    
    signer_id = fields.Many2one(
        'res.partner', 
        string="Signer",
    )
    signer_email = fields.Char(
        string="Signer Email",
    )
    request_url = fields.Char(
        string="URL para firmar",
    )
    signature_date = fields.Date(
        string="Signature date",
    )
    signature_name = fields.Char(
        'Signature name',
        copy=False,
    )
    signature = fields.Binary(
        string="Signature", 
        copy=False,
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        ondelete='set null',
    )
    attachment_id = fields.Many2one(
        string="Document",
        comodel_name='ir.attachment',
        ondelete='restrict',
        copy=False,
    )
    attachment_datas = fields.Binary(
        related='attachment_id.datas',
        string="Fan",
    )
    attachment_name = fields.Char(
        related='attachment_id.name',
    )
    

    request_status = fields.Selection(
        selection=[
            ('draft', "Draft"),
            ('sent', "Sent"),
            ('review', "In review"),
            ('correction', "Correction request"),
            ('annulled', "Annulled"),
            ('rejected', "Rejected"),
            ('approved', "Approved"),
        ],
        string="Request Status",
        readonly=True, copy=False, index=True,
        default='draft'
    )
    access_token = fields.Char(
        'Security Token', 
        default=_default_access_token,
        copy=False,
    )
    organization_id = fields.Many2one(
        comodel_name='pao.globalgap.organization',
        string='GLOBALG.A.P Organization',
        ondelete='restrict',
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        ondelete='set null',
    )

    def action_approve(self):
        for rec in self:
            old_attachment_id = None
            filename = "GlobalGAP_Application_%s_%s.%s" % (rec.title,rec.organization_id.name, "pdf")
            pdf = rec.env.ref('pao_globalgap_fans.globalgap_application_report').sudo()._render_qweb_pdf([rec], data= {"values":rec})[0]
            attachment = rec.env['ir.attachment'].sudo().create({
                'name': filename,
                'datas': base64.b64encode(pdf),
                'res_model': 'pao.globalgap.fans.request',
                'res_id': rec.id,
                'type': 'binary',  # override default_type from context, possibly meant for another model!
            })
            if rec.attachment_id:
                old_attachment_id = rec.attachment_id.id
            rec.write({"request_status": "approved", "attachment_id": attachment.id})
            if old_attachment_id:
                rec.env['ir.attachment'].sudo().search([("id","=",old_attachment_id),("res_id","=",rec.id),("res_model","=","pao.globalgap.fans.request")]).unlink()

        
    
    def action_cancel(self):
        for rec in self:
            rec.write({"request_status": "annulled"})


    
    def resend_fans_request(self):
        self.ensure_one()
        return {
            'name': _('Fans Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'pao.globalgap.send.fans.request',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_fans_request_id': self.id,
                'default_capturist_id': self.capturist_id
            }
        }

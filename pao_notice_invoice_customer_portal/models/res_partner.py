from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"

    pao_upload_invoice_portal = fields.Boolean(
        string="Se debe subir factura al portal"
    )
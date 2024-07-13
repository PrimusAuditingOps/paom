from odoo import fields, models, api



class ResPartner(models.Model):
    _inherit = 'res.partner'

    st_supplier_taxes_id = fields.Many2one('suppliertaxes.supplier.taxes',
                                           string="Supplier taxes",
                                           ondelete='set null')
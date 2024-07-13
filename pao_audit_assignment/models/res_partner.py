from odoo import fields, models, api




class ResPartner(models.Model):
    _inherit = 'res.partner'

    aa_product_ids = fields.Many2many('product.product',
                                      'audit_assignment_product_res_partner_rel',
                                      'res_partner_id', 'product_product_id',
                                       string='Product')
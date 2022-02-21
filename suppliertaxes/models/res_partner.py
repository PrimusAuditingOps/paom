from odoo import fields, models, api
from logging import getLogger

_logger = getLogger(__name__)
class Partner(models.Model):
    _inherit='res.partner'

    st_supplier_taxes_id = fields.Many2one(
        string="Supplier taxes",
        comodel_name='suppliertaxes.supplier.taxes',
        ondelete='set null',
    )
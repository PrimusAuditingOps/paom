# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pao_sa_addon_id = fields.Many2one(
        comodel_name='pao.sa.addon',
        string='SA Add-On',
        ondelete='restrict',
        help="Chile GLOBALG.A.P. SA (CERT-008): the product is this add-on and checks its box in point 7.",
    )
    pao_sa_is_fee = fields.Boolean(
        string='Is an SA Fee',
        help="Chile GLOBALG.A.P. SA (CERT-008): the product is a fee and gets its own line from point 9 on.",
    )

    @api.constrains('pao_sa_addon_id', 'pao_sa_is_fee', 'is_travel_expenses')
    def _check_pao_sa_single_type(self):
        """A product is either the audit service, an add-on, a fee or a travel expense, never two of them."""
        for template in self:
            types = [bool(template.pao_sa_addon_id), template.pao_sa_is_fee, template.is_travel_expenses]
            if sum(types) > 1:
                raise ValidationError(_(
                    "The product '%(product)s' can only be one of: SA add-on, SA fee or travel expense.",
                    product=template.display_name,
                ))

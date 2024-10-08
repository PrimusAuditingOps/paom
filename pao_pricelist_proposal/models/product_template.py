from odoo import models, fields, api
from odoo.exceptions import ValidationError
from logging import getLogger
_logger = getLogger(__name__)

class ProductTemplateInherit(models.Model):

    _inherit = 'product.template'
    
    def copy(self, default=None):
        # Ensure default is a dictionary, if not already provided
        default = dict(default or {})
        # Set the name field to an empty string in the copied record
        default['name'] = ''
        # Call the super method with the updated default values
        return super(ProductTemplateInherit, self).copy(default)
    
    @api.model
    def create(self, vals):
        self._check_name_translations(vals)
        return super(ProductTemplateInherit, self).create(vals)

    def write(self, vals):
        self._check_name_translations(vals)
        return super(ProductTemplateInherit, self).write(vals)

    def _check_name_translations(self, vals):
        # Check if the name is set in each active language
        # if 'name' in vals and not vals['name']:
        #     raise ValidationError("Please set a name before saving the product.")

        # Ensure translations are also set
        for lang in self.env['res.lang'].search([]).mapped('code'):
            translated_name = self.with_context(lang=lang).name_get()[0][1]
            _logger.warning(self.with_context(lang=lang).name_get())
            if translated_name and not translated_name.strip():
                raise ValidationError(
                    f"Please set a translated name for the language: {lang}"
                )
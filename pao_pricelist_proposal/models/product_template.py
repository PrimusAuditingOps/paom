from odoo import models, api, _
from odoo.exceptions import UserError

class ProductTemplateInherit(models.Model):

    _inherit = 'product.template'
    
    def copy(self, default=None):
        # Ensure default is a dictionary, if not already provided
        default = dict(default or {})
        # Set the name field to an empty string in the copied record
        default['name'] = ''
        # Call the super method with the updated default values
        return super(ProductTemplateInherit, self).copy(default)
    
    @api.constrains("name")
    def _check_existing_record_translations(self):
        if self._origin:  # Check if the record is an existing one
            default_lang = self.env.lang
            for lang in self.env.langs:
                if lang.code != default_lang:
                    if not self.with_context(lang=lang.code).name:
                        raise UserError("Translations for 'Name' are missing in language '%s'. Please set them before updating the record." % lang.code)
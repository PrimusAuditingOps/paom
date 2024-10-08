from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplateInherit(models.Model):

    _inherit = 'product.template'
    
    def copy(self, default=None):
        # Ensure default is a dictionary, if not already provided
        default = dict(default or {})
        # Set the name field to an empty string in the copied record
        default['name'] = ''
        # Call the super method with the updated default values
        return super(ProductTemplateInherit, self.with_context(skip_name_check=True)).copy(default)
    
    @api.constrains('name')
    def _check_name_and_translations(self):
        # Skip validation if the context has skip_name_check
        if self.env.context.get('skip_name_check'):
            return

        for record in self:
            if not record.name.strip():
                raise ValidationError(_("Please set a name for the copied product."))

            # Ensure translations are also set
            for lang in self.env['res.lang'].search([]).mapped('code'):
                translated_name = record.with_context(lang=lang).name_get()[0][1]
                if not translated_name.strip():
                    raise ValidationError(
                        _("Please set a translated name for the language: %s") % lang
                    )
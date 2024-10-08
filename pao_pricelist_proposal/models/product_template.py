from odoo import models, _
from odoo.exceptions import ValidationError

class ProductTemplateInherit(models.Model):

    _inherit = 'product.template'
    
    def copy(self, default=None):
        # Ensure default is a dictionary, if not already provided
        default = dict(default or {})
        # Set the name field to an empty string in the copied record
        default['name'] = ''
        # Call the super method with the updated default values
        return super(ProductTemplateInherit, self).copy(default)
    
    def write(self, vals):
        if 'name' in vals:
            # Validate translations only when the `name` field is modified
            self._check_translations_set() 
        return super(ProductTemplateInherit, self).write(vals)

    def _check_translations_set(self):
        for record in self:
            translations = record.with_context(active_test=False).env['ir.translation'].search([
                ('name', '=', 'product.template,name'),
                ('res_id', '=', record.id),
                ('lang', '!=', False)  # Only check non-default languages
            ])
            for translation in translations:
                if not translation.value:
                    # Raise an error if any translation is empty
                    raise ValidationError(_(
                        "The translation for the field 'name' in language '%s' cannot be empty after creation."
                    ) % translation.lang)
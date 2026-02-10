from odoo import fields, models, api


class PurchaseSelectOrganizationsWizard(models.TransientModel):
    _name = 'purchase.select.organization.wizard'
    _description = 'Purchase Select Organization Wizard'

    purchase_order_id = fields.Many2one(
        'purchase.order',
        required=True,
        readonly=True
    )

    organization_ids = fields.Many2many(
        'servicereferralagreement.organization',
        'pao_purchase_select_organization_wizard_rel',
        'wizard_id', 'organization_id',
        string='Organization'
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        po = self.env['purchase.order'].browse(
            self.env.context.get('default_purchase_order_id')
        )

        organizations = po.order_line.mapped('organization_id')

        res.update({
            'purchase_order_id': po.id,
            'organization_ids': [(6, 0, organizations.ids)],
        })

        return res

    def action_confirm(self):
        self.ensure_one()

        po = self.purchase_order_id
        selected_organizations = self.organization_ids

        lines_to_remove = po.order_line.filtered(
            lambda l: l.organization_id not in selected_organizations
        )

        lines_to_remove.unlink()
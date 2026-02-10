class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    def action_open_select_organization_wizard(self):
        self.ensure_one()

        organizations = self.order_line.mapped('organization_id')

        return {
            'name': 'Seleccionar Organizaciones',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.select.organization.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
                'available_organization_ids': organizations.ids,
            }
        }
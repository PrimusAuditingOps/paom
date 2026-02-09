from odoo import models, fields, api, _

class ProjectTask(models.Model):

    _inherit='account.move'
    
    auto_exchange_rate_lines_value = fields.Float(string="Automatic Exchange Rate")
    
    def update_exchange_rate_lines_action(self):
        for move in self:
            rate = move.auto_exchange_rate_lines_value

            if move.state != 'draft' or not rate:
                continue

            for line in move.invoice_line_ids:
                if line.price_unit:
                    new_price = line.price_unit * rate
                    line.price_unit = new_price
    
    # def _check_partner_id_has_the_same_company(self):
    #     for rec in self:
    #         return True
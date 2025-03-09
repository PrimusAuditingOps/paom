from odoo import models, fields, api

class PurchaseReportInherit(models.Model):
    _inherit = "purchase.report"

    pao_price_in_house_auditor = fields.Float(string="In House Auditor Price")
    
    def _select(self):
        return super(PurchaseReportInherit, self)._select() + ", l.pao_price_in_house_auditor as pao_price_in_house_auditor"

    def _group_by(self):
        return super(PurchaseReportInherit, self)._group_by() + ", l.pao_price_in_house_auditor"


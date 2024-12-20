from odoo import fields, models, api

class SaleReport(models.Model):
    _inherit = 'sale.report'

    sale_order_line_id = fields.Many2one("sale.order.line", string="Sale Order Line")
    sale_order_id = fields.Many2one(related="sale_order_line_id.order_id")
    purchase_order_id = fields.One2many(related="sale_order_id.purchase_order_id")
    organization_id = fields.Many2one('servicereferralagreement.organization', string="Organization", compute="_get_po_organization")
    registration_number_id = fields.Many2one('servicereferralagreement.registrynumber', string="Registration Number", compute="_get_po_registration_number")
    audit_date = fields.Date(string="Audit Date", compute="_get_po_audit_date")
    vendor_id = fields.Many2one(related="purchase_order_id.partner_id")
    coordinator_id = fields.Many2one(related="purchase_order_id.coordinator_id")

    def _select_sale(self):
        select_ = super(SaleReport, self)._select_sale()
        select_ += ', l.id as sale_order_line_id'
        return select_
    
    def _group_by_sale(self):
        groupby_ = super(SaleReport, self)._group_by_sale()
        groupby_ += ', l.id'
        return groupby_
                    
    @api.depends('purchase_order_id.order_line', 'purchase_order_id.state')
    def _get_po_registration_number(self):
        for rec in self:
            rec.registration_number_id = None
            valid_po = rec.purchase_order_id.filtered(lambda po: po.state != 'cancel')
            if valid_po:
                first_po = valid_po[0]
                po_line_with_rn = first_po.order_line.filtered('registrynumber_id')
                so_line_with_rn = rec.sale_order_id.order_line.filtered('registrynumber_id')
                if po_line_with_rn:
                    rec.registration_number_id = po_line_with_rn[0].registrynumber_id.id
                elif so_line_with_rn:
                    rec.registration_number_id = so_line_with_rn[0].registrynumber_id.id

                
    @api.depends('purchase_order_id.order_line', 'purchase_order_id.state')
    def _get_po_organization(self):
        for rec in self:
            rec.organization_id = None
            valid_po = rec.purchase_order_id.filtered(lambda po: po.state != 'cancel')
            if valid_po:
                first_po = valid_po[0]
                po_line_with_org = first_po.order_line.filtered('organization_id')
                so_line_with_org = rec.sale_order_id.order_line.filtered('organization_id')
                if po_line_with_org:
                    rec.organization_id = po_line_with_org[0].organization_id.id
                elif so_line_with_org:
                    rec.organization_id = so_line_with_org[0].organization_id.id
                    
    @api.depends('purchase_order_id.order_line', 'purchase_order_id.state')
    def _get_po_audit_date(self):
        for rec in self:
            rec.audit_date = None
            valid_po = rec.purchase_order_id.filtered(lambda po: po.state != 'cancel')
            if valid_po:
                first_po = valid_po[0]
                po_line_with_date = first_po.order_line.filtered('service_start_date')
                so_line_with_date = rec.sale_order_id.order_line.filtered('service_start_date')
                if po_line_with_date:
                    rec.audit_date = po_line_with_date[0].service_start_date
                elif so_line_with_date:
                    rec.audit_date = so_line_with_date[0].service_start_date


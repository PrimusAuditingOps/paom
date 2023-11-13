from odoo import fields, models
from logging import getLogger

_logger = getLogger(__name__)

class AccountMove(models.Model):
    _inherit='account.move'
    
    pao_so_date = fields.Datetime(
        string='Order Date',
        compute="_get_so_date",
    )
    
    
    pao_so_salesman = fields.Many2one(
        string="Salesman",
        comodel_name='res.users',
        compute="_get_so_salesman",
    )
    pao_so_team_id = fields.Many2one(
        string="Sales team",
        comodel_name='crm.team',
        compute="_get_so_sales_team",
    )
    pao_so_categories = fields.Many2many(
        string="Categories",
        comodel_name='res.partner.category',
        compute="_get_so_categories",
    )
    pao_so_schemes = fields.Text(
        string="Schemes",
        compute="_get_schemes",
    )

    def _get_schemes(self):
        scheme_list = []
        productqty = 0
        schemes = ""
        for rec in self:
            for r in rec.invoice_line_ids.sorted(key=lambda r: (r.product_id.id)):
                if r.product_id.can_be_commissionable and r.product_id.product_tmpl_id.categ_id.paa_schem_id:
                    if r.product_id.product_tmpl_id.categ_id.paa_schem_id.id not in scheme_list:
                        scheme_list.append(r.product_id.product_tmpl_id.categ_id.paa_schem_id.id)
                        schemes += r.product_id.product_tmpl_id.categ_id.paa_schem_id.name if schemes == "" else ", " + r.product_id.product_tmpl_id.categ_id.paa_schem_id.name
                   
            rec.pao_so_schemes= schemes
            

    def _get_so_date(self):
        for rec in self:
            if rec.invoice_origin:
                recSaleOrder = rec.env["sale.order"].search([("name", '=', rec.invoice_origin)])
                if recSaleOrder.date_order:
                    rec.pao_so_date = recSaleOrder.date_order
                else:
                    rec.pao_so_date = None
            else:
                    rec.pao_so_date = None
    def _get_so_salesman(self):
        for rec in self:

            if rec.move_type == "out_invoice" and rec.invoice_origin != "":
                recSaleOrder = rec.env["sale.order"].search([("name", '=', rec.invoice_origin)])
                if recSaleOrder.user_id.id:
                    rec.pao_so_salesman = recSaleOrder.user_id.id
                else:
                    rec.pao_so_salesman = None
            else:
                rec.pao_so_salesman = None
    def _get_so_sales_team(self):
        for rec in self:
            if rec.invoice_origin:
                recSaleOrder = rec.env["sale.order"].search([("name", '=', rec.invoice_origin)])
                if recSaleOrder.team_id.id:
                    rec.pao_so_team_id = recSaleOrder.team_id.id
                else:
                    rec.pao_so_team_id = None
            else:
                rec.pao_so_team_id = None
    def _get_so_categories(self):
        for rec in self:
            if rec.invoice_origin:
                recSaleOrder = rec.env["sale.order"].search([("name", '=', rec.invoice_origin)])
                if recSaleOrder.partner_id.category_id:
                    rec.pao_so_categories = recSaleOrder.partner_id.category_id
                else:
                    rec.pao_so_categories = None
            else:
                rec.pao_so_categories = None

   
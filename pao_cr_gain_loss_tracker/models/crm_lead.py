from datetime import datetime, timedelta
from odoo import fields, models, api, _
from logging import getLogger

_logger = getLogger(__name__)
class CRMLead(models.Model):

    _inherit='crm.lead'
    
    coordinator_id = fields.Many2one(
        string="Coordinator",
        comodel_name='res.users',
        compute='_get_coordinator',
        store=True,
        copy=False,
        
    )
    pao_scheme_id = fields.Many2one(
        comodel_name = 'pao.cr.schemes', 
        string='Scheme', 
        help='Select Scheme', 
        ondelete='restrict', 
    )
    pao_gain_or_loss = fields.Selection(
        selection=[
            ('gain', "Gain"),
            ('loss', "Loss"),
            ('pending', "Pending")
        ],
        string="Gain or lost", 
        compute='_get_gain_or_lost',
        store=True,
        copy=False,
    )

    pao_origination_month = fields.Selection(
        selection=[
            ('1', "January"),
            ('2', "Febrary"),
            ('3', "March"),
            ('4', "April"),
            ('5', "May"),
            ('6', "June"),
            ('7', "July"),
            ('8', "August"),
            ('9', "September"),
            ('10', "October"),
            ('11', "November"),
            ('12', "December"),
        ],
        string="Origination month", 
        compute='_get_origination_mont',
        store=True,
        copy=False,
    )
    pao_origination_year = fields.Char(
        string="Origination year", 
        compute='_get_origination_year',
        store=True,
        copy=False,
    )


    pao_gain_loss_date = fields.Date(
        string="Gain/Loss date", 
        compute='_get_gain_loss_date',
        store=True,
        copy=False,
    )

    pao_gain_loss_month = fields.Selection(
        selection=[
            ('1', "January"),
            ('2', "Febrary"),
            ('3', "March"),
            ('4', "April"),
            ('5', "May"),
            ('6', "June"),
            ('7', "July"),
            ('8', "August"),
            ('9', "September"),
            ('10', "October"),
            ('11', "November"),
            ('12', "December"),
        ],
        string="Gain/Loss month", 
        compute='_get_gain_loss_month',
        store=True,
        copy=False,
    )
    pao_gain_loss_year = fields.Char(
        string="Gain/Loss year", 
        compute='_get_gain_loss_year',
        store=True,
        copy=False,
    )


    pao_closed_month = fields.Selection(
        selection=[
            ('1', "January"),
            ('2', "Febrary"),
            ('3', "March"),
            ('4', "April"),
            ('5', "May"),
            ('6', "June"),
            ('7', "July"),
            ('8', "August"),
            ('9', "September"),
            ('10', "October"),
            ('11', "November"),
            ('12', "December"),
        ],
        string="Closed month", 
        compute='_get_closed_month',
        store=True,
        copy=False,
    )
    pao_closed_year = fields.Char(
        string="Closed year", 
        compute='_get_closed_year',
        store=True,
        copy=False,
    )

    pao_quoute_number = fields.Char(
        string="Quote number", 
        compute='_get_quote_number',
        store=True,
        copy=False,
    )

    pao_number_of_audits = fields.Integer(
        string="Number of audits", 
        compute='_get_number_of_audits',
        store=True,
        copy=False,
    )

    pao_current_customer_partner = fields.Selection(
        related='partner_id.pao_current_customer', 
        string='Current customer', 
        readonly=True, 
        store=True
    )

    pao_previous_cb_partner = fields.Many2one(
        'pao.cr.cb', 
        related='partner_id.pao_previous_cb_id', 
        string='Previous CB', 
        readonly=True, 
        store=True
    )

    pao_new_cb_partner = fields.Many2one(
        'pao.cr.cb', 
        related='partner_id.pao_new_cb_id', 
        string='New CB', 
        readonly=True, 
        store=True
    )
    pao_city_id_partner = fields.Many2one(
        'res.city', 
        related='partner_id.city_id', 
        string='Customer city', 
        readonly=True, 
        store=True
    )
    pao_state_id_partner = fields.Many2one(
        'res.country.state', 
        related='partner_id.state_id', 
        string='Customer state', 
        readonly=True, 
        store=True
    )
    pao_country_id_partner = fields.Many2one(
        'res.country', 
        related='partner_id.country_id', 
        string='Customer country', 
        readonly=True, 
        store=True
    )

    pao_consultant_referral = fields.Text(
        string="Consultant/Referral", 
        compute='_get_consultant_referral',
        store=True,
        copy=False,
    )

    
    @api.depends('probability')
    def _get_gain_or_lost(self):
        for rec in self:
            if rec.probability <= 0 :
               rec.pao_gain_or_loss = "loss"
            elif rec.probability >= 100:
                rec.pao_gain_or_loss = "gain"
            else:
                rec.pao_gain_or_loss = "pending"


    @api.depends('order_ids.order_line')
    def _get_coordinator(self):
       for rec in self:
            for quote in rec.order_ids.filtered_domain([('state', '!=', 'cancel')]).sorted(key=lambda r: (r.id)):
                for line in quote.order_line:
                    if line.coordinator_id:
                        rec.coordinator_id = line.coordinator_id
                        break
               

    @api.depends('partner_id.promotor_id','partner_id.cgg_group_id')
    def _get_consultant_referral(self):
        for rec in self:
            if rec.partner_id.promotor_id:
                rec.pao_consultant_referral = rec.partner_id.promotor_id.name
            if rec.partner_id.cgg_group_id:
                rec.pao_consultant_referral = rec.partner_id.cgg_group_id.name if not rec.pao_consultant_referral else rec.pao_consultant_referral + "/" + rec.partner_id.cgg_group_id.name



    @api.depends('order_ids.order_line')
    def _get_number_of_audits(self):
        for rec in self:
            for quote in rec.order_ids.filtered_domain([('state', '!=', 'cancel')]).sorted(key=lambda r: (r.id)):
                qty = 0
                for line in quote.order_line:
                    if line.product_template_id.can_be_commissionable:
                        qty+= line.product_uom_qty
                
                rec.pao_number_of_audits = qty
                break

    @api.depends('order_ids')
    def _get_quote_number(self):
        for rec in self:
            for quote in rec.order_ids.filtered_domain([('state', '!=', 'cancel')]).sorted(key=lambda r: (r.id)):
                rec.pao_quoute_number = quote.name
                break
    @api.depends('date_open')
    def _get_origination_mont(self):
        for rec in self:
            if rec.date_open:
                rec.pao_origination_month = str(rec.date_open.month)       
            else:
                rec.pao_origination_month = None

    @api.depends('date_open')
    def _get_origination_year(self):
        for rec in self:
            if rec.date_open:
                rec.pao_origination_year = str(rec.date_open.year)       
            else:
                rec.pao_origination_year = None

    @api.depends('order_ids.order_line')
    def _get_gain_loss_date(self):
       for rec in self:
            for quote in rec.order_ids.filtered_domain([('state', '!=', 'cancel')]).sorted(key=lambda r: (r.id)):
                preview_date = None
                for line in quote.order_line:
                    if line.service_start_date:
                        if not preview_date:
                            preview_date = line.service_start_date
                        elif line.service_start_date < preview_date:
                            preview_date = line.service_start_date
                            
                rec.pao_gain_loss_date = preview_date
                break
    @api.depends('pao_gain_loss_date')
    def _get_gain_loss_month(self):
        for rec in self:
            if rec.pao_gain_loss_date:
                rec.pao_gain_loss_month = str(rec.pao_gain_loss_date.month)       
            else:
                rec.pao_gain_loss_month = None

    @api.depends('pao_gain_loss_date')
    def _get_gain_loss_year(self):
        for rec in self:
            if rec.pao_gain_loss_date:
                rec.pao_gain_loss_year = str(rec.pao_gain_loss_date.year)       
            else:
                rec.pao_gain_loss_year = None

    



    @api.depends('date_closed')
    def _get_closed_month(self):
        for rec in self:
            if rec.date_closed:
                rec.pao_closed_month = str(rec.date_closed.month)       
            else:
                rec.pao_closed_month = None

    @api.depends('date_closed')
    def _get_closed_year(self):
        for rec in self:
            if rec.date_closed:
                rec.pao_closed_year = str(rec.date_closed.year)       
            else:
                rec.pao_closed_year = None

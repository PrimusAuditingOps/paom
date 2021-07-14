from odoo import tools
from odoo import fields, models


class ServiceReferralAgreementAgenda(models.Model):
    _name = "servicereferralagreement.agenda"
    _description = "Auditor Agenda"
    _auto = False
    _rec_name = 'order_id'
    _order = 'service_start_date desc'


    id = fields.Integer('ID', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Auditor', readonly=True)
    partner_ref = fields.Char('Auditor Reference', readonly=True)
    order_id = fields.Many2one('purchase.order', 'Purchase Order', readonly=True)
    service_start_date = fields.Date('Service Start Date', readonly=True)
    service_end_date = fields.Date('Service End Date', readonly=True)
    coordinator_id = fields.Many2one('res.users', 'Coordinator', readonly=True)
    all_day = fields.Boolean(
        string="All Day",
        default=True,
    )
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], 'Status', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        select_ = """
            row_number() over() as id,
            po.partner_id as partner_id,
            po.partner_ref as partner_ref,
            po.id as order_id,
            pl.service_start_date as service_start_date,
            pl.service_end_date as service_end_date,
            po.coordinator_id as coordinator_id,
            true as all_day,
            po.state as state
        """

        for field in fields.values():
            select_ += field

        from_ = """
                purchase_order_line pl 
                inner join purchase_order po on (po.id=pl.order_id) 
                inner join res_partner partner on po.partner_id = partner.id     
                %s
        """ % from_clause

        groupby_ = """
            po.partner_id,
            po.partner_ref,
            po.id,
            pl.service_start_date,
            pl.service_end_date,
            po.coordinator_id,
            all_day %s
        """ % (groupby)

        return '%s (SELECT %s FROM %s GROUP BY %s)' % (with_, select_, from_, groupby_)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))


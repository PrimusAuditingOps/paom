from odoo import fields, models



class PaoServicereFerralAgreementAuditorExchangeRate(models.Model):
    _name = 'servicereferralagreement.auditorexchangerate'
    _description = 'Auditor Exchange Rate'
    _rec_name = "currency_id"
    
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  help='Select currency', ondelete='restrict',
                                  required=True)
    exchange_rate = fields.Float(string='Rate', help='Enter Rate', required=True)
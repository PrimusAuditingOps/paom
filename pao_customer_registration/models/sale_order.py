from odoo import api, fields, models
from logging import getLogger
from werkzeug.urls import url_join
_logger = getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        
        partner = vals.get('partner_id')
        if partner: 
            recPartner = self.env["res.partner"].browse(partner)
            for rec in recPartner:
                recRegistration = self.env["pao.customer.registration"].search([("res_partner_id", "=", rec.id)])
                if not recRegistration:
                    cr = self.env['pao.customer.registration'].create({
                        'contact_id': rec.id,
                        'res_partner_id': rec.id,
                        'name': rec.name,
                        'country_id': rec.country_id.id,
                        'state_id': rec.state_id.id,
                        'city_id': rec.city_id.id,
                        'street_name': rec.street,
                        'street_number': rec.street2,
                        'zip': rec.zip,
                        'phone': rec.phone,
                        'email': rec.email,
                        'fiscal_regime': rec.l10n_mx_edi_fiscal_regime,
                        'vat': rec.vat,
                    })
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    form_url = url_join(base_url, '/pao/customer/registration/%s/%s' % (cr.id, cr.access_token))
                    cr.write({"form_url": form_url})
        records = super(SaleOrder, self).create(vals)
        
        return records

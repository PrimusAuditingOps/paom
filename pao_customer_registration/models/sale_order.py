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
            for recP in recPartner:
                recRegistration = self.env["pao.customer.registration"].search([("res_partner_id", "=", recP.id)])
                if not recRegistration:
                    cr = self.env['pao.customer.registration'].create({
                        'contact_id': recP.id,
                        'res_partner_id': recP.id,
                        'name': recP.name,
                        'country_id': recP.country_id.id,
                        'state_id': recP.state_id.id,
                        'city_id': recP.city_id.id,
                        'street_name': recP.street,
                        'street_number': recP.street2,
                        'zip': recP.zip,
                        'phone': recP.phone,
                        'email': recP.email,
                        'fiscal_regime': recP.l10n_mx_edi_fiscal_regime,
                        'vat': recP.vat,
                    })
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    form_url = url_join(base_url, '/pao/customer/registration/%s/%s' % (cr.id, cr.access_token))
                    cr.write({"form_url": form_url})
        records = super(SaleOrder, self).create(vals)
        return records

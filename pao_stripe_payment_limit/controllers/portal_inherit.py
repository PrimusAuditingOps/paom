from odoo import http, _
from odoo.http import request
import werkzeug
from odoo.addons.payment.controllers.portal import PaymentPortal
from odoo.addons.account_payment.controllers.payment import PaymentPortal as AccountPaymentPortal
import logging
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.payment import utils as payment_utils
import urllib.parse
from odoo.fields import Command

_logger = logging.getLogger(__name__)
class CustomPaymentProcessing(PaymentPortal):
    
    @http.route(
        '/payment/pay', type='http', methods=['GET'], auth='public', website=True, sitemap=False,
    )
    def payment_pay(
        self, reference=None, amount=None, currency_id=None, partner_id=None, company_id=None,
        access_token=None, **kwargs
    ):
        invoice_id = kwargs.get('invoice_id')
        
        if invoice_id:
            
            domain = [
                ('id', '=', int(invoice_id)),
            ]
            invoices = request.env['account.move'].sudo().search(domain, limit=1)
            
            domain = [
                ('invoice_ids', 'in', [invoice_id]),
                # ('currency_id', '=', int(currency_id)),
                ('partner_id', '=', int(invoices.partner_id.id)), 
            ]
            
            transactions = request.env['payment.transaction'].sudo().search(domain)
            amount_paid = 0
            for tx in transactions:
                if tx.state in ('done', 'pending', 'authorized'):
                    amount_paid = amount_paid + int(float(tx.amount))
            
            amount_payment = int(float(amount))
            for inv in invoices:
                if (amount_paid + amount_payment) > inv.amount_total:
                    return request.render('pao_stripe_payment_limit.payment_not_available')
        
        """ Display the payment form with optional filtering of payment options.

        The filtering takes place on the basis of provided parameters, if any. If a parameter is
        incorrect or malformed, it is skipped to avoid preventing the user from making the payment.

        In addition to the desired filtering, a second one ensures that none of the following
        rules is broken:

        - Public users are not allowed to save their payment method as a token.
        - Payments made by public users should either *not* be made on behalf of a specific partner
          or have an access token validating the partner, amount and currency.

        We let access rights and security rules do their job for logged users.

        :param str reference: The custom prefix to compute the full reference.
        :param str amount: The amount to pay.
        :param str currency_id: The desired currency, as a `res.currency` id.
        :param str partner_id: The partner making the payment, as a `res.partner` id.
        :param str company_id: The related company, as a `res.company` id.
        :param str access_token: The access token used to authenticate the partner.
        :param dict kwargs: Optional data passed to helper methods.
        :return: The rendered payment form.
        :rtype: str
        :raise werkzeug.exceptions.NotFound: If the access token is invalid.
        """
        # Cast numeric parameters as int or float and void them if their str value is malformed
        currency_id, partner_id, company_id = tuple(map(
            self._cast_as_int, (currency_id, partner_id, company_id)
        ))
        amount = self._cast_as_float(amount)

        # Raise an HTTP 404 if a partner is provided with an invalid access token
        if partner_id:
            if not payment_utils.check_access_token(access_token, partner_id, amount, currency_id):
                raise werkzeug.exceptions.NotFound()  # Don't leak information about ids.

        user_sudo = request.env.user
        logged_in = not user_sudo._is_public()
        # If the user is logged in, take their partner rather than the partner set in the params.
        # This is something that we want, since security rules are based on the partner, and created
        # tokens should not be assigned to the public user. This should have no impact on the
        # transaction itself besides making reconciliation possibly more difficult (e.g. The
        # transaction and invoice partners are different).
        # partner_is_different = False
        # if logged_in:
        #     partner_is_different = partner_id and partner_id != user_sudo.partner_id.id
        #     partner_sudo = user_sudo.partner_id
        # else:
        #     partner_sudo = request.env['res.partner'].sudo().browse(partner_id).exists()
        #     if not partner_sudo:
        #         return request.redirect(
        #             # Escape special characters to avoid loosing original params when redirected
        #             f'/web/login?redirect={urllib.parse.quote(request.httprequest.full_path)}'
        #         )
        
        partner_is_different = False
        if partner_id or invoice_id:
            partner_sudo = request.env['res.partner'].sudo().browse(partner_id).exists()
            
            if not partner_sudo and invoice_id:
                invoice_sudo = request.env['account.move'].sudo().browse(int(invoice_id)).exists()
                partner_sudo = request.env['res.partner'].sudo().browse(invoice_sudo.partner_id.id).exists()
            else:
                return request.redirect(
                    # Escape special characters to avoid loosing original params when redirected
                    f'/web/login?redirect={urllib.parse.quote(request.httprequest.full_path)}'
                )
        elif logged_in:
            partner_is_different = partner_id and partner_id != user_sudo.partner_id.id
            partner_sudo = user_sudo.partner_id
                
        # Instantiate transaction values to their default if not set in parameters
        reference = reference or payment_utils.singularize_reference_prefix(prefix='tx')
        amount = amount or 0.0  # If the amount is invalid, set it to 0 to stop the payment flow
        company_id = company_id or partner_sudo.company_id.id or user_sudo.company_id.id
        company = request.env['res.company'].sudo().browse(company_id)
        currency_id = currency_id or company.currency_id.id

        # Make sure that the currency exists and is active
        currency = request.env['res.currency'].browse(currency_id).exists()
        if not currency or not currency.active:
            raise werkzeug.exceptions.NotFound()  # The currency must exist and be active.

        # Select all the payment methods and tokens that match the payment context.
        providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
            company_id, partner_sudo.id, amount, currency_id=currency.id, **kwargs
        )  # In sudo mode to read the fields of providers and partner (if logged out).
        payment_methods_sudo = request.env['payment.method'].sudo()._get_compatible_payment_methods(
            providers_sudo.ids,
            partner_sudo.id,
            currency_id=currency.id,
        )  # In sudo mode to read the fields of providers.
        tokens_sudo = request.env['payment.token'].sudo()._get_available_tokens(
            providers_sudo.ids, partner_sudo.id
        )  # In sudo mode to be able to read tokens of other partners and the fields of providers.

        # Make sure that the partner's company matches the company passed as parameter.
        company_mismatch = not PaymentPortal._can_partner_pay_in_company(partner_sudo, company)

        # Generate a new access token in case the partner id or the currency id was updated
        access_token = payment_utils.generate_access_token(partner_sudo.id, amount, currency.id)

        portal_page_values = {
            'res_company': company,  # Display the correct logo in a multi-company environment.
            'company_mismatch': company_mismatch,
            'expected_company': company,
            'partner_is_different': partner_is_different,
        }
        payment_form_values = {
            'show_tokenize_input_mapping': PaymentPortal._compute_show_tokenize_input_mapping(
                providers_sudo, **kwargs
            ),
        }
        payment_context = {
            'reference_prefix': reference,
            'amount': amount,
            'currency': currency,
            'partner_id': partner_sudo.id,
            'providers_sudo': providers_sudo,
            'payment_methods_sudo': payment_methods_sudo,
            'tokens_sudo': tokens_sudo,
            'transaction_route': '/payment/transaction',
            'landing_route': '/payment/confirmation',
            'access_token': access_token,
        }
        rendering_context = {
            **portal_page_values,
            **payment_form_values,
            **payment_context,
            **self._get_extra_payment_form_values(
                **payment_context, currency_id=currency.id, **kwargs
            ),  # Pass the payment context to allow overriding modules to check document access.
        }
        return request.render(self._get_payment_page_template_xmlid(**kwargs), rendering_context)
    
    
class CustomEmailStripePayment(AccountPaymentPortal):
    
    @http.route('/invoice/transaction/<int:invoice_id>', type='json', auth='public')
    def invoice_transaction(self, invoice_id, access_token, **kwargs):
        
        # Check the invoice id and the access token
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except MissingError as error:
            raise error
        except AccessError:
            raise ValidationError(_("The access token is invalid."))
        
        partner_id = invoice_sudo.partner_id
        
        if partner_id:
            domain = [
                    ('id', '=', int(partner_id)), 
                ]
                
            partner = request.env['res.partner'].sudo().search(domain)
            emails = partner.email
            single_email = emails.split(',')[0]
            partner.sudo().write({'email':single_email})
        
        """ Create a draft transaction and return its processing values.

        :param int invoice_id: The invoice to pay, as an `account.move` id
        :param str access_token: The access token used to authenticate the request
        :param dict kwargs: Locally unused data passed to `_create_transaction`
        :return: The mandatory values for the processing of the transaction
        :rtype: dict
        :raise: ValidationError if the invoice id or the access token is invalid
        """

        logged_in = not request.env.user._is_public()
        partner_sudo = request.env.user.partner_id if logged_in else invoice_sudo.partner_id
        self._validate_transaction_kwargs(kwargs)
        kwargs.update({
            'currency_id': invoice_sudo.currency_id.id,
            'partner_id':  invoice_sudo.partner_id.id,
        })  # Inject the create values taken from the invoice into the kwargs.
        tx_sudo = self._create_transaction(
            custom_create_values={'invoice_ids': [Command.set([invoice_id])]}, **kwargs,
        )
        
        if partner_id:
            partner.sudo().write({'email':emails})

        return tx_sudo._get_processing_values()

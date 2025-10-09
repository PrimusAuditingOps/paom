from odoo import api, models, fields

class MexicanAccountReportCustomHandlerInherit(models.AbstractModel):
    _inherit = 'l10n_mx.report.handler'

    def action_get_diot_txt(self, options):
        result = super().action_get_diot_txt(options)

        report = self.env['account.report'].browse(options['report_id'])
        partner_and_values_to_report = self._get_diot_values_per_partner(report, options)

        new_lines = []
        old_lines = result['file_content'].decode('utf-8').split('\n')

        for (partner, values), line in zip(partner_and_values_to_report.items(), old_lines):
            if not line.strip():
                continue

            data = line.split('|')

            # data.append(values.get('extra_info', ''))
            # data[8] = values.get('special_code', '') 
            
            #Columnas vacías
            # 9, 10, 13, 14, 15, 16, 18, 19, 20. 22 - 46,
            
            data[7] = round(float(values.get('paid_8', 0))) or '' # Pagado al 8%
            # data[8] = '' # Notas de credito fronterizas (rara vez tiene info)
            data[11] = round(float(values.get('paid_16', 0))) or '' # Pagado al 16%
            data[12] = round(float(values.get('refunds', 0)) / 0.16) or '' # Reembolso / 0.16
            data[17] = round(float(values.get('paid_8', 0)) * 0.08) or '' # IVA de la región fronteriza (data[7] * 0.08)
            data[21] = round(float(values.get('paid_16', 0)) * 0.16) or '' # IVA de data[11]
            
            
            data[53] = 'test'
            
            new_lines.append('|'.join(str(d) for d in data))

        result['file_content'] = '\n'.join(new_lines).encode('utf-8')
        return result

    ##### ORIGINAL METHOD: ######
    # def action_get_diot_txt(self, options):
    #     report = self.env['account.report'].browse(options['report_id'])
    #     partner_and_values_to_report = self._get_diot_values_per_partner(report, options)

    #     self.check_for_error_on_partner([partner for partner in partner_and_values_to_report])

    #     lines = []
    #     for partner, values in partner_and_values_to_report.items():
    #         if not any([values.get(x) for x in ('paid_16', 'paid_16_non_cred', 'paid_8', 'paid_8_non_cred', 'importation_16', 'paid_0', 'exempt', 'withheld', 'refunds')]):
    #             # don't report if there isn't any amount to report
    #             continue

    #         is_foreign_partner = values['third_party_code'] != '04'
    #         data = [''] * 25
    #         data[0] = values['third_party_code']  # Supplier Type
    #         data[1] = values['operation_type_code']  # Operation Type
    #         data[2] = values['partner_vat_number'] if not is_foreign_partner else '' # Tax Number
    #         data[3] = values['partner_vat_number'] if is_foreign_partner else ''  # Tax Number for Foreigners
    #         data[4] = ''.join(self.str_format(partner.name)).encode('utf-8').strip().decode('utf-8') if is_foreign_partner else ''  # Name
    #         data[5] = values['country_code'] if is_foreign_partner else '' # Country
    #         data[6] = ''.join(self.str_format(values['partner_nationality'])).encode('utf-8').strip().decode('utf-8') if is_foreign_partner else '' # Nationality
    #         data[7] = round(float(values.get('paid_16', 0))) or '' # 16%
    #         data[9] = round(float(values.get('paid_16_non_cred', 0))) or '' # 16% Non-Creditable
    #         data[12] = round(float(values.get('paid_8', 0))) or '' # 8%
    #         data[14] = round(float(values.get('paid_8_non_cred', 0))) or '' # 8% Non-Creditable
    #         data[15] = round(float(values.get('importation_16', 0))) or '' # 16% - Importation
    #         data[20] = round(float(values.get('paid_0', 0))) or '' # 0%
    #         data[21] = round(float(values.get('exempt', 0))) or '' # Exempt
    #         data[22] = round(float(values.get('withheld', 0))) or '' # Withheld
    #         data[23] = round(float(values.get('refunds', 0))) or '' # Refunds

    #         lines.append('|'.join(str(d) for d in data))

    #     diot_txt_result = '\n'.join(lines)
    #     return {
    #         'file_name': report.get_default_report_filename(options, 'txt'),
    #         'file_content': diot_txt_result.encode(),
    #         'file_type': 'txt',
    #     }
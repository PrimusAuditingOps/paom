from logging import getLogger
from odoo.exceptions import ValidationError
from odoo import fields, models, api, _

_logger = getLogger(__name__)
class Partner(models.Model):
    
    _name = 'res.partner'
    _inherit = 'res.partner'

    ctm_ref_bank_pesos = fields.Text(
        string = 'Pesos Reference MXN',
        readonly = True,
        copy=False,
    )
    ctm_ref_bank_dolares = fields.Text(
        string = 'Dollar Reference USD',
        readonly = True,
        copy=False,
    )

    @api.model
    def create(self, vals):
        seq = 0
        if (not self.ctm_ref_bank_pesos or not self.ctm_ref_bank_dolares) and (self.company_type == 'company' or vals.get('company_type') == 'company'):
            seq = self.env['ir.sequence'].next_by_code('referenciasbancarias.refbank')
            vals['ctm_ref_bank_pesos'] = self.generate_reference_pesos(seq)
            vals['ctm_ref_bank_dolares'] = self.generate_reference_usd(seq)
        result = super(Partner, self).create(vals)
        return result
    
    def write(self, vals):
        seq = 0
        for rec in self:
            if (not rec.ctm_ref_bank_pesos or not rec.ctm_ref_bank_dolares) and (vals.get('company_type') == 'company' or rec.company_type == 'company'):
                seq = self.env['ir.sequence'].next_by_code('referenciasbancarias.refbank')
                vals['ctm_ref_bank_pesos'] = self.generate_reference_pesos(seq)
                vals['ctm_ref_bank_dolares'] = self.generate_reference_usd(seq)
        result = super(Partner, self).write(vals)
        return result

    def generate_reference_pesos(self,seq):
        ponderadorFijoNoventaSiete = 97
        ponderadorFijoNoventaNueve = 99
        secuencia = str(seq).zfill(18)
        lstSucursalPesos = [7,0,0,9]
        lstPonderadorSucursal = [23,29,31,37]
        lstCuentaPesos = [4,5,3,4,5,7,5]
        lstPonderarorCuenta = [13,17,19,23,29,31,37]
        lstConcecutivoPesos = list(secuencia)
        lstPonderadorConcecutivo = [19,23,29,31,37,1,2,3,5,7,11,13,17,19,23,29,31,37]

        residuo = 0
        sumTotal = 0
        digitoVerificador = 0

        for i in range(len(lstSucursalPesos)):
            sumTotal += lstSucursalPesos[i] * lstPonderadorSucursal[i]
        for i in range(len(lstCuentaPesos)):
            sumTotal += lstCuentaPesos[i] * lstPonderarorCuenta[i]
        for i in range(len(lstConcecutivoPesos)):
            sumTotal += int(lstConcecutivoPesos[i]) * lstPonderadorConcecutivo[i]


        residuo = sumTotal % ponderadorFijoNoventaSiete
        digitoVerificador = ponderadorFijoNoventaNueve - residuo

        return str(seq)+str(digitoVerificador).zfill(2)

    def generate_reference_usd(self,seq):
        ponderadorFijoNoventaSiete = 97
        ponderadorFijoNoventaNueve = 99
        secuencia = str(seq).zfill(18)
        lstSucursalDolares = [0,8,9,1]
        lstPonderadorSucursal = [23,29,31,37]
        lstCuentaDolares = [9,7,6,6,7,5,2]
        lstPonderarorCuenta = [13,17,19,23,29,31,37]
        lstConcecutivoDolares = list(secuencia)
        lstPonderadorConcecutivo = [19,23,29,31,37,1,2,3,5,7,11,13,17,19,23,29,31,37]

        residuo = 0
        sumTotal = 0
        digitoVerificador = 0

        for i in range(len(lstSucursalDolares)):
            sumTotal += lstSucursalDolares[i] * lstPonderadorSucursal[i]
        for i in range(len(lstCuentaDolares)):
            sumTotal += lstCuentaDolares[i] * lstPonderarorCuenta[i]
        for i in range(len(lstConcecutivoDolares)):
            sumTotal += int(lstConcecutivoDolares[i]) * lstPonderadorConcecutivo[i]


        residuo = sumTotal % ponderadorFijoNoventaSiete
        digitoVerificador = ponderadorFijoNoventaNueve - residuo

        return str(seq)+str(digitoVerificador).zfill(2)
    @api.constrains('ctm_ref_bank_pesos')
    def _check_duplicate_ctm_ref_bank_pesos(self):
        refs = self.env['res.partner'].search([('ctm_ref_bank_pesos', '=', self.ctm_ref_bank_pesos), ('id','!=',self.id)])
        for n in refs:
            raise ValidationError(_("There is already a PESOS reference with this number("+self.ctm_ref_bank_dolares+")"))
    @api.constrains('ctm_ref_bank_dolares')
    def _check_duplicate_ctm_ref_bank_pesos(self):
        refs = self.env['res.partner'].search([('ctm_ref_bank_dolares', '=', self.ctm_ref_bank_dolares), ('id','!=',self.id)])
        for n in refs:
            raise ValidationError(_("There is already a DOLLAR reference with this number ("+self.ctm_ref_bank_dolares+")"))
import base64
from lxml import etree
from odoo import models, fields, api
from logging import getLogger

_logger = getLogger(__name__)


class PAOSatCfdiXmlLine(models.Model):
    _name = 'pao.sat.cfdi.xml.line'
    _description = 'SAT CFDI Lines'

    cfdi_id = fields.Many2one(
        'pao.sat.cfdi.xml',
        string="CFDI",
        ondelete='cascade'
    )
    prod_serv_key = fields.Char(string="Prod/Serv Key")
    description = fields.Text(string="Description")
    quantity = fields.Float(string="Quantity")
    unity_key = fields.Char(string="Unity Key")
    unity = fields.Char(string="Unity")
    unit_value = fields.Float(string="Unit Value")
    amount = fields.Float(string="amount")
    tax_object = fields.Char(string="Tax Object")
    output_tax = fields.Float(string="Output Tax")
    withholding_tax = fields.Float(string="Withholding Tax")


class PAOSatCFDIXml(models.Model):
    _name = 'pao.sat.cfdi.xml'
    _description = 'CFDI Imported from SAT'

    _sql_constraints = [
        ('uuid_unique', 'unique(name)', 'This UUID already exist.')
    ]

    name = fields.Char(string="UUID", index=True)
    vendor_vat = fields.Char(string="Vendor VAT")
    vendor_name = fields.Char(string="Vendor Name")

    customer_vat = fields.Char(string="Customer VAT")
    customer_name = fields.Char(string="Customer name")

    cfdi_date = fields.Datetime(string="CFDI Date")
    total = fields.Float(string="Total")
    subtotal = fields.Float(string="Subtotal")
    currency = fields.Char(string="Currency")
    type_of_receipt = fields.Char(string="type of receipt")
    xml_files = fields.Binary(string="XML")
    file_name = fields.Char(string="File Name")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processed', 'Done'),
    ], default='draft')
    pao_line_ids = fields.One2many(
        'pao.sat.cfdi.xml.line',
        'cfdi_id',
        string="CFDI Lines"
    )
    xml_text = fields.Text(
        string="XML Content",
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, 
        index=True,
        default=lambda self: self.env.company
    )
    sat_cfdi_request_id = fields.Many2one(
        'pao.sat.cfdi.request',
        string='SAT CDFI request',
        ondelete='cascade'
    )
    method_of_payment = fields.Selection(
        [
            ('01', 'Efectivo'),
            ('02', 'Cheque nominativo'),
            ('03', 'Transferencia electrónica de fondos'),
            ('04', 'Tarjeta de crédito'),
            ('05', 'Monedero electrónico'),
            ('06', 'Dinero electrónico'),
            ('08', 'Vales de despensa'),
            ('12', 'Dación en pago'),
            ('13', 'Pago por subrogación'),
            ('14', 'Pago por consignación'),
            ('15', 'Condonación'),
            ('17', 'Compensación'),
            ('23', 'Novación'),
            ('24', 'Confusión'),
            ('25', 'Remisión de deuda'),
            ('26', 'Prescripción o caducidad'),
            ('27', 'A satisfacción del acreedor'),
            ('28', 'Tarjeta de débito'),
            ('29', 'Tarjeta de servicios'),
            ('30', 'Aplicación de anticipos'),
            ('99', 'Por definir'),
        ],
        string="Method of Payment"
    )

    cfdi_use = fields.Selection(
        [
            ('G01', 'Adquisición de mercancías'),
            ('G02', 'Devoluciones, descuentos o bonificaciones'),
            ('G03', 'Gastos en general'),
            ('I01 - I08', 'Inversiones'),
            ('D01 - D10', 'Deducciones Personales'),
            ('D01', 'Honorarios médicos, dentales y hospitalarios'),
            ('D02', 'Gastos médicos por incapacidad o discapacidad'),
            ('D03', 'Gastos funerales'),
            ('D10', 'Pagos por servicios educativos (colegiaturas)'),
            ('S01', 'Sin efectos fiscales'),
            ('CP01', 'Pagos'),
            ('CN01', 'Nómina'),
        ],
        string="CFDI Use"
    )

    payment_method = fields.Char(
        string="Payment Method"
    )
    
    export = fields.Selection(
        [
            ('01', 'No aplica: Operaciones nacionales'),
            ('02', 'Definitiva'),
            ('03', 'Temporal'),
            ('04', 'Definitiva sin enajenación'),
        ],
        string="Export",
    )
    
    type_receipt = fields.Selection(
        [
            ('I', 'Ingreso'),
            ('E', 'Egreso'),
            ('T', 'Traslado'),
            ('N', 'Nómina'),
            ('P', 'Pago'),
        ],
        string="Type of Receipt",
    )

    exchange_rate = fields.Float(
        string="Exchange Rate", 
        default=0.00,
    )
    customer_tax_regime = fields.Selection(
        [
            ('601', 'REGIMEN GENERAL DE LEY PERSONAS MORALES'),
            ('602', 'RÉGIMEN SIMPLIFICADO DE LEY PERSONAS MORALES'),
            ('603', 'PERSONAS MORALES CON FINES NO LUCRATIVOS'),
            ('604', 'RÉGIMEN DE PEQUEÑOS CONTRIBUYENTES'),
            ('605', 'RÉGIMEN DE SUELDOS Y SALARIOS E INGRESOS ASIMILADOS A SALARIOS'),
            ('606', 'RÉGIMEN DE ARRENDAMIENTO'),
            ('607', 'RÉGIMEN DE ENAJENACIÓN O ADQUISICIÓN DE BIENES'),
            ('608', 'RÉGIMEN DE LOS DEMÁS INGRESOS'),
            ('609', 'RÉGIMEN DE CONSOLIDACIÓN'),
            ('610', 'RÉGIMEN RESIDENTES EN EL EXTRANJERO SIN ESTABLECIMIENTO PERMANENTE EN MÉXICO'),
            ('611', 'RÉGIMEN DE INGRESOS POR DIVIDENDOS (SOCIOS Y ACCIONISTAS)'),
            ('612', 'RÉGIMEN DE LAS PERSONAS FÍSICAS CON ACTIVIDADES EMPRESARIALES Y PROFESIONALES'),
            ('613', 'RÉGIMEN INTERMEDIO DE LAS PERSONAS FÍSICAS CON ACTIVIDADES EMPRESARIALES'),
            ('614', 'RÉGIMEN DE LOS INGRESOS POR INTERESES'),
            ('615', 'RÉGIMEN DE LOS INGRESOS POR OBTENCIÓN DE PREMIOS'),
            ('616', 'SIN OBLIGACIONES FISCALES'),
            ('617', 'PEMEX'),
            ('618', 'RÉGIMEN SIMPLIFICADO DE LEY PERSONAS FÍSICAS'),
            ('619', 'INGRESOS POR LA OBTENCIÓN DE PRÉSTAMOS'),
            ('620', 'SOCIEDADES COOPERATIVAS DE PRODUCCIÓN QUE OPTAN POR DIFERIR SUS INGRESOS'),
            ('621', 'RÉGIMEN DE INCORPORACIÓN FISCAL'),
            ('622', 'RÉGIMEN DE ACTIVIDADES AGRÍCOLAS, GANADERAS, SILVÍCOLAS Y PESQUERAS PM'),
            ('623', 'RÉGIMEN DE OPCIONAL PARA GRUPOS DE SOCIEDADES'),
            ('624', 'RÉGIMEN DE LOS COORDINADOS'),
            ('625', 'RÉGIMEN DE LAS ACTIVIDADES EMPRESARIALES CON INGRESOS A TRAVÉS DE PLATAFORMAS TECNOLÓGICAS'),
            ('626', 'RÉGIMEN SIMPLIFICADO DE CONFIANZA')
        ], 
        string="Customer Tax Regime",
    )


    vendor_tax_regime = fields.Selection(
        [
            ('601', 'REGIMEN GENERAL DE LEY PERSONAS MORALES'),
            ('602', 'RÉGIMEN SIMPLIFICADO DE LEY PERSONAS MORALES'),
            ('603', 'PERSONAS MORALES CON FINES NO LUCRATIVOS'),
            ('604', 'RÉGIMEN DE PEQUEÑOS CONTRIBUYENTES'),
            ('605', 'RÉGIMEN DE SUELDOS Y SALARIOS E INGRESOS ASIMILADOS A SALARIOS'),
            ('606', 'RÉGIMEN DE ARRENDAMIENTO'),
            ('607', 'RÉGIMEN DE ENAJENACIÓN O ADQUISICIÓN DE BIENES'),
            ('608', 'RÉGIMEN DE LOS DEMÁS INGRESOS'),
            ('609', 'RÉGIMEN DE CONSOLIDACIÓN'),
            ('610', 'RÉGIMEN RESIDENTES EN EL EXTRANJERO SIN ESTABLECIMIENTO PERMANENTE EN MÉXICO'),
            ('611', 'RÉGIMEN DE INGRESOS POR DIVIDENDOS (SOCIOS Y ACCIONISTAS)'),
            ('612', 'RÉGIMEN DE LAS PERSONAS FÍSICAS CON ACTIVIDADES EMPRESARIALES Y PROFESIONALES'),
            ('613', 'RÉGIMEN INTERMEDIO DE LAS PERSONAS FÍSICAS CON ACTIVIDADES EMPRESARIALES'),
            ('614', 'RÉGIMEN DE LOS INGRESOS POR INTERESES'),
            ('615', 'RÉGIMEN DE LOS INGRESOS POR OBTENCIÓN DE PREMIOS'),
            ('616', 'SIN OBLIGACIONES FISCALES'),
            ('617', 'PEMEX'),
            ('618', 'RÉGIMEN SIMPLIFICADO DE LEY PERSONAS FÍSICAS'),
            ('619', 'INGRESOS POR LA OBTENCIÓN DE PRÉSTAMOS'),
            ('620', 'SOCIEDADES COOPERATIVAS DE PRODUCCIÓN QUE OPTAN POR DIFERIR SUS INGRESOS'),
            ('621', 'RÉGIMEN DE INCORPORACIÓN FISCAL'),
            ('622', 'RÉGIMEN DE ACTIVIDADES AGRÍCOLAS, GANADERAS, SILVÍCOLAS Y PESQUERAS PM'),
            ('623', 'RÉGIMEN DE OPCIONAL PARA GRUPOS DE SOCIEDADES'),
            ('624', 'RÉGIMEN DE LOS COORDINADOS'),
            ('625', 'RÉGIMEN DE LAS ACTIVIDADES EMPRESARIALES CON INGRESOS A TRAVÉS DE PLATAFORMAS TECNOLÓGICAS'),
            ('626', 'RÉGIMEN SIMPLIFICADO DE CONFIANZA')
        ], 
        string="Vendor Tax Regime",
    )

    
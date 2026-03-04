from odoo import models, fields



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

    xml_file = fields.Binary(string="XML")
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


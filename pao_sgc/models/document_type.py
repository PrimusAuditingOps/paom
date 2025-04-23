from odoo import models, fields


class DocumentType(models.Model):
    _name = 'pao.sgc.document.type'
    _description = "PAO Document Type"
    
    name = fields.Char('Document Type', required=True, translate=True)
    
    document_type_key = fields.Char(
        string="Document Type Key",
        required=True,
    )

    validity_years = fields.Integer(
        string="Validity Per Document (Years)",
        default=0, 
        required=True,
    )


                    

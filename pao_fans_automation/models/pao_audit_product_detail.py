from odoo import fields,models,api

class PaoAuditProductDetail(models.Model):

    _name = "pao.audit.product.detail"
    _description = "PAO Audit Product Detail"
    _rec_name = 'product_id'

    product_id= fields.Many2one('servicereferralagreement.auditproducts',string="Product")
    siteHectares= fields.Float("Hectares",required=True)
    toCertificate= fields.Boolean("To Certificate",required=True)
    pp= fields.Boolean("PP",required=True)
    po= fields.Boolean("PO",required=True)
    isCoveredProduction= fields.Boolean("Is Covered Production",required=True)
    hasApplicableCrop= fields.Boolean("Has Applicable Crop",required=True)
    cropType= fields.Selection(
        string='Crop Type',
        selection=[('first','First'), ('second','Second')],
        help="Crop type is used to indicate the current crop", default= 'first'
        )    
    productHandling= fields.Selection(
        string="Product Handling",
        selection=[('yes','Yes'), ('no','No')],
        help="Indicates if the product is currently handled", default= 'no'
        )
    hasSubcontractedActivities= fields.Boolean("Has Subcontracted Activities",required=True)
    subcontractedActivitiesDetail= fields.Text("Subcontracted Activities Detail")
    subcontractedGgnOrGln = fields.Text("Subcontracted GGN/GLN",required=True)
    estimatedYieldTons= fields.Float("Estimated Yield Tons")
    estimatedHarvestPeriod= fields.Char("Estimated Harvest Period")
    destinationCountries_ids= fields.Many2many('res.country',string="Destination Countries",required=True)

    audit_property_id= fields.Many2one("pao.audit.property",string="Property")




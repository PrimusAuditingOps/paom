from odoo import fields,models,api

class PaoGlobalGapApplication(models.Model):
    
    _name = "pao.global.gap.application"
    _description = "PAO GLOBALG.A.P. Application"
    _rec_name = 'plNumber'

    plNumber = fields.Char("PL-México",required=True,copy=False,help="Asigned by Primus Auditing Operations")
    ggn = fields.Char(string="GGN",required=True,help="Asigned by GLOBALG.A.P.")
    version = fields.Selection(
        string='Version',
        selection=[('5.4-1','V5.4-1-GFS'), ('5.3','V5.3-GFS')],
        help="It refers to the GLOBALG.A.P. version on which the customer would like to get certified", default= '5.4-1',
        )
    certification_option = fields.Selection(
        string= "Certification Option",
        selection=[('individual','Opcion 1. Productor Individual'),('multisitio','Opcion 1. Productor Multisitio sinSGC')],
        help="It refers to the certificate option on which the customer would like to get",
        default= 'individual'
        )
    evaluation_type = fields.Selection(
        string= "Evaluation Type",
        selection=[('inicial','Certificacion Inicial'),('recertificacion','Re-certificacion'),('ampliacion','Ampliacion de alcance'),('reduccion','Reduccion de alcance')],
        help="It refers to the certificate option on which the customer would like to get",
        default= 'inicial'
        )
    scheme_addon_ids = fields.Many2many('pao.audit.scheme.addon', string="Addons")
    unannounced_rewards_program = fields.Selection(
        string= "Programa de recompensas no anunciadas",
        selection=[('si','Si'),('no','No'),('na','N/A')],
        help="It indicates if the customer wants a reward program",
        default= 'no'
        )
    legal_entity_ids = fields.One2many('pao.audit.legal.entity','global_gap_application_id')
    allow_access = fields.Selection(
        string="Acceso a datos",
        selection=[('si','Si, el productor se compromete a permitir el acceso a la dirección de su empresa por parte del grupo público de acceso.'),('no','No, el productor no permite el acceso a la dirección de su empresa para el grupo público de acceso.')],
        help='De acuerdo a los requisitos del documento de las Reglas de Acceso a Datos, (que se adjunta y se localiza en \n'
              'www.globalgap.org/es/documents) indicar si:', 
        default = 'si'
        )
    legal_entity_contact_sign = fields.Binary(string='Signature')
    legal_entity_contact_name = fields.Char('Name')
    sign_date= fields.Date('Sign date')
    has_unavailable_period = fields.Boolean('Tiene periodo no disponible')
    unavailable_initial_date = fields.Date('Unavailable initial date')
    unavailable_final_date = fields.Date('Unavailable final date')
    coordinator_id = fields.Many2one('res.partner', string='Coordinator', default=lambda self: self.env.user)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    status = fields.Selection(
        string= 'Status',
        selection= [('draft','Draft'),('filled','Filled'),('reviewing','Reviewing'),('approved','Approved')],
        help= 'Application Status',
        default= 'draft'
    )

    
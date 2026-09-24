from odoo import models, fields, api


# ==========================================
# CATÁLOGOS SIMPLES (administrados por TI)
# ==========================================
# Todos son globales (sin compañía), excepto las ubicaciones, que sí
# pertenecen a una compañía. Los nombres de catálogos con valores
# "genéricos" (categoría, condición, motivo de baja, tipo de software) son
# traducibles; los que son nombres propios (marca, modelo, paquetería,
# método de compra) no.

class PaoItAssetCategory(models.Model):
    _name = 'pao.it.asset.category'
    _description = 'IT Asset Category'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    requires_imei = fields.Boolean(
        string='Requires IMEI',
        help="If checked, assets of this category show the IMEI field (e.g. mobile phones, tablets).")
    active = fields.Boolean(string='Active', default=True)


class PaoItBrand(models.Model):
    _name = 'pao.it.brand'
    _description = 'IT Asset Brand'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    model_ids = fields.One2many('pao.it.model', 'brand_id', string='Models')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'This brand already exists.'),
    ]


class PaoItModel(models.Model):
    _name = 'pao.it.model'
    _description = 'IT Asset Model'
    _order = 'brand_id, name'

    name = fields.Char(string='Name', required=True)
    brand_id = fields.Many2one('pao.it.brand', string='Brand', required=True, ondelete='restrict')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_brand_uniq', 'unique(name, brand_id)', 'This model already exists for this brand.'),
    ]


class PaoItLocation(models.Model):
    _name = 'pao.it.location'
    _description = 'IT Asset Location'
    _order = 'company_id, name'

    # `name` guarda "Ciudad, Estado" (para buscar); el nombre que se ve
    # agrega el tipo traducido al idioma del usuario: "Guadalajara, Jalisco
    # – Office" / "– Oficina". Por eso el tipo NO se guarda dentro de
    # `name`: quedaría congelado en el idioma de quien creó el registro.
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    city = fields.Char(string='City', required=True)
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    country_id = fields.Many2one(related='state_id.country_id', string='Country', store=True)
    location_type = fields.Selection([
        ('office', 'Office'),
        ('home_office', 'Home Office'),
    ], string='Location Type', required=True, default='office')
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('city', 'state_id')
    def _compute_name(self):
        for location in self:
            location.name = ', '.join(p for p in (location.city, location.state_id.name) if p)

    @api.depends('name', 'location_type')
    @api.depends_context('lang')
    def _compute_display_name(self):
        type_labels = dict(self._fields['location_type']._description_selection(self.env))
        for location in self:
            label = type_labels.get(location.location_type)
            location.display_name = f"{location.name} – {label}" if label else location.name


class PaoItCondition(models.Model):
    _name = 'pao.it.condition'
    _description = 'IT Asset Condition'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)


class PaoItPurchaseMethod(models.Model):
    _name = 'pao.it.purchase.method'
    _description = 'Other Purchase Method'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)


class PaoItCarrier(models.Model):
    _name = 'pao.it.carrier'
    _description = 'Shipping Carrier'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=True)


class PaoItRetirementReason(models.Model):
    _name = 'pao.it.retirement.reason'
    _description = 'Asset Retirement Reason'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)


class PaoItSoftwareType(models.Model):
    _name = 'pao.it.software.type'
    _description = 'Software Type'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    active = fields.Boolean(string='Active', default=True)

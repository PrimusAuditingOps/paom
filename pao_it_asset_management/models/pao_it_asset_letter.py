from odoo import models, fields, api, _
from odoo.exceptions import UserError

LETTER_TYPES = [
    ('delivery', 'Delivery Letter'),
    ('return', 'Return Letter'),
]
LETTER_LANGS = [
    ('en_US', 'English'),
    ('es_MX', 'Spanish'),
]

# Textos fijos del PDF por idioma. Viven aquí (y no en el .po) para que el
# PDF salga en el idioma ELEGIDO para la carta sin depender de cómo Odoo
# parte los términos de un reporte QWeb con valores intercalados. Lo
# editable (título y cláusulas) vive en pao.it.letter.template.
LETTER_TEXTS = {
    'en_US': {
        'place': "{place}, on {date}",
        'delivery_paragraph': (
            "Hereby, {company}, hereinafter “the Grantor”, delivers the following computer equipment "
            "to {employee}, hereinafter “the Recipient”, for exclusive use in their work area as of: {date}."),
        'return_paragraph': (
            "Hereby, {company}, through the IT department, receives back the following computer equipment "
            "from: {employee}, to whom it was delivered as a tool for exclusive work use; the equipment is "
            "received in the conditions described in the table, and is handed over to the IT support person "
            "on duty: {admin}."),
        'col_tag': "Asset Tag", 'col_category': "Category", 'col_brand': "Brand", 'col_model': "Model",
        'col_specs': "Specifications", 'col_serial': "Serial No.", 'col_condition': "Condition",
        'regards': "Sincerely,",
        'recipient': "Recipient", 'grantor': "Grantor",
        'prepared': "Prepared by", 'reviewed': "Reviewed by", 'approved': "Approved by",
        'page': "Page", 'of': "of",
        'original_edition': "Original edition", 'revision': "Revision", 'issue': "Issue",
        'issue_default': "As per record",
        'date_format': '%m/%d/%Y',
    },
    'es_MX': {
        'place': "{place}, a {date}",
        'delivery_paragraph': (
            "Por la presente, {company}, en lo subsecuente “El otorgante”, hace entrega del siguiente "
            "equipo de cómputo a {employee}, en lo subsecuente “El receptor”, para uso exclusivo en su "
            "área de trabajo a partir del: {date}."),
        'return_paragraph': (
            "Por la presente, {company}, a través del departamento de TI, recibe en devolución el siguiente "
            "equipo de cómputo de: {employee}, a quien le fue entregado como herramienta para uso exclusivo "
            "de trabajo; el equipo se recibe en las condiciones descritas en la tabla, y se entrega al "
            "encargado en turno de soporte de TI: {admin}."),
        'col_tag': "Etiqueta", 'col_category': "Categoría", 'col_brand': "Marca", 'col_model': "Modelo",
        'col_specs': "Especificaciones", 'col_serial': "No. serie", 'col_condition': "Condición",
        'regards': "Atentamente,",
        'recipient': "Receptor", 'grantor': "Otorgante",
        'prepared': "Elaborado por", 'reviewed': "Revisado por", 'approved': "Aprobado por",
        'page': "Página", 'of': "de",
        'original_edition': "Edición original", 'revision': "Revisión", 'issue': "Emisión",
        'issue_default': "Según la ficha",
        'date_format': '%d/%m/%Y',
    },
}


# ==========================================
# PLANTILLA GLOBAL (título y cláusulas EN/ES)
# ==========================================
# Una por tipo de carta, igual para todos los países y editable por el
# administrador (si calidad publica una revisión con otro texto, no hay que
# programar). Las cláusulas se separan con una línea en blanco.
class PaoItLetterTemplate(models.Model):
    _name = 'pao.it.letter.template'
    _description = 'IT Letter Template'
    _rec_name = 'letter_type'

    letter_type = fields.Selection(LETTER_TYPES, string='Letter Type', required=True)
    title_en = fields.Char(string='Title (English)', required=True)
    title_es = fields.Char(string='Title (Spanish)', required=True)
    clauses_en = fields.Text(string='Clauses (English)', help="Separate paragraphs with a blank line.")
    clauses_es = fields.Text(string='Clauses (Spanish)', help="Separate paragraphs with a blank line.")

    _sql_constraints = [
        ('letter_type_uniq', 'unique(letter_type)', 'There is already a template for this letter type.'),
    ]


# ==========================================
# CONTROL DEL DOCUMENTO (por compañía / país)
# ==========================================
class PaoItLetterControl(models.Model):
    _name = 'pao.it.letter.control'
    _description = 'IT Letter Document Control'
    _order = 'company_id, letter_type'

    company_id = fields.Many2one('res.company', string='Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    letter_type = fields.Selection(LETTER_TYPES, string='Letter Type', required=True)
    code = fields.Char(string='Document Code', required=True)
    revision = fields.Char(string='Revision')
    prepared_by = fields.Char(string='Prepared by')
    reviewed_by = fields.Char(string='Reviewed by')
    approved_by = fields.Char(string='Approved by')
    original_edition_date = fields.Date(string='Original Edition')
    issue_date = fields.Date(string='Issue Date',
                             help="Leave empty to print \"As per record\" / \"Según la ficha\".")

    _sql_constraints = [
        ('company_type_uniq', 'unique(company_id, letter_type)',
         'There is already a document control for this company and letter type.'),
    ]

    @api.depends('company_id', 'letter_type', 'code')
    def _compute_display_name(self):
        labels = dict(self._fields['letter_type']._description_selection(self.env))
        for control in self:
            control.display_name = f"{control.code} – {labels.get(control.letter_type)} ({control.company_id.name})"

    @api.model
    def _ensure_letter_controls(self):
        """Idempotente (data/pao_it_asset_data_update.xml): un control por
        compañía y tipo. Las compañías de México se prellenan con los datos de
        los formatos FTI-01 / FTI-02 vigentes; las demás, solo código y
        revisión (el administrador completa el resto)."""
        defaults = {
            'delivery': {'code': 'FTI-01', 'revision': '01', 'prepared_by': 'P. Maldonado',
                         'reviewed_by': 'H. Calderón', 'approved_by': 'I. Salazar',
                         'original_edition_date': '2024-02-20'},
            'return': {'code': 'FTI-02', 'revision': '00', 'prepared_by': 'P. Maldonado',
                       'reviewed_by': 'M. Salmerón', 'approved_by': 'J. Ledezma',
                       'original_edition_date': '2024-02-20', 'issue_date': '2024-02-20'},
        }
        Control = self.sudo()
        existing = {(c.company_id.id, c.letter_type) for c in Control.search([])}
        vals_list = []
        for company in self.env['res.company'].sudo().search([]):
            for letter_type, values in defaults.items():
                if (company.id, letter_type) in existing:
                    continue
                vals = {'company_id': company.id, 'letter_type': letter_type,
                        'code': values['code'], 'revision': values['revision']}
                if company.country_id.code == 'MX':
                    vals.update(values)
                vals_list.append(vals)
        Control.create(vals_list)


# ==========================================
# CARTA GENERADA (responsiva o devolución)
# ==========================================
# Registro de cada carta generada: queda en el historial del activo y ahí se
# sube el PDF firmado. El PDF en blanco NO se guarda: se regenera a partir de
# la foto de los datos (renglones), así siempre sale idéntico.
class PaoItAssetLetter(models.Model):
    _name = 'pao.it.asset.letter'
    _description = 'IT Asset Letter'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    letter_type = fields.Selection(LETTER_TYPES, string='Letter Type', required=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True,
                                  ondelete='restrict', index=True)
    date = fields.Date(string='Date', required=True, readonly=True)
    lang = fields.Selection(LETTER_LANGS, string='Language', required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Generated By', required=True, readonly=True,
                              default=lambda self: self.env.user)
    place = fields.Char(string='Place', readonly=True)
    line_ids = fields.One2many('pao.it.asset.letter.line', 'letter_id', string='Assets', readonly=True)
    asset_ids = fields.Many2many('pao.it.asset', string='Assets (Records)', compute='_compute_asset_ids',
                                 search='_search_asset_ids')
    movement_ids = fields.Many2many('pao.it.asset.movement', 'pao_it_asset_letter_movement_rel',
                                    'letter_id', 'movement_id', string='Movements', readonly=True)
    signed_attachment_ids = fields.Many2many('ir.attachment', 'pao_it_asset_letter_signed_rel',
                                             'letter_id', 'attachment_id', string='Signed PDF')
    state = fields.Selection([
        ('pending', 'Pending Signature'),
        ('signed', 'Signed'),
    ], string='Status', compute='_compute_state', store=True)
    notes = fields.Text(string='Notes')

    @api.depends('letter_type', 'employee_id', 'date')
    def _compute_display_name(self):
        labels = dict(self._fields['letter_type']._description_selection(self.env))
        for letter in self:
            letter.display_name = f"{labels.get(letter.letter_type)} – {letter.employee_id.name} ({letter.date})"

    @api.depends('line_ids.asset_id')
    def _compute_asset_ids(self):
        for letter in self:
            letter.asset_ids = letter.line_ids.asset_id

    def _search_asset_ids(self, operator, value):
        return [('line_ids.asset_id', operator, value)]

    @api.depends('signed_attachment_ids')
    def _compute_state(self):
        for letter in self:
            letter.state = 'signed' if letter.signed_attachment_ids else 'pending'

    @api.ondelete(at_uninstall=False)
    def _unlink_never(self):
        raise UserError(_("Letters are part of the asset history and cannot be deleted."))

    # ==========================================
    # GENERACIÓN
    # ==========================================
    @api.model
    def _place_for(self, assets, company, lang):
        location = assets.location_id[:1]
        country = company.country_id.with_context(lang=lang).name or ''
        if location:
            parts = [location.city, location.state_id.name, country]
        else:
            parts = [company.city, company.state_id.name, country]
        return ', '.join(p for p in parts if p)

    @api.model
    def _create_letter(self, letter_type, employee, assets, date, lang, movements=None):
        """Crea la carta con la foto de los datos de cada activo. En la
        devolución, la condición sale del movimiento Return de cada activo."""
        movements = movements or self.env['pao.it.asset.movement']
        if not employee:
            raise UserError(_("Letters can only be generated for assets assigned to an employee."))
        company = assets[:1].company_id or employee.company_id
        lines = []
        for asset in assets:
            movement = movements.filtered(lambda m: m.asset_id == asset)[:1]
            condition = movement.condition_to_id if letter_type == 'return' and movement else asset.condition_id
            lines.append((0, 0, {
                'asset_id': asset.id,
                'asset_tag': asset.asset_tag,
                'category': asset.category_id.with_context(lang=lang).name,
                'brand': asset.brand_id.name,
                'model': asset.model_id.name,
                'specifications': asset.specifications,
                'serial_number': asset.serial_number,
                'condition': condition.with_context(lang=lang).name,
            }))
        return self.create({
            'letter_type': letter_type,
            'company_id': company.id,
            'employee_id': employee.id,
            'date': date,
            'lang': lang,
            'place': self._place_for(assets, company, lang),
            'line_ids': lines,
            'movement_ids': [(6, 0, movements.ids)],
        })

    # ==========================================
    # PDF
    # ==========================================
    def _print_lang(self):
        """Idioma del PDF: el de la carta, o el pedido al descargar."""
        self.ensure_one()
        return self.env.context.get('pao_it_letter_lang') or self.lang

    def _get_report_values(self):
        """Todo lo que el reporte necesita, ya en el idioma del PDF."""
        self.ensure_one()
        lang = self._print_lang()
        texts = LETTER_TEXTS[lang]
        template = self.env['pao.it.letter.template'].sudo().search(
            [('letter_type', '=', self.letter_type)], limit=1)
        control = self.env['pao.it.letter.control'].sudo().search(
            [('company_id', '=', self.company_id.id), ('letter_type', '=', self.letter_type)], limit=1)
        if not template or not control:
            raise UserError(_(
                "Please configure the letter template and the document control of %s "
                "(Configuration > Documents).", self.company_id.name))
        date_str = self.date.strftime(texts['date_format'])
        place = self.place if lang == self.lang else self._place_for(self.line_ids.asset_id, self.company_id, lang)
        paragraph_key = 'delivery_paragraph' if self.letter_type == 'delivery' else 'return_paragraph'
        clauses = (template.clauses_es if lang == 'es_MX' else template.clauses_en) or ''
        company = self.company_id
        address = ', '.join(p for p in [company.street, company.street2, company.city,
                                        company.state_id.name, company.zip] if p)

        def fmt(value):
            return value.strftime(texts['date_format']) if value else ''

        return {
            'texts': texts,
            'title': template.title_es if lang == 'es_MX' else template.title_en,
            'clauses': [c.strip() for c in clauses.split('\n\n') if c.strip()],
            'control': control,
            'place_line': texts['place'].format(place=place, date=date_str),
            'paragraph': texts[paragraph_key].format(
                company=company.name, employee=self.employee_id.name, date=date_str, admin=self.user_id.name),
            'address': address,
            'is_return': self.letter_type == 'return',
            'original_edition': fmt(control.original_edition_date),
            'issue': fmt(control.issue_date) or texts['issue_default'],
            # En la devolución se invierten los roles.
            'left_role': texts['recipient'],
            'right_role': texts['grantor'],
        }

    def action_download(self):
        self.ensure_one()
        lang = self.env.context.get('pao_it_letter_lang') or self.lang
        return self.env.ref('pao_it_asset_management.action_report_asset_letter').with_context(
            pao_it_letter_lang=lang).report_action(self)

    def action_download_en(self):
        return self.with_context(pao_it_letter_lang='en_US').action_download()

    def action_download_es(self):
        return self.with_context(pao_it_letter_lang='es_MX').action_download()


class PaoItAssetLetterLine(models.Model):
    _name = 'pao.it.asset.letter.line'
    _description = 'IT Asset Letter Line'
    _order = 'id'

    letter_id = fields.Many2one('pao.it.asset.letter', string='Letter', required=True, ondelete='cascade',
                                index=True)
    company_id = fields.Many2one(related='letter_id.company_id', store=True)
    asset_id = fields.Many2one('pao.it.asset', string='Asset', ondelete='set null', index=True)
    # Foto de los datos al generar la carta.
    asset_tag = fields.Char(string='Asset Tag')
    category = fields.Char(string='Category')
    brand = fields.Char(string='Brand')
    model = fields.Char(string='Model')
    specifications = fields.Text(string='Specifications')
    serial_number = fields.Char(string='Serial Number')
    condition = fields.Char(string='Condition')

from odoo import fields, models
from logging import getLogger


_logger = getLogger(__name__)

class ResPartner(models.Model):
    _inherit='res.partner'

    def _generar_ext_id(self):
        for record in self:
            res = record.get_external_id()
            xml_id = ''
            if res.get(record.id):
                xml_id = res.get(record.id)
            else:
                xml_id = record.export_data(['id']).get('datas')[0][0]

            record['ctm_ext_id'] = 'https://www.paomx.com/altaclientes/index.php?cliente='+record.name+'&id='+xml_id

    def _obtener_ext_id(self):
        for record in self:
            res = record.get_external_id()
            xml_id = ''
            if res.get(record.id):
                xml_id = res.get(record.id)
            else:
                xml_id = record.export_data(['id']).get('datas')[0][0]

            record['ctm_external_id'] = xml_id

    ctm_ext_id = fields.Char(
        compute = _generar_ext_id,
        string = 'customer registration',
        readonly = True,
    )
    ctm_external_id = fields.Char(
        compute = _obtener_ext_id,
        string = 'External ID',
        readonly = True,
    )
    

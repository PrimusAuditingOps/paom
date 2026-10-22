from odoo import models, api

# Llave de contexto que activan las pantallas de IT Asset Management (sus
# acciones y el asistente de movimientos). SOLO con ella presente,
# departamentos y empleados muestran el país de su compañía:
# "IT (México)", "Hector Cortes (Estados Unidos)". PAO repite departamentos
# y empleados por compañía (control de gastos), así que sin esto la lista
# muestra dos "IT" idénticos. Fuera del módulo el nombre no cambia.
#
# Solo se extiende el cálculo del nombre visible; NO se agregan campos ni
# columnas a hr.department / hr.employee (sin riesgo de desfase de esquema,
# ver ODOO_MODULE_DEVELOPMENT_GUIDE.md punto 1).
SHOW_COMPANY_CONTEXT_KEY = 'pao_it_show_company'


def _company_label(company):
    # País de la compañía (una compañía por país en PAO); si no tiene país,
    # el nombre de la compañía.
    company = company.sudo()
    return company.country_id.name or company.name


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    @api.depends_context(SHOW_COMPANY_CONTEXT_KEY)
    def _compute_display_name(self):
        super()._compute_display_name()
        if not self.env.context.get(SHOW_COMPANY_CONTEXT_KEY):
            return
        for department in self:
            # Departamento sin compañía (compartido): solo su nombre.
            if department.company_id:
                department.display_name = f"{department.display_name} ({_company_label(department.company_id)})"


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.depends_context(SHOW_COMPANY_CONTEXT_KEY)
    def _compute_display_name(self):
        super()._compute_display_name()
        if not self.env.context.get(SHOW_COMPANY_CONTEXT_KEY):
            return
        for employee in self:
            if employee.company_id:
                employee.display_name = f"{employee.display_name} ({_company_label(employee.company_id)})"

# PAO Attendance Schedule Restriction (Odoo 17)

Restringe el registro de entrada y salida de **Asistencias** al horario laboral del empleado, tanto cuando checa el empleado como cuando captura su Responsable de asistencias.

## Configuración

**Empleados → Configuración → Horarios laborales → (jornada) → pestaña "Restricción de asistencias"**

| Campo | Default | Ejemplo con periodo 08:00–13:00 |
|---|---|---|
| Restringir entradas/salidas al horario | Activo | Apaga la restricción solo para esa jornada |
| Minutos permitidos antes de la entrada | 10 | Entrada desde 07:50 |
| Tolerancia de retardo en la entrada (minutos) | 10 | Entrada hasta 08:10 |
| Minutos permitidos después de la salida | 5 | Salida hasta 13:05 |
| Tiempo mínimo entre salida y entrada (minutos) | 60 | Si salió 13:05, entra a partir de 14:05 |

Las tolerancias aplican igual a los periodos Mañana y Tarde. Las líneas de Descanso se ignoran.

## Reglas de horario

- **Entrada**: solo dentro de la ventana *inicio − minutos antes* a *inicio + tolerancia de retardo* (07:50–08:10). A las 08:11 ya no se permite.
- **Salida**: en cualquier momento hasta el *fin del periodo de la entrada + minutos después* (13:05). La salida anticipada está permitida.
- **Comida**: una entrada debe ser al menos *tiempo mínimo* después de la última salida del empleado.
- Se bloquea en días sin periodos en la jornada (ej. sábado) y para empleados sin jornada.
- Respeta jornadas de 2 semanas, líneas con fecha de inicio/fin y líneas por recurso. La hora se evalúa en la zona horaria del empleado (o la de la jornada).

## Quién aplica qué

| Quién | Qué puede hacer |
|---|---|
| **Empleado** (botón de la barra superior, app móvil, kiosko) | Checar entrada/salida solo dentro de las reglas de horario. Si no puede, el mensaje le indica pedírselo a su Responsable de asistencias. |
| **Responsable de asistencias** (no administrador) | Solo para sus empleados: **crear** la entrada (registro nuevo) y **agregar la salida** a un registro que aún no la tiene. Las horas deben cumplir las reglas de horario y no pueden ser futuras. **No puede** cambiar una entrada o salida ya registrada, cambiar el empleado del registro ni eliminar registros. |
| **Administrador de Asistencias** | Crea, edita y corrige libremente, sin reglas de horario. Es el único que puede eliminar registros. |

Al asignar a alguien como **Responsable de asistencias** (`attendance_manager_id`) de un empleado, Odoo le da automáticamente el grupo *Officer: Manage attendances*, que solo le deja ver y capturar asistencias de esos empleados, no las suyas (comportamiento nativo).

Arrastrar un registro en las vistas de calendario/Gantt también es una modificación de horas, así que para el responsable queda bloqueado igual.

## Registros hechos por otro usuario

En `hr.attendance` se agregan:

- `registered_by_other`: se marca cuando alguien distinto al empleado crea o modifica la entrada, la salida o el empleado del registro.
- `registered_by_other_user_id`: el último usuario que lo hizo.

Están ocultos en la lista (se activan desde las columnas opcionales). Para consultarlos, usa el filtro **"Registrado por otro usuario"** y la agrupación **"Registrado/modificado por"**. El historial de cambios de entrada/salida sigue quedando en el chatter, como en el estándar de Odoo.

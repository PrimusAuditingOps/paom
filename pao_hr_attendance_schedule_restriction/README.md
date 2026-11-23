# PAO Attendance Schedule Restriction (Odoo 17)

Restringe el registro de entrada y salida de **Asistencias** al horario laboral del empleado.

## Configuración

**Empleados → Configuración → Horarios laborales → (jornada) → pestaña "Restricción de asistencias"**

| Campo | Default | Uso |
|---|---|---|
| Restringir entradas/salidas al horario | Activo | Apaga la restricción solo para esa jornada |
| Minutos permitidos antes de la entrada | 10 | Ej. periodo 08:00 → entrada desde 07:50 |
| Minutos permitidos después de la salida | 5 | Ej. periodo hasta 13:00 → salida hasta 13:05 |

Las tolerancias aplican igual a los periodos Mañana y Tarde. Las líneas de Descanso se ignoran.

## Reglas (botón de la barra superior, app móvil y kiosko)

- **Entrada**: desde el inicio del periodo menos la tolerancia y hasta el fin del periodo. Llegar tarde está permitido; checar antes no.
- **Salida**: en cualquier momento antes del fin del periodo de la entrada más la tolerancia. La salida anticipada está permitida.
- Si se pasa el límite de salida, el empleado ya no puede checar y debe pedirle a su **Responsable de asistencias** que lo registre.
- Se bloquea el registro en días sin periodos en la jornada (ej. sábado) y para empleados sin jornada asignada.
- Respeta jornadas de 2 semanas, líneas con fecha de inicio/fin y líneas específicas por recurso.
- La hora se evalúa en la zona horaria del empleado (o la de la jornada).

## Permisos (nativo de Odoo 17, sin cambios)

Al asignar a un usuario como **Responsable de asistencias** (`attendance_manager_id`) de un empleado, Odoo le da automáticamente el grupo *Officer: Manage attendances*. Con él puede ver, crear, editar y borrar las asistencias **solo de esos empleados**, y no puede editar las suyas salvo que él mismo sea su propio responsable. El grupo **Administrador** sigue viendo todo.

Los registros creados o editados desde la app de Asistencias (formulario o lista) **no** pasan por la restricción de horario.

## Registros hechos por otro usuario

En `hr.attendance` se agregan:

- `registered_by_other`: se marca cuando alguien distinto al empleado crea o modifica la entrada, la salida o el empleado del registro.
- `registered_by_other_user_id`: el último usuario que lo hizo.

Están ocultos en la lista (se activan desde las columnas opcionales). Para consultarlos, usa el filtro **"Registrado por otro usuario"** y la agrupación **"Registrado/modificado por"**. El historial de cambios de entrada/salida sigue quedando en el chatter, como en el estándar de Odoo.

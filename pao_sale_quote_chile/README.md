# PAO Sale Quote Chile

Formato regional de cotización (PDF, portal y correo) para la compañía de Chile
(Primus Auditing Ops Chile). La operación interna de Ventas no cambia: el vendedor
captura la cotización con productos, secciones y notas nativas de Odoo, y el
módulo arma el documento con el formato que antes se hacía a mano.

Muestras del formato original: `nuevosdesarrollos/docs/formatos_cotizacion/`.

## Cuándo aplica

- Solo a compañías que tengan un registro en **Ventas › Configuración › Cotización Chile › Formato de cotización**.
  Al instalar, se crea automáticamente para cada compañía con país Chile.
- Solo a **cotizaciones** (estado Borrador / Enviada). Los pedidos confirmados y las
  demás compañías siguen con el reporte nativo de Odoo.
- Aplica al PDF (imprimir / adjunto del correo) y al **portal del cliente**. En el portal
  no se muestra el total de Odoo, porque mezcla alternativas y monedas base.

## Cómo se arma el documento

| Formato | Origen en Odoo |
|---|---|
| `#S00235` | Número de la cotización |
| Cliente / Contacto / Email / Teléfono | Empresa del cliente / contacto de la cotización (si es una persona) |
| "Estimada Karina:" | Campo **Título** del contacto (Sra./Srta. → Estimada, Sr. → Estimado; sin título → Estimado/a) |
| Fecha "Septiembre 2026." | Fecha de la cotización |
| Introducción larga / corta | Larga si algún esquema de la cotización tiene "Usar introducción larga" |
| Cada tabla | Una **sección** nativa. El nombre de la sección es el título (a., b., c. automáticos) |
| Encabezados, franja y pie de la tabla | **Formato de tabla** del primer producto de la sección (columna opcional "Formato de tabla" para cambiarlo en la línea) |
| "1. Auditorías de Campo" | **Categoría** del formato de tabla; secciones seguidas con la misma categoría comparten número |
| Fila "GG opc 1 + Nurture" con precio sumado | Línea de Nurture con **Combinar** marcado (se toma del producto, editable en la línea) |
| Monto con su moneda | **Moneda base** del producto (`pao_chile_invoices`); sin conversión |
| Notas al pie de la tabla | Notas del formato de tabla + "Nota en cotización" de cada producto de la tabla |
| Párrafos antes/después de una tabla | **Notas** nativas dentro de la sección (antes o después de los productos) |
| Consideraciones de facturación | Bloques de posición "Facturación" + **Términos y condiciones** de la cotización (para textos de un cliente específico) |
| Información adicional / Anexos | Bloques según los **esquemas** de los productos y el país del cliente (nacional / extranjero) |

## Configuración inicial

1. **Formato de papel**: Ajustes › Compañías › (Chile) › Diseño de documento › Formato de papel = `PAO Chile - Carta`.
2. **Formato de cotización**: revisar logo, firma (imagen de Katherine Legua), introducciones y pie de página.
3. **Productos**: pestaña **Cotización Chile** en cada servicio / add-on:
   - Esquema de auditoría (GLOBALG.A.P., PrimusGFS, SMETA…).
   - Formato de tabla en cotización.
   - Nombre en cotización (opcional, p. ej. `GLOBALG.A.P. (v.6 GFS)¹`).
   - Combinar con la línea anterior (p. ej. Nurture).
   - Nota en cotización (p. ej. `² Para el Módulo Nurture, se cargará adicionalmente un Fee de € 60 por certificado.`).
4. **Catálogo**: completar Esquemas, Formatos de tabla, Categorías y Bloques de información.
   El módulo trae GLOBALG.A.P. como ejemplo, con los textos de las cotizaciones manuales.
5. **Correo**: elegir la plantilla de envío de cotización desde la interfaz. La nativa menciona el
   monto total; para Chile conviene una plantilla sin el monto.

## Uso por el vendedor

1. Crear la cotización como siempre.
2. Agregar una **sección** por tabla (p. ej. "Auditorías GLOBALG.A.P. versión 6 GFS.").
3. Agregar los productos debajo. Para un combo, poner el servicio y después el add-on
   (el add-on ya viene con "Combinar" marcado si así está en el producto).
4. Notas nativas dentro de la sección para párrafos propios de esa cotización.
5. Al aceptar el cliente: borrar las alternativas no elegidas y confirmar.

Si un combo junta productos con monedas base distintas, Odoo no deja guardar (no se pueden sumar).

# PAO Sale Quote Chile

Formato regional editable de cotización (PDF y portal) para la compañía de Chile
(Primus Auditing Ops Chile). La operación interna de Ventas no cambia: el vendedor
captura la cotización con productos, secciones y notas nativas, y el contenido del
documento es un campo HTML que se genera solo y después se edita libremente.

Muestras del formato original: `nuevosdesarrollos/docs/formatos_cotizacion/`.

## Cuándo aplica

- Compañías con un registro en **Ventas › Configuración › Formato de cotización Chile**
  (al instalar se crea automáticamente para cada compañía con país Chile).
- Cotizaciones **y pedidos confirmados** de esas compañías. Las demás compañías siguen
  con el reporte nativo de Odoo.
- PDF (imprimir / adjunto del correo) y **portal del cliente**. En el portal no se muestra
  el total de Odoo, porque mezcla alternativas y monedas base.

## Piezas

| Pieza | Dónde |
|---|---|
| Formato por plantilla (diseño completo con marcadores) | Plantilla de cotización › pestaña **Formato Chile** |
| Formato por defecto (si la plantilla no tiene) | Formato de cotización Chile › **Formato por defecto** |
| Formato de cada cotización (lo que se imprime) | Cotización › pestaña **Formato de cotización** |
| Logo, imagen de firma, pie de página | Formato de cotización Chile |
| Check **Combinar** | Columna en las líneas de la cotización |

## Marcadores

| Marcador | Se reemplaza por |
|---|---|
| `[[NUMERO]]` | Número de la cotización (`#S00235`) |
| `[[CLIENTE]]` | Empresa del cliente |
| `[[CONTACTO]]` | Contacto de la cotización (si es una persona) |
| `[[EMAIL]]` / `[[TELEFONO]]` | Del contacto (o "No Registra.") |
| `[[FECHA]]` | "Octubre 2026." |
| `[[SALUDO]]` | "Estimada Karina:" según el **Título** del contacto (Sra./Srta. → Estimada, Sr. → Estimado, sin título → Estimado/a) |
| `[[TABLAS]]` | Tablas armadas desde las líneas (ver abajo) |
| `[[FIRMA]]` | Imagen de firma. Se reemplaza **al imprimir**, en el editor se ve el texto `[[FIRMA]]` |

Todos menos `[[FIRMA]]` se reemplazan al **generar** el formato y quedan como texto editable.

## Cómo se arman las tablas (`[[TABLAS]]`)

- Cada **sección** nativa es una tabla; su nombre es el título (a., b., c. automáticos).
- Cada producto es una fila con su precio (subtotal sin impuestos) en la **moneda base**
  del producto (`pao_chile_invoices`), sin conversión: USD 770, € 50, £ 199.
- Una línea con **Combinar** marcado se une a la fila anterior: "GG opc 1 + Nurture" con el precio sumado.
  Si el combo junta monedas base distintas, Odoo no deja guardar.
- Una **nota** dentro de la sección, antes de los productos, es un párrafo arriba de la tabla;
  después de los productos, es el pie gris de la tabla (p. ej. "Valores en USD + Fee GLOBALG.A.P.¹ + Gastos Viaje³ + IVA").
- Encabezados genéricos ("ALTERNATIVAS" | "Valor USD $"); se ajustan en el editor si hace falta.

## Cuándo se genera

- Automáticamente al guardar la cotización si el formato está vacío, y al cambiar la plantilla
  de cotización si el formato está vacío.
- Con el botón **Generar formato** (pide confirmación si ya hay contenido: se pierden los cambios manuales).
- Si se imprime con el formato vacío, se arma al vuelo para no imprimir en blanco.
- Al duplicar una cotización el formato no se copia; se genera de nuevo con los datos nuevos.

## Configuración inicial

1. **Formato de papel**: Ajustes › Compañías › (Chile) › Diseño de documento › Formato de papel = `PAO Chile - Carta`.
2. **Formato de cotización Chile**: subir logo e imagen de firma (Katherine Legua); revisar el pie de página.
3. **Plantillas de cotización**: una por tipo (GLOBALG.A.P., SMETA, PrimusGFS…), cada una con su
   pestaña **Formato Chile**. Al instalar se crea "GLOBALG.A.P. (Chile)" como ejemplo, con los textos
   de las cotizaciones manuales (archivo `data/pao_quote_default_format.html`).
4. **Correo**: elegir la plantilla de envío desde la interfaz (la nativa menciona el monto total).

## Uso por el vendedor

1. Crear la cotización y elegir la plantilla de cotización.
2. Una **sección** por tabla, productos debajo, **Combinar** en el add-on que va pegado al servicio.
3. Guardar: el formato se genera solo. Revisarlo y editarlo en la pestaña **Formato de cotización**.
4. Si se cambian las líneas después, usar **Generar formato** (o ajustar a mano).
5. Al aceptar el cliente: borrar las alternativas no elegidas y confirmar.

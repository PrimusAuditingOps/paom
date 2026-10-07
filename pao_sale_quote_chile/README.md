# PAO Sale Quote Chile

Formato regional de cotización (PDF y portal) para la compañía de Chile (Primus Auditing Ops Chile).

Al cliente no se le envía una cotización con líneas, sino una **tarifa armada**: un documento con los precios de
los servicios y lo que se cobra, para que indique lo que requiere. Este módulo guarda esas tarifas, las liga a
las plantillas de cotización y las carga en la cotización con los datos del cliente. La operación interna de
Ventas (líneas, confirmación, facturación) sigue siendo la nativa de Odoo.

Muestras del formato original: `nuevosdesarrollos/docs/formatos_cotizacion/`.

## Piezas

| Pieza | Dónde |
|---|---|
| **Tarifas armadas de cotización** (HTML completo con marcadores) | Ventas › Configuración › Tarifas armadas de cotización |
| Tarifa de cada plantilla de cotización | Plantilla de cotización › campo **Tarifa armada** |
| Formato de cada cotización (lo que se imprime) | Cotización › pestaña **Formato de cotización** |
| Logo, imagen de firma y pie de página | Ventas › Configuración › Formato de cotización Chile |

Al instalar se cargan **8 tarifas** transcritas de los PDFs originales (`data/rates/*.html`):
GLOBALG.A.P., GLOBALG.A.P. + Combo, GLOBALG.A.P. + Combo + Add-ons, Varios esquemas con combo y add-ons,
SMETA, PrimusGFS, LEAF Marque y PHA. Se cargan con `noupdate`: lo que edite ventas no se pisa al actualizar.
Las referencias "Tabla de la Página X" se cambiaron por "Tabla 1 de la sección Información Adicional".

## Marcadores

| Marcador | Se reemplaza por |
|---|---|
| `[[NUMERO]]` | Número de la cotización (`#S00235`) |
| `[[CLIENTE]]` | Empresa del cliente |
| `[[CONTACTO]]` | Contacto de la cotización (si es una persona) |
| `[[EMAIL]]` / `[[TELEFONO]]` | Del contacto (teléfono vacío → "No Registra.") |
| `[[PAIS]]` | País del cliente |
| `[[FECHA]]` | "Octubre 2026." |
| `[[SALUDO]]` | "Estimada Karina:" según el **Título** del contacto (Sra./Srta. → Estimada, Sr. → Estimado, sin título → Estimado/a) |
| `[[FIRMA]]` | Imagen de firma. Se reemplaza **al imprimir**; en el editor se ve el texto `[[FIRMA]]` |

## Cuándo se carga

- Automáticamente al guardar la cotización si el formato está vacío y la plantilla tiene tarifa
  (también al cambiar la plantilla, si el formato sigue vacío).
- Con el botón **Generar formato** (pide confirmación si ya hay contenido: se pierden los cambios manuales).
- Si se imprime con el formato vacío, se arma al vuelo desde la tarifa.
- Al duplicar una cotización el formato no se copia; se vuelve a cargar con los datos nuevos.

## Dónde aplica

- Compañías con registro en **Formato de cotización Chile** (al instalar se crea para cada compañía con país Chile;
  si hay una sola, las 8 tarifas quedan asignadas a ella).
- Cotizaciones **y pedidos confirmados** de esas compañías; las demás siguen con el reporte nativo.
- PDF (imprimir / adjunto del correo) y **portal del cliente** (sin mostrar el total de Odoo).

## Editar el HTML

Con el **modo desarrollador** activo, los campos de tarifa y de formato muestran el botón `</>` del editor para
editar el código HTML. Se conservan los estilos inline (`style="..."`), tablas y clases; Odoo elimina por seguridad
etiquetas como `<style>` o `<script>`.

## Configuración inicial

1. **Formato de papel**: Ajustes › Compañías › (Chile) › Diseño de documento › Formato de papel = `PAO Chile - Carta`.
2. **Formato de cotización Chile**: subir logo e imagen de firma (Katherine Legua); revisar el pie de página.
3. **Tarifas**: revisar y ajustar las 8 tarifas.
4. **Plantillas de cotización**: crear las combinaciones necesarias y asignar a cada una su **Tarifa armada**.
5. **Correo**: elegir la plantilla de envío desde la interfaz (la nativa menciona el monto total).

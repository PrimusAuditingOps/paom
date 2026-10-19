# PAO SIGN SA Chile

Formato **CERT-008 R7 "Acuerdo de Servicios de Programa de Certificación"** para el esquema **GLOBALG.A.P.**
en el flujo de firma de SA (`pao_sign_sa`, botón **Send SA**) con **formato de país Chile**.
México, USA y Costa Rica no cambian (Costa Rica sigue bloqueado para GLOBALG.A.P.).

## Cómo se arma

Un documento por **organización + número de registro**, igual que el resto de los SA. Todo sale de las líneas de
la cotización de esa organización / número de registro, clasificadas por el producto:

| El producto tiene… | Se imprime en… |
|---|---|
| **Es cuota del SA** (pestaña *SA Chile*) | Un renglón propio desde el punto 9, en el orden de las líneas, con la descripción de la línea y su valor |
| **Add-On del SA** (catálogo) | Marca su casilla en el punto 7; su valor suma al Costo Total Auditoría |
| **It's a travel expense** (`pao_sign_ra`) | "a. Cargos del viaje" (suma) |
| Ninguno | Servicio de auditoría: su descripción va en el punto 6 y su valor suma al Costo Total Auditoría |

- Un producto solo puede tener **uno** de los tres (cuota, add-on, viaje); el catálogo no permite combinarlos.
- **Valor** = subtotal de la línea; **moneda** = *Moneda base* del producto (`pao_chile_invoices`), sin conversión.
- **Costo Total Auditoría**: auditoría + add-ons por moneda, y debajo "+ € … Fee" con las cuotas por moneda.
- Puntos 1–4 y 8: organización y número de registro (igual que los otros formatos). **Preparado por**: coordinadora
  de las líneas de esa organización / número de registro.
- Las casillas del punto 7 salen del catálogo **Ventas › Configuración › Add-Ons del SA** (en el orden del catálogo).
- Al enviar, las líneas clasificadas se guardan en el SA (`pao.sa.cert008.line`): el documento firmado no cambia si
  después se edita la cotización o el catálogo. La vista previa usa las líneas actuales.

## Pendiente

- **Punto 5** (N.º Orden de compra): se imprime vacío; posiblemente capturable al enviar (solo Chile).
- **Firmas**: nombre del firmante del cliente y firma de Katherine Legua (archivo de firma) por definir.
  Hoy se imprime la firma electrónica del cliente, su nombre y la fecha de firma; el espacio de Primus Chile queda vacío.

## Cambio en `pao_sign_sa`

`sa.send.request._is_globalgap_format_available()`: el bloqueo de GLOBALG.A.P. fuera de México pasó a este método;
este módulo lo extiende para Chile.

# Especificación funcional — MVP

## 1. Contexto
Catálogo público para Dulce y Salado, comercio pequeño con productos de repostería, dietética y cotillón vendidos por peso, unidad o paquete. Público principal: clientes que consultan precios y arman pedidos, especialmente desde celular. La comunicación y confirmación final ocurre por WhatsApp.

## 2. Objetivo
Reducir consultas manuales de precios y facilitar pedidos de productos y cantidades, sin crear un comercio electrónico transaccional.

## 3. Actores
- Visitante anónimo: busca, consulta precios, agrega artículos a un carrito local y abre WhatsApp con el texto precargado.
- Administrador del comercio: gestiona categorías y productos con Django Admin.

## 4. Alcance del MVP
- Catálogo público de productos activos, categorías activas, fotos, búsqueda por nombre, marca y descripción (prioridad en ese orden).
- Productos con nombre, categoría, marca opcional, descripción opcional, una imagen opcional, unidad de venta, incremento válido de cantidad, precio minorista y mayorista cuando corresponda, observación de condiciones mayoristas, estado activo.
- Precio minorista seleccionado por defecto. Visitante puede elegir precio mayorista manualmente cuando exista; no se validan automáticamente condiciones.
- Cantidad editable respetando unidad/incremento; cálculo de subtotales y total estimado con aritmética decimal o unidades enteras, sin errores de coma flotante de dinero.
- Carrito persistido con `localStorage` en un navegador; no sincronizado entre dispositivos. Guardar como mínimo ID de producto, cantidad y tipo de precio. Ante cambios o desactivación del catálogo se recalcula o informa, sin mostrar precios antiguos como vigentes.
- Pantalla de revisión con totales estimados. Antes de abrir WhatsApp, advertencia explícita: precios estimados, disponibilidad pendiente de confirmación y mayoristas sujetos a condiciones y validación comercial.
- Enlace `wa.me` a número configurado del negocio con texto URL-encoded. El usuario finalmente envía el mensaje en WhatsApp.
- Administración mediante Django Admin, sin panel administrativo propio.

## 5. Sin implementar en MVP
Autenticación de clientes, historial/registro de pedidos, stock, pagos, pagos a cuenta, envíos, facturación, cupones, promociones complejas, umbrales mayoristas automáticos, múltiples fotografías, ratings, newsletter, notificaciones, chat embebido, API REST pública, WhatsApp Business API, PWA.

## 6. Entidades
**Category**: `name`, `slug`, `sort_order`, `is_active`.
**Product**: `category`, `name`, `brand` (opcional), `description` (opcional), `sale_unit`, `quantity_step`, `retail_price`, `wholesale_price` (opcional), `wholesale_condition` (opcional), `image` (opcional), `is_active`, `created_at`, `updated_at`.

Decisiones autorizadas el 2026-10-10: kg, unidad y paquete. Incremento inicial 0,1 kg o 1 unidad/paquete; cantidad positiva y múltiplo de ese incremento. El administrador puede definir incrementos positivos con hasta dos decimales para kg e incrementos enteros para unidad/paquete. Sin conversiones de gramos. Precios por unidad de venta en ARS con dos decimales, no negativos; mayorista opcional y manual. No inventar un catálogo real ni precios.

## 7. Reglas de cálculo
- Ambos precios expresan el importe por unidad de venta definida para ese producto.
- Cantidad positiva y múltiplo del incremento definido. Artículos por unidad/paquete usan incrementos enteros, artículos por peso pueden usar cantidades decimales.
- Subtotal = precio elegido × cantidad. Total estimado = suma de subtotales.
- No aplicar impuestos, descuentos, cargos de envío ni conversiones de unidad no documentadas.
- No prometer aplicación de mayorista por alcanzar una cantidad; la condición de texto es informativa.
- Ante producto inactivo/eliminado o precio ausente: impedir envío silencioso de un importe incorrecto; exigir revisión del carrito.
- Carrito vacío: CTA para enviar deshabilitado.

## 8. Mensaje WhatsApp (formato objetivo)
```
Hola! Quisiera realizar el siguiente pedido:

- Dulce de leche repostero - Marca ElNoNo - precio mayorista $10.000/kg - cantidad 3 kg - subtotal estimado: $30.000
- Otros productos...

Total estimado: $30.000

Gracias, espero su respuesta!
```
En el mensaje final, las cantidades, precios y subtotales deben corresponder a datos actuales y selección explícita. Marca opcional: omitir el segmento cuando no existe. El número WhatsApp se configura por entorno o ajustes seguros, no se incorpora un número ficticio en producción. El mensaje puede ser largo; en ese caso no cortar productos de manera silenciosa. El enlace abre el cliente WhatsApp disponible; el sitio no sabe si se envió.

## 9. Aviso previo obligatorio
“Los precios mostrados son estimados y pueden cambiar. La disponibilidad y la aplicación del precio mayorista están sujetas a confirmación del comercio por WhatsApp.”
Ofrecer “Volver al carrito” y “Continuar a WhatsApp”.

## 10. Criterios de aceptación MVP
1. Visitante navega y busca sin cuenta y sólo ve productos/categorías activos.
2. Selecciona cantidad y tipo de precio, reconoce la unidad y condición mayorista.
3. Cierra y reabre la pestaña; carrito permanece en el mismo navegador.
4. Los precios del carrito se recalculan desde productos vigentes y cambios se comunican.
5. Total/subtotales se calculan sin errores de precisión monetaria.
6. Antes de navegar a WhatsApp hay advertencia y posibilidad de cancelar.
7. El texto precargado contiene cantidades, unidades, tipo de precio, subtotales, total estimado.
8. Admin modifica productos, imágenes y categorías mediante Django Admin.
9. Interfaz usable en móvil con teclado, lector de pantalla y controles táctiles.
10. No se persisten pedidos ni se gestionan existencias.

## 11. Configuración comercial pendiente
El dueño debe configurar el número real de WhatsApp por entorno y cargar productos/precios reales en Admin. Denominación inicial: Dulce y Salado. Mayorista sin precio no se ofrece. Los subtotales se redondean a dos decimales con mitad hacia arriba y el total suma esos subtotales, con formato ARS es-AR.

## 12. Mejoras complementarias autorizadas
Exportación CSV completa/filtrada desde Admin con permisos de ver/cambiar productos. BusinessSettings central único: dirección comercial y enlace exacto opcional de Google Maps, editables con permisos del modelo. /como-llegar/ muestra dirección y enlace; sin dirección informa ausencia y no ofrece ubicación. No se cargan datos comerciales ficticios.

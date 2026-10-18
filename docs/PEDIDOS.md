# Solicitudes de pedido — 18/10/2026

El catálogo prepara una solicitud, sin confirmar compra, disponibilidad, pagos ni entrega. El cliente envía el texto efectivamente desde WhatsApp.

## Flujo vigente

Enviar Pedido (SVG de WhatsApp) abre el diálogo nativo Completá tus datos. Nombre de hasta 120 caracteres, sin exigir apellido. Retiro predeterminado; envío revela calle (160), número (30) y ciudad (100, inicialmente Viedma editable). Django y JavaScript validan campos activos. Datos ocultos de retiro se ignoran. Borrador personal sólo en memoria de la pestaña/iframe; nunca en localStorage. Cancelar/Escape antes del envío conserva carrito y borrador.

Enviar abre una pestaña provisional, revalida productos/precios/presentaciones y revisión de configuración WhatsApp bajo transacción. Cambios exigen volver al carrito y revisar nuevamente conservando el borrador. Durante una escritura en curso se deshabilita Cancelar y se impide cerrar con Escape o el contenedor iframe, para no informar una cancelación que podría haber llegado a PostgreSQL.

Order en catalog y migración aditiva 0010_order guardan nombre, modalidad/dirección, fecha con zona Argentina, productos/precios/subtotales originales y total Decimal entero. JSON guarda nombre/marca/descripción/unidad/cantidad/precio/subtotal, sin FK a Product ni dependencia de sus imágenes. BigAutoField usa secuencia PostgreSQL: DYS-000001, con posibles huecos por rollback, sin reutilización ni reset al renovar demos. UUID4 independiente controla la URL /orders/<token>/.

Confirmación firmada y clave UUID UNIQUE proporcionan idempotencia incluso con concurrencia. La huella compara artículos, revisión y datos normalizados. Un reintento devuelve el registro guardado antes de consultar el catálogo actual. Si se pierde una respuesta, el navegador repite la misma confirmación y datos, sin permitir editar esa solicitud incierta. El token de confirmación sin datos personales permanece en sessionStorage para recuperar reintentos de la misma selección.

El mensaje final conserva el formato editable del comercio y agrega código, cliente, modalidad, dirección sólo para envío y enlace privado. Se neutralizan saltos/control/formato introducidos por el cliente. Se guardan mensaje y URL UTF-8 api.whatsapp.com/send, de modo que Reenviar pedido no recalcula ni crea otro registro aunque cambien productos, teléfono o plantilla.

Sólo una respuesta de persistencia correcta vacía los artículos preparados de localStorage, sincroniza contador y catálogo y muestra ¡Tu pedido fue generado con éxito! 🎉. Artículos añadidos o modificados desde otra pestaña durante el envío se conservan. Un fallo de almacenamiento del navegador después de persistir informa que el pedido ya existe y ofrece reintentar únicamente la limpieza. Cerrar el resultado conserva el carrito restante; Reenviar pedido es un enlace seguro con noopener/noreferrer que también sirve si el popup fue bloqueado.

## Privacidad y administración

Detalle público de sólo lectura por UUID4, desconocido 404; sin listado ni búsqueda por código. No hay HTML físico por pedido. Datos escapados, Cache-Control private/no-store, X-Robots-Tag noindex/nofollow/noarchive y Referrer-Policy no-referrer. Enlace privado con información personal: compartir únicamente con el comercio/personas autorizadas. Admin permite consulta con permisos Django, sin altas/edición/borrado de órdenes.

## Configuración y futura publicación

PUBLIC_BASE_URL es obligatoria para preparar pedidos. Sin excepción local explícita debe ser HTTPS, sin usuario/contraseña, query, fragmento o ruta, con host público. manage.py check informa configuración inválida en producción. No se infiere el host desde una petición del visitante.

Prueba Raspberry autorizada por el dueño: PUBLIC_BASE_URL=http://192.168.0.80:8003 y ORDER_ALLOW_LOCAL_URLS=1. El enlace sólo funciona en la red que alcanza esa IP; no es accesible a clientes externos. Para publicar: configurar el dominio y HTTPS reales en la infraestructura elegida, cambiar PUBLIC_BASE_URL=https://<dominio-real>, ORDER_ALLOW_LOCAL_URLS=0, DJANGO_DEBUG=0, hosts permitidos y servir static/media con el mecanismo de producción. No se añade proxy, túnel ni infraestructura. Los pedidos existentes conservan su enlace/mensaje original; los nuevos usan la nueva configuración.

## Verificación

Tests en catalog/test_orders.py y tests/orders.browser.cjs cubren validación condicional, CSRF, instantáneas, reintentos, concurrencia PostgreSQL, migración aditiva, privacidad, popup bloqueado y respuesta perdida después de guardar. Chromium conserva la regresión de catálogo/carrito/Admin y añade normal/iframe a 320/390/768/1280 px. Ninguna prueba envía mensajes a terceros; WhatsApp se intercepta y las bases/media QA son descartables.

## Correcciones del flujo y presentación — 18/10/2026

El reconciliador de `.cart-items` conserva únicamente filas identificadas; el estado vacío sin ID se reemplaza en cada respuesta. No acumula nodos y mantiene conectados los controles de productos vigentes.

El éxito reside en `includes/order_result_dialog.html`, incluido en base fuera del drawer. El iframe, después del guardado y de confirmar la limpieza, libera el handle de WhatsApp y envía `dys-order-complete` al origen exacto. El padre verifica origin, source del iframe activo y destino HTTPS api.whatsapp.com/send antes de cerrar el panel y abrir su diálogo. Sólo se intercambian datos; no se inserta HTML recibido por mensajes. La misma plantilla y controlador sirven al carrito independiente; Cerrar/Escape vuelve al catálogo. En el panel se restaura el control que lo abrió. Reenviar abre exactamente la URL guardada, sin POST ni nuevo cálculo.

El resultado muestra únicamente el título y los dos párrafos solicitados, con Reenviar pedido/Cerrar iguales a la derecha. Si falla localStorage, aún no se muestra este éxito: el formulario queda sustituido por Pedido guardado y una acción que sólo reintenta la limpieza. Se conserva la confirmación idempotente hasta limpiar correctamente, incluida una reapertura posterior. No se vuelve a registrar el pedido.

Entrega utiliza radios en dos columnas; dirección con calle/número 3:1 (mínimo legible para número en móvil) y ciudad debajo. La migración nueva 0011_remove_order_door retira la columna obsoleta después de respaldar e inspeccionar sus valores; 0010 no se modifica. Los mensajes, enlaces y demás valores históricos permanecen intactos. Admin deriva los campos de Order y ya no ofrece esa columna. El detalle utiliza una sola card de máximo 860 px con marca interna; flex con márgenes auto centra contenido corto y permite desplazamiento natural para contenido largo.

Diagnóstico real previo: PUBLIC_BASE_URL=http://192.168.0.80:8003, excepción LAN habilitada, cuatro pedidos existentes y ningún valor no vacío en la columna retirada. En los cuatro, detail_url coincide con la última línea independiente de message y decodificar text de whatsapp_url reproduce exactamente message: sin espacios invisibles en URL, reemplazos Unicode ni doble codificación UTF-8. No se encontró un defecto de generación que justifique cambiar api.whatsapp.com/send. Esto no prueba la detección del enlace dentro de la aplicación WhatsApp. La IP es privada; falta un dominio HTTPS real y acceso externo para comprobar esa segunda condición. No se cambian URL históricas.

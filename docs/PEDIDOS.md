# Solicitudes de pedido — 18/10/2026

El catálogo prepara una solicitud, sin confirmar compra, disponibilidad, pagos ni entrega. El cliente envía el texto efectivamente desde WhatsApp.

## Flujo vigente

Enviar Pedido (SVG de WhatsApp) abre el diálogo nativo Completá tus datos. Nombre de hasta 120 caracteres, sin exigir apellido. Retiro predeterminado; envío revela calle (160), número (30), puerta opcional (80) y ciudad (100, inicialmente Viedma editable). Django y JavaScript validan campos activos. Datos ocultos de retiro se ignoran. Borrador personal sólo en memoria de la pestaña/iframe; nunca en localStorage. Cancelar/Escape antes del envío conserva carrito y borrador.

Enviar abre una pestaña provisional, revalida productos/precios/presentaciones y revisión de configuración WhatsApp bajo transacción. Cambios exigen volver al carrito y revisar nuevamente conservando el borrador. Durante una escritura en curso se deshabilita Cancelar y se impide cerrar con Escape o el contenedor iframe, para no informar una cancelación que podría haber llegado a PostgreSQL.

Order en catalog y migración aditiva 0010_order guardan nombre, modalidad/dirección, fecha con zona Argentina, productos/precios/subtotales originales y total Decimal entero. JSON guarda nombre/marca/descripción/unidad/cantidad/precio/subtotal, sin FK a Product ni dependencia de sus imágenes. BigAutoField usa secuencia PostgreSQL: DYS-000001, con posibles huecos por rollback, sin reutilización ni reset al renovar demos. UUID4 independiente controla la URL /orders/<token>/.

Confirmación firmada y clave UUID UNIQUE proporcionan idempotencia incluso con concurrencia. La huella compara artículos, revisión y datos normalizados. Un reintento devuelve el registro guardado antes de consultar el catálogo actual. Si se pierde una respuesta, el navegador repite la misma confirmación y datos, sin permitir editar esa solicitud incierta. El token de confirmación sin datos personales permanece en sessionStorage para recuperar reintentos de la misma selección.

El mensaje final conserva el formato editable del comercio y agrega código, cliente, modalidad, dirección sólo para envío y enlace privado. Se neutralizan saltos/control/formato introducidos por el cliente. Se guardan mensaje y URL UTF-8 api.whatsapp.com/send, de modo que Reenviar pedido no recalcula ni crea otro registro aunque cambien productos, teléfono o plantilla.

Sólo una respuesta de persistencia correcta vacía los artículos preparados de localStorage, sincroniza contador y catálogo y muestra ¡Tu pedido está listo! 🎉. Artículos añadidos o modificados desde otra pestaña durante el envío se conservan. Un fallo de almacenamiento del navegador después de persistir informa que el pedido ya existe y ofrece reintentar únicamente la limpieza. Cerrar el resultado conserva el carrito restante; Reenviar pedido es un enlace seguro con noopener/noreferrer que también sirve si el popup fue bloqueado.

## Privacidad y administración

Detalle público de sólo lectura por UUID4, desconocido 404; sin listado ni búsqueda por código. No hay HTML físico por pedido. Datos escapados, Cache-Control private/no-store, X-Robots-Tag noindex/nofollow/noarchive y Referrer-Policy no-referrer. Enlace privado con información personal: compartir únicamente con el comercio/personas autorizadas. Admin permite consulta con permisos Django, sin altas/edición/borrado de órdenes.

## Configuración y futura publicación

PUBLIC_BASE_URL es obligatoria para preparar pedidos. Sin excepción local explícita debe ser HTTPS, sin usuario/contraseña, query, fragmento o ruta, con host público. manage.py check informa configuración inválida en producción. No se infiere el host desde una petición del visitante.

Prueba Raspberry autorizada por el dueño: PUBLIC_BASE_URL=http://192.168.0.80:8003 y ORDER_ALLOW_LOCAL_URLS=1. El enlace sólo funciona en la red que alcanza esa IP; no es accesible a clientes externos. Para publicar: configurar el dominio y HTTPS reales en la infraestructura elegida, cambiar PUBLIC_BASE_URL=https://<dominio-real>, ORDER_ALLOW_LOCAL_URLS=0, DJANGO_DEBUG=0, hosts permitidos y servir static/media con el mecanismo de producción. No se añade proxy, túnel ni infraestructura. Los pedidos existentes conservan su enlace/mensaje original; los nuevos usan la nueva configuración.

## Verificación

Tests en catalog/test_orders.py y tests/orders.browser.cjs cubren validación condicional, CSRF, instantáneas, reintentos, concurrencia PostgreSQL, migración aditiva, privacidad, popup bloqueado y respuesta perdida después de guardar. Chromium conserva la regresión de catálogo/carrito/Admin y añade normal/iframe a 320/390/768/1280 px. Ninguna prueba envía mensajes a terceros; WhatsApp se intercepta y las bases/media QA son descartables.

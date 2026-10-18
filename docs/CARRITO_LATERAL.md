# Carrito lateral en iframe — 17/10/2026

El botón del carrito y la acción Ver carrito abren un panel de aproximadamente el 46% del ancho de escritorio a la derecha (mínimo 520 px en tablet). El catálogo conserva filtros, scroll y geometría; el resto queda atenuado y ligeramente difuminado. Los productos tienen scroll y total/WhatsApp permanecen en el pie. En pantallas de hasta 600 px ocupa toda la pantalla con flecha para volver; en escritorio tiene cruz arriba a la izquierda. Clic exterior/Escape cierran, y el foco vuelve al control de origen.

Vacío: total cero y Agregar productos abajo, que cierra el panel. Se mantienen cantidades enteras, basura con 1/menos con más de 1, sincronización de contador/catalogo, precio minorista vigente, revisión, mensaje editable, copiado y apertura de WhatsApp. Escape cierra primero la revisión o foto abiertas. Cerrar el panel invalida una preparación pendiente y cierra su pestaña provisional. No confirma pedidos ni envía mensajes.

## Implementación y archivos

- templates/includes/cart_drawer.html y static/js/cart-drawer.js: modal, carga del iframe y cierre/foco/scroll.
- templates/cart_frame.html, includes/cart_app.html, cart.html y cart_contents.html: frame mínimo y componentes compartidos, lista/pie/CTA vacío.
- catalog/views.py: variante ?panel=1 de cart_page, SAMEORIGIN sólo en esa vista y contexto de presentación del vacío en cart_refresh.
- static/js/cart-frame.js y cart.js: Escape/cierre, sincronización y cancelación de provisional al descargar el frame; cálculo/validaciones/endpoints anteriores conservados.
- static/js/header.js y static/css/site.css: buscador sin contorno de mouse con foco de teclado en el conjunto, ubicación centrada/limitada, panel responsive y backdrop.
- catalog/test_views.py, test_business.py y tests/browser.spec.cjs: vista/seguridad/fallback, geometría, vacío, cantidades, scroll, copiado, revisión/cancelación, toque y error de carga.

Iframe propio con mismo origen; mensajes de cierre comprueban origen y ventana emisora. No se agrega librería, servicio, modelo ni migración. El acceso /carrito/ conserva la página independiente como respaldo y para enlaces sin JavaScript. Un fallo de carga conserva cierre y enlace para abrirlo en otra pestaña.

## Probar y actualizar

En esta PC abrir http://localhost:8000/, hacer Ctrl+F5, sumar productos y tocar carrito. Probar la cruz, clic exterior, volver móvil, lista larga, pie fijo, vacío y revisión/copiado. Productos/fotos/configuración no se limpian ni cambian. No ejecutar seed ni reset para aplicar esta interfaz.

Para una instalación futura autorizada: revisar el diff, respaldar DB/media, aplicar/reconstruir el código y verificar check/migraciones pendientes de tareas previas. Esta tarea no añade migraciones. Revisar que proxy/política de headers permita el SAMEORIGIN de la vista del carrito, manteniendo protección de otras páginas. Raspberry requiere autorización expresa; no se accedió ni desplegó allí.

## Verificación

Verificación final: 180 Django completos, 9 Node y 59 Chromium correctos; 9 del grupo lateral repetidos tras añadir la eliminación del último artículo, también correctos. Ruff/check/makemigrations --check/diff correctos. Cobertura de SAMEORIGIN/frame mínimo/fallback, foco del buscador por mouse/Tab, centro limitado de Ubicación, geometría y scroll sin desplazar catálogo, pie fijo, lista larga, vacío/última eliminación, cantidades sincronizadas, toque/volver, Escape anidado, copiado real en iframe, revisión y cancelación de provisional WhatsApp, mensaje de origen/ventana incorrecta, fallo de carga y apertura desde aviso con retorno de foco.

Comprobación sobre el sitio local con seis presentaciones/fotos de Baño de repostería blanco: nueve anchos (320/390/430/600/768/800/1050/1280/1440), panel a la derecha o completo, total fijo al hacer scroll, sin desplazamiento inicial del catálogo, sin errores JS/peticiones externas/incidencias automáticas axe WCAG 2A/AA/2.1AA. Capturas privadas local-cart-drawer-1440.png, local-cart-drawer-390.png y local-location-centered-1440.png inspeccionadas. No se afirma evaluación exhaustiva con lectores o dispositivos físicos.

## Ajuste de lectura y avisos

Ancho ampliado respecto de los 500 px anteriores, manteniendo pantalla completa hasta 600 px y todo el comportamiento de scroll/total/cierre. Cards de catálogo centradas en sus columnas. Avisos flotantes arriba, con contenido centrado dentro y mensaje/Ver carrito en una fila cuando caben y wrapping seguro en móvil. Footer Ubicación ahora abre Maps directamente en otra pestaña con la configuración actual; el header conserva su desplegable.

Verificación de este ajuste: 181 Django, 9 Node y 63 Chromium correctos; doce anchos de grilla y cinco del panel sobre fotos locales, axe sin incidencias automáticas y capturas inspeccionadas. Detalle en QA.md.

## Corrección posterior de avisos y actualización

Los avisos aparecen arriba y sólo su contenido se centra dentro. El estado de consulta de catálogo queda reservado a lectores de pantalla, sin ocupar lugar en la lista. Catálogo paginado de a 20 para completar filas de cinco/cuatro columnas. Archivos de esta corrección: site.css, includes/cart_app.html y catalog/views.py, sus pruebas y documentación.

En local, Ctrl+F5; sumar/restar con el panel abierto, comprobar lista/total estables y recorrer las tres páginas de 45 productos a 1920x1080. Si la instalación usa un proceso sin recarga automática, reiniciar web al actualizar views.py. No hay nuevas migraciones ni carga de datos. Actualización futura según los respaldos/procedimiento existente y sólo con autorización para Raspberry.

Validación de la corrección: 182 Django, 9 Node y 66 Chromium; siete específicos del grupo responsive/carga. Comparación de posiciones antes/durante/después del recálculo en ambas variantes, tres páginas completas a cinco columnas y ocho anchos locales con axe sin incidencias automáticas. Detalle en QA.md.

## Actualización silenciosa y listas largas

Sumar/restar/quitar dentro del carrito no muestra éxitos ni recarga el iframe. Sólo cambian los datos necesarios; fotos/títulos/filas intactas y scroll se conservan. El cálculo sigue siendo del servidor, con revisión bloqueada mientras consulta y errores/reintento si falla. Apertura sin Cargando carrito; respaldo sólo ante fallo. Lista sin compresión aunque incluya muchas fichas.

Catálogo: Se agregó {producto} al carrito. Ver carrito. Cruces acordes al color de cada aviso, sin naranja. Vista previa con icono de copiar a la derecha del label, total sólo en mensaje y sin párrafo redundante. Fallback/copiar/revisión/advertencia comercial conservados.

Archivos: static/js/cart.js, quantity.js y cart-drawer.js; static/css/site.css; plantillas cart_review.html, includes/notification.html y cart_drawer.html; pruebas/guías/seguimiento. Sin nueva migración, dependencias o datos. Local: Ctrl+F5, abrir muchos artículos, cambiar cantidades, quitar y revisar/copiar. Para actualización futura autorizada, aplicar código/static/template y seguir respaldos y controles del procedimiento existente; Raspberry requiere autorización expresa.

Validación de esta iteración: 184 Django, 9 Node y 72 Chromium, más seis del grupo específico repetidos. Cuarenta y cinco productos locales en ocho anchos, axe sin incidencias automáticas y capturas inspeccionadas. Detalle en QA.md.

## Visor y revisión simplificados

Visor sin marco, foto completa y cruz blanca fuera sobre fondo más oscuro. Botón de revisión conserva apariencia mientras recalcula. Total; revisión con Volver/Enviar a WhatsApp, campo un poco mayor y copiar al lado del label. Advertencia separada retirada; mensaje guardado utiliza Subtotal. Mínimo 1 confirmado, sólo enteros: errores de cantidad arriba, sin recuadro visible en la ficha y sin redondear.

Archivos: site.css, cart.js/cart-core.js/quantity.js, image_dialog.html, quantity_control.html, cart_app.html, cart_contents.html/cart_review.html; cart.py/views.py/whatsapp_templates.py; migración 0007 y pruebas/documentación. Actualización futura autorizada: respaldar DB/media/configuración, aplicar código, migrate, static/reinicio de web según instalación y check; probar zoom, revisión, negativos/cero/fracciones y cantidades válidas. No ejecutar seed/reset. Reversa de migración no revierte textos; restaurar formato desde respaldo si se desea. Raspberry sigue requiriendo autorización expresa.

Validación de zoom/revisión/cantidad: 188 Django, 9 Node y 77 Chromium, ocho específicos repetidos; ocho anchos locales con axe/capturas inspeccionadas. 0007 aplicada local con respaldo/comparación de configuración y hashes de productos/usuarios/horarios. Datos conservados, QA temporal retirado.

También se ajusta catalog.js para no quitar el foco de otro control tras cerrar la foto; teclado/cierre y acción siguiente quedan cubiertos.

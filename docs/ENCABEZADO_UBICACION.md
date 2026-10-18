# Encabezado y ubicación desplegable — 17/10/2026

La marca conserva nombre/logo y elimina el subtítulo. El encabezado reúne buscador, Ubicación, Horarios y carrito; debajo aparecen categorías y el retorno Catálogo fuera del catálogo. Los filtros respetan los datos/orden activos de Admin y se dirigen al catálogo desde cualquier página. No se añade cuenta de clientes.

## Ubicación y horarios

En Admin → Configuración comercial, editar dirección, enlace exacto de Google Maps opcional y horarios. Ubicación abre la dirección y un enlace con pin SVG con nombre accesible para abrir Maps en otra pestaña. Si falta enlace se busca por dirección; si falta dirección se informa ausencia sin enlace falso. La página e iframe anteriores fueron eliminados. `/ubicacion/` y `/como-llegar/` redirigen 301 a `/?ubicacion=1#ubicacion`, renderizado abierto aun sin JavaScript. El footer abre Google Maps directamente en otra pestaña; las rutas anteriores conservan el acceso al panel.

Horarios muestra estado vigente y la semana publicada, con el cálculo previo en Buenos Aires cada 15 segundos. Sin publicar informa «Horarios no disponibles». No se modifican valores guardados. Details/summary conserva teclado y funcionamiento sin JS; JS añade cierre exterior/Escape, retorno del foco y exclusión entre paneles.

## Archivos

- templates/base.html, home.html e includes/header_search.html, catalog_navigation.html, location_panel.html, business_hours.html: composición y controles.
- static/css/site.css: distribución responsive, paneles y enlaces; static/js/header.js: mejora de desplegables; business-hours.js: reloj sin lógica duplicada de cierre; cart.js: descarta recálculos que ya no corresponden al carrito guardado.
- catalog/context_processors.py: categorías activas disponibles también en carrito; catalog/views.py y config/urls.py: retiro de vista y compatibilidad de rutas anteriores.
- catalog/test_business.py, test_views.py y tests/browser.spec.cjs: comportamiento, seguridad, filtros, navegación, teclado y responsive.

## Actualización

En esta PC los archivos se sirven desde el repositorio actual: abrir http://localhost:8000/ y recargar con Ctrl+F5. Esta tarea no agrega migraciones ni requiere sembrar/limpiar la base. Conserva los 45 productos, sus imágenes, usuarios y configuración.

Para otra instalación autorizada, respaldar DB/media, revisar el diff completo y aplicar el código en una ventana acordada; reconstruir/reiniciar web, ejecutar las migraciones pendientes de tareas anteriores y las comprobaciones de Django. Verificar búsqueda, categorías, carrito y ambos paneles. No ejecutar seed/reset como parte de la actualización. Raspberry requiere autorización expresa; no se accedió ni se desplegó allí.

## Sincronización detectada durante la revisión

Una respuesta de recálculo pendiente podía restaurar el producto que otra pestaña acababa de eliminar si el evento storage llegaba tarde. Antes de aplicar HTML/cantidades normalizadas, cart.js compara el carrito actual guardado con el enviado; ante diferencia descarta esa respuesta, lee el estado actual y recalcula. No cambia el formato de almacenamiento ni el cálculo de precios. La regresión retiene una respuesta y simula entrega tardía del evento: antes restauraba un artículo y después conserva cero.

## Verificación

Verificación final: 177 pruebas Django completas sin omisiones, 9 Node y 46 Chromium correctas; check, Ruff, migraciones pendientes de modelo y diff sin incidencias. Comprobación adicional del sitio local con sus 45 productos/45 imágenes/3 categorías/configuración existente: nueve anchos (320/390/600/768/800/1049/1050/1280/1440), ambos paneles dentro del viewport, axe sin incidencias automáticas, búsqueda desde carrito, seis presentaciones por nombre, cantidades sincronizadas, redirecciones y cero peticiones externas/errores JS. Capturas privadas local-header-location-1440.png y local-header-hours-390.png inspeccionadas. Esto no sustituye una evaluación completa con lectores de pantalla o teléfonos reales.

## Ajuste posterior: espacio, hover e íconos

El buscador tiene máximo 600 px en escritorio. Ubicación, Horarios y carrito tienen más espacio, texto mayor y altura de 48 px; categorías sólo texto, sin íconos. Las flechas son chevrons SVG fijos hacia abajo. El enlace Maps usa un pin SVG de líneas en lugar del emoji rosado.

Con mouse/capacidad de hover los paneles abren al pasar el puntero y cierran al salir con 200 ms de margen para alcanzar el contenido. Hover no mueve el foco; un enlace enfocado mantiene abierto su panel. Escape cierra sin reapertura inmediata. Clic de mouse mantiene abierto; teclado Enter/Espacio y toque alternan abrir/cerrar, y se conserva clic exterior y fallback sin JS. No cambia datos, precios, formatos, ni requiere migraciones.

### Verificación de este ajuste

Validación final del ajuste: 177 Django completos, 9 Node y 50 Chromium correctos, sin omisiones; check/Ruff/makemigrations --check/diff correctos. Las nuevas pruebas comprueban ancho máximo de búsqueda, acciones de 48 px/separación de 16 px, categorías sin íconos, pin SVG, flecha fija antes/después, apertura por hover sin mover foco, recorrido al panel, cierre al salir, cambio de panel/Escape, enlace enfocado persistente, teclado y pantalla táctil real emulada (tap abre/cierra/exterior). Fallback sin JS y filtros/carrito/WhatsApp siguen cubiertos en la suite completa.

Sitio local habitual: diez anchos (320/390/600/768/800/1049/1050/1280/1440/1920), ambos paneles dentro del viewport, sin desbordes ni incidencias automáticas axe WCAG 2A/AA/2.1AA, sin peticiones externas ni errores JS; 45 productos conservados. Capturas privadas header-hover-closed-1440.png, header-hover-location-panel-1440.png y header-hover-location-panel-390.png inspeccionadas. Se conserva foco visible por teclado. Esta revisión automática no afirma una auditoría completa de lectores o dispositivos reales.

## Footer directo

Ubicación en el footer enlaza a la URL de Maps validada/configurada y abre otra pestaña; no activa el desplegable. Si falta dirección muestra indisponibilidad sin inventar enlaces. El control del header y las rutas de compatibilidad siguen mostrando dirección y enlace.

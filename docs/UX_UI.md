# UX/UI mobile-first

> Decisión vigente 18/10/2026: solicitudes persistidas, formulario de datos y limpieza posterior al guardado, según [PEDIDOS.md](PEDIDOS.md). Esta decisión reemplaza las referencias históricas a no persistir pedidos, conservar el carrito después de preparar y copiar/vista previa del mensaje. Continúan fuera de alcance pagos, stock, estados y cuentas de clientes.

## Objetivo
Catálogo veloz y sencillo, orientado primero a teléfonos móviles. Priorizar navegación, legibilidad de precios, selección de cantidades y revisión del carrito por encima de animaciones.

## Identidad
Tomar como referencia el logotipo provisto del comercio: naranja como color principal, con acentos suaves en fucsia, cyan y amarillo sobre fondos blancos o crema. Los colores del logo son referencias visuales, no se fijan códigos hex exactos hasta definir tokens desde el recurso original y comprobar contraste. Evitar fondos saturados y usar naranja en CTA, estado seleccionado y destacados.

## Vistas previstas
- `/`: buscador accesible, selector nativo de categorías con formulario GET en móvil y chips desde 800 px (espacio suficiente para controles y grilla). Búsqueda conservada sin JavaScript. Grilla de tarjetas adaptativas según espacio.
- `/carrito/`: artículos, cantidades, precio público, subtotales y total estimado; control derecho basura/1/+ o −/cantidad/+. Restablecer sólo ante storage corrupto.
- Confirmación de salida: aviso sobre estimación de precios, disponibilidad sin confirmar; cancelar o continuar a WhatsApp.
- `/admin/`: Django Admin sin interfaz hecha a medida.

## Interacción
- Priorizar 360–430 px, luego tablet y desktop.
- Áreas táctiles de ~44×44 px o más; foco visible y formularios etiquetados.
- Cantidades enteras: +/basura/− de 44×44 px en catálogo; campo entero compacto editable, basura con 1 y − con más de 1 en carrito. Incremento fijo en 1; formato v1 con centésimos conservado por compatibilidad. Placeholder discreto «Sin imagen» con espacio estable; precio minorista sin etiqueta y sin condiciones mayoristas en el flujo público.
- Jerarquía visual del catálogo: foto, nombre y descripción cercanos, un único precio y controles a la derecha. La marca se conserva en datos, búsqueda y mensaje.
- Mostrar unidades junto a precios y cantidades, evitando “$10.000” sin contexto.
- Precio público minorista calculado por el servidor, sin selector de tarifa.
- CTA al carrito fácilmente accesible en móvil, considerando barra inferior pegajosa cuando no tape contenido o controles del sistema.
- Estados vacíos, imagen ausente, producto inactivo, precios actualizados y datos inválidos claramente informados.
- Evitar scroll horizontal, diálogos intrusivos repetidos y navegación innecesaria.
- Feedback flotante en la parte superior, con texto centrado dentro: éxito verde con «Ver carrito» al agregar, errores rojos, advertencias ámbar e información neutra. Cinco/ocho segundos, cierre manual y pausa por hover/foco; errores que bloquean permanecen también junto al campo/producto. Un solo aviso live visible, sin duplicar anuncios. Confirmaciones administrativas nativas.
- El recálculo conserva altura, controles, foco y scroll del carrito. Mientras se consulta se ocultan sólo importes y se bloquea revisión; ante fallo se mantienen controles y se permite reintentar.
- Horario compacto dentro del header. Details/summary nativo con estado textual y punto verde/neutro, siete días y todos sus intervalos, sin textos auxiliares. Panel flotante responsive con scroll interno, cierre exterior/Escape y foco visible; sin configuración no se deduce cierre. Funciona sin JavaScript; el estado en ese caso corresponde a la carga de página.

## Rendimiento y accesibilidad
HTML semántico, etiquetas y textos alternativos, contraste WCAG AA cuando corresponda. Imágenes responsive, lazy loading de fotos fuera de pantalla y tamaños optimizados. No bloquear render con dependencias grandes. Navegación por teclado y uso con VoiceOver/TalkBack deben funcionar en los flujos principales.

## Criterio de aceptación UX
En móvil se puede encontrar un artículo, identificar ambos precios/condición, ajustar cantidad, revisar y abrir WhatsApp sin zoom forzado ni campos inaccesibles; nunca se confunde la estimación con una compra confirmada.

## Segunda iteración — navegación compacta

Horarios integrados dentro del header en una segunda fila compacta, sin textos auxiliares. Details conserva teclado y fallback sin JS; panel absoluto con altura limitada, scroll interno y cierre exterior/Escape (restaura summary). Abrirlo no cambia altura del header ni posición del contenido. El reloj y la zona Buenos Aires permanecen iguales.

Catálogo sin introducción comercial; Nuestros productos es el h1. Buscador conserva placeholder y etiqueta oculta. Selector móvil aplica GET automáticamente con JS y conserva búsqueda; Filtrar sólo sin JS. Footer móvil centrado, icono ubicación y enlace Instagram oficial con target blank/noopener/noreferrer. Toolbar móvil del carrito apilada, ambos controles de igual ancho. Escritorio conserva chips y disposición existente.

## Segunda iteración — mapa del comercio

Cómo llegar incluye el iframe fijo exacto suministrado por el propietario, responsive también en móvil, title accesible, carga lazy y referrerpolicy strict-origin-when-cross-origin. La dirección/enlace Admin y el botón siguen siendo independientes del iframe y funcionan ante un bloqueo del recurso externo. Si el comercio se muda, actualizar la URL fija en templates/directions.html además de los datos del Admin. No usa API key ni scripts Maps.

## Segunda iteración — fotos, condiciones y avisos

La fotografía abre un único dialog nativo del catálogo con mismo archivo optimizado, imagen contain, nombre accesible, cierre botón/Escape/fondo y devolución de foco. Sin foto se mantiene Sin imagen; sin JS el enlace abre el archivo. Condiciones mayoristas conservadas en administración/exportaciones, sin mostrarlas en catálogo/carrito.

Notifications.show centraliza éxitos/info (5 s), errores/warnings (8 s), reemplazo, cierre y pausa por hover/foco. Componente fijo superior con safe-area, acción Ver carrito, sin alterar scroll/foco/layout. Sólo un aviso visible/live; el diálogo de revisión tiene una ubicación del mismo componente para mantenerlo operable dentro del modal. Explicaciones persistentes de campos/productos/red/almacenamiento permanecen sin anuncios live duplicados. Invalidar cantidad del carrito dispara la validación vigente y bloquea revisión/importes; Admin conserva sus mensajes nativos.

## Segunda iteración — apertura de WhatsApp

Continuar inicia una pestaña provisional desde el clic, sin destino WhatsApp hasta completar la última revalidación. Se anula opener y se fija no-referrer manteniendo el handle para cerrar. Ante precios/datos cambiados se cierra y exige revisión; ante cancelación/error se cierra sin salir. Tras validar se conserva el enlace target blank/noopener/noreferrer para apertura manual si el navegador bloquea o el usuario cierra el contexto nuevo. El carrito permanece en su pestaña, sin borrado ni envío automático. Referencia de comportamiento del navegador: https://html.spec.whatwg.org/multipage/nav-history-apis.html (noopener/noreferrer retornan null; por eso la pestaña provisional se desacopla antes de navegar y el enlace manual usa ambos atributos).

## Correcciones puntuales — composición vigente

Esta solicitud sustituye exclusivamente la disposición de header/footer/fotos/dirección indicada en la segunda iteración; los demás comportamientos anteriores se conservan como historial.

- Tarjetas: marco constante de 210 px con fondo neutro, enlace de altura definida en Flex y fotografía contain centrada. Nunca depender de una fila Grid automática que crezca con el tamaño intrínseco de la foto. Una única imagen optimizada, lazy/async y archivos originales intactos.
- Ampliación: sólo fotografía y × de cierre ≥44 px. Dialog tiene nombre genérico y descripción oculta; alt conserva identificación del producto para lectores. Sin encabezado, marca, descripción o texto comercial visible. Botón/Escape/exterior y retorno del foco; enlace nativo sin JS.
- Header actual: marca sin subtítulo, buscador y acciones Ubicación/Horarios/Carrito desde 1050 px; buscador en fila completa entre 600–1049 px y bloques apilados bajo 600 px. Categorías en franja inferior, selector nativo bajo 800 px y enlaces por encima. Logo de 64 px, aria-current y controles ≥44 px; paneles flotantes limitados al viewport.
- Ubicación actual: desplegable nativo junto a Horarios, dirección de Admin y enlace con pin SVG de 44 px a Maps, con nombre accesible y aviso de otra pestaña. Se retiran página/iframe; rutas antiguas redirigen al catálogo con panel abierto. Sin dirección, aviso claro sin enlace falso.
- Footer: enlaces/iconos, nombre y aviso centrados en todas las resoluciones; mismos destinos y área táctil.

Aceptación verificada en 360/390/430/768/1280 y límite de header 800 px, con capturas/mediciones reales y axe. No hay nuevas dependencias/modelos/migraciones.

## Nueva iteración — composición actual

Sustituye las indicaciones históricas de títulos y toolbar: Nuestros productos, Categoría móvil, Revisá tu carrito y Antes de abrir WhatsApp permanecen accesibles con visually-hidden, sin espacio visual reservado. El placeholder es «Buscar productos, marcas y más...». Catálogo de 20 por página con rango real «1–20 de 45 productos», filtros GET y navegación Anterior/Página/Siguiente; vacío coherente y controles ocultos si no hay más páginas.

El carrito comienza con los artículos; no hay Seguir viendo productos ni Vaciar. Fotos actuales de 56 px contain junto al nombre, Quitar a la derecha; sin foto no se reserva una columna ni se muestra placeholder. Usa el mismo dialog de catálogo, sólo imagen/×, con delegación para HTML recalculado. El título oculto de revisión sigue nombrando el diálogo y recibiendo foco; se retira sólo el párrafo redundante de texto largo. Aviso obligatorio, mensaje/copiar y apertura manual permanecen íntegros.

## Exportación PDF y ajustes puntuales

El nuevo encabezado sustituye esa disposición histórica: Ubicación y Horarios son desplegables junto al carrito, con buscador y categorías integrados; Catálogo queda como retorno contextual en la franja inferior.

Admin → Productos ofrece PDF con imágenes y PDF sin imágenes junto al CSV; las dos variantes A4 son listas blancas con texto completo, separadores finos, ARS, inactivos identificados y página/aviso comercial. Sin fotos el texto ocupa todo el ancho. Con fotos, encaje proporcional de aprox. 75 px al inicio del registro; imagen ausente/ilegible sólo muestra un aviso discreto.

Quitar se representa con una papelera SVG inline, naranja secundario, objetivo 44×44 px y aria-label «Quitar [nombre] del carrito». El icono decorativo se oculta a lectores; el producto retirado dispone de una etiqueta contextual accesible. Se conservan handler, almacenamiento y avisos existentes.

Desde 800 px, las filas del carrito con foto disponen de una columna de 132 px a la izquierda. Nombre/marca/precios/condición/controles/subtotal quedan a su derecha y la papelera arriba a la derecha. Entre 800 y 1099 px, los controles de estas filas se apilan para mantener espacio útil. Sin imagen se recupera todo el ancho, también si se elimina en Admin. Bajo 800 px se conserva la miniatura de 56 px junto al nombre y la distribución móvil previa. Fotos contain y visor compartido intactos.

Los productos [DEMO] y sus marcas/precios son ficticios; se incorporan únicamente por el comando manual documentado en README, nunca durante navegación o arranque.

## Nuevas variantes PDF del Admin

PDF tabla compacta y PDF tabla con imágenes se agregan junto al CSV y ambas listas, sin reemplazarlas. A4 horizontal blanco, filas flexibles y encabezados repetidos, tipografía oscura de 9 pt, márgenes y separadores finos; no categoría. Compacta usa abreviaturas monetarias claras. Con imágenes conserva los ocho encabezados completos, miniaturas contain de unos 51 px y avisos discretos cuando faltan; texto completo, ARS, inactivos y nota/página en las dos tablas.

## Fotografías cuadradas del catálogo — disposición vigente

Sustituye el marco histórico de 210 px: cada tarjeta reserva proporción 1:1, incluida Sin imagen. Miniatura cover/center, sin distorsión y sin bandas; recorta extremos no cuadrados. Visor siempre contain con foto completa, accesible por clic/teclado y enlace nativo sin JS; carrito/PDF también completos. Se contrastaron fotografías comerciales, incluyendo envases; su identificación central sigue visible. Etiquetas junto al borde pueden ocultarse en miniatura: abrir el visor y preferir fotos fuente cuadradas, bien encuadradas. Sin cambios físicos, modelos o editor.

## Importación en Django Admin

Importar CSV aparece junto a exportaciones sólo con permiso de agregar productos. Pantalla nativa del Admin, etiqueta de archivo/ayuda, enlace subrayado a plantilla y botón Analizar archivo; elegir un archivo no lo importa. Preview con tabla semántica desplazable horizontalmente, números de fila, valores efectivos y conteos nuevo/duplicado/error; mensajes escapados y descriptivos. Cualquier error oculta Confirmar importación y exige corregir/reanalizar. Sin errores, el botón explícito confirma los nuevos y omite duplicados sin sobrescribir. Vista previa vencida/modificada informa reanálisis; datos cambiados pueden presentar preview nueva para revisar/confirmar. Éxito usa mensaje nativo con creados/omitidos y carga vacía. Sin JavaScript adicional ni cambios al catálogo/carrito.

## Ajustes visuales vigentes — 2026-10-11

Visor compartido de ancho intrínseco, padding 10 px y foto en dimensiones naturales con máximos del viewport; no amplía fuentes pequeñas. Botón de cierre opaco 44×44 superpuesto arriba a la derecha, sin franja superior adicional. Foto completa/proporcional, foco/cierres y enlace nativo anteriores conservados. Verificado incluso en 844×300.

Disposición actual (2026-10-17): contenedor de 1360 px, Grid auto-fill con mínimo 240 px, cinco columnas desde espacio suficiente (1440 px probado), cuatro a 1280, tres a 800/1000 y dos a 768. Máximo de card 340 px, 300 desde 700 px: un resultado único conserva su ancho. Marcos cuadrados/cover, objetivos de 44 px y paginación de 20. Nombre y descripción con separación .15rem, padding .8rem, precios y controles compactos.

Carrito desde 800 px centra verticalmente la foto de 132 px respecto de toda la tarjeta, incluidos nombres/condiciones largos. Datos y controles permanecen a su derecha; sin foto recupera ancho. Bajo 800 px no cambia la disposición de 56 px.

Los cuatro PDF muestran el logo existente completo/proporcional de 16 mm arriba a la izquierda, nombre a su derecha y título debajo; encabezado en cada página, con fallback textual. Sólo las listas cambian etiquetas a negrita/valores normales; descripción normal. Foto de lista centrada, datos TOP; si el texto necesita varias páginas, se centra en el fragmento visible que contiene la foto, sin duplicarla. Tablas conservan columnas/encabezados/distribución anteriores salvo marco comercial.

## Mensaje WhatsApp y copiado — disposición vigente

El formato del mensaje es editable en Configuración comercial. Por defecto: saludo con 🛍️, título numerado, marca/presentación opcionales, viñetas •, Precio minorista, Cantidad y Subtotal estimado; divisor Unicode y total con 💰 en bloque monoespaciado. Los formatos permiten cambiar frases, orden, emojis y separadores conservando los campos necesarios para un pedido completo. El textarea permanece de texto plano y usa exactamente el mensaje generado por el servidor, igual que el copiado y el enlace.

Copiar mensaje completo intenta Clipboard API y, si no está disponible, copy alternativo síncrono dentro del clic sobre el textarea existente. Tras un rechazo moderno se intenta también el alternativo. Éxito sólo con promesa resuelta o retorno true; restaura selección/foco/scroll al copiar mediante fallback. Si no se confirma, el campo queda enfocado y completamente seleccionado con el aviso manual existente. No hay nuevos nodos, cierres, navegación ni cambios del carrito por copiar; clics pendientes duplicados y avisos tras cerrar la revisión se descartan. Las políticas del navegador pueden impedir ambos métodos.

## Interacción vigente del catálogo — 2026-10-17

El único control visible de una ficha ausente del carrito es +. Se transforma en basura/1/+ y luego −/cantidad/+; al borrar se recupera foco en +. No hay campo editable, label visual, selector de tarifa ni CTA Agregar dentro de la card. Nombre del producto en etiquetas accesibles y aviso de agregado; output sin live duplicado. No se reducen objetivos táctiles por debajo de 44 px. Errores de cantidad anterior/storage quedan junto al control; guardar debe confirmar antes de reflejar éxito. Sin JS permanecen catálogo/búsqueda/fotos y aviso explícito sobre el carrito.

Precio minorista en todo el flujo público; selecciones mayoristas antiguas se convierten con aviso y nueva revisión. Sin selector ni texto visible Minorista. La descripción identifica cada presentación también en el carrito/mensaje. Admin mantiene sus formularios nativos, seis unidades nuevas, incremento oculto fijo en 1 y alta repetida precargada. Unidad anterior conservada sólo al editar un registro previo. [Compatibilidad y actualización](CATALOGO_COMPACTO.md).

## Filas uniformes y header compacto — ajuste posterior del 17/10/2026

Cada fila adopta la altura del contenido más alto, conservando huecos blancos en cards más breves. Controles alineados abajo. Con 1 sólo papelera, con 2 o más sólo −; + siempre visible. El header retira el texto visible Carrito y reserva una columna compacta para icono/contador, con nombre y cantidad todavía accesibles. Verificado en móvil/tablet/escritorio y axe. Las imágenes ficticias de la carga local se identifican DEMO y no representan fotos de oferta comercial.

## Carrito y precio único — ajuste final del 17/10/2026

Controles de catálogo al pie derecho; carrito con el mismo patrón y menos márgenes/padding. Cantidad entera editable compacta, sin label visual; una sola papelera con 1, sólo − con más de 1 y + siempre disponible. Precio minorista sin etiqueta, sin marca, selector o condición mayorista en las fichas públicas. Subtotal/total y fotos ampliables permanecen. Avisos antiguos de cambio se mantienen visibles; no se ocultan errores al compactar.

## Alineación y personalización — 17/10/2026

Título, descripción y precio comparten inicio por fila; cada bloque reserva el máximo necesario sin truncar. Header sin Catálogo en el catálogo, sin Ver horarios visible y con desplegable conservado. Se quita el aviso de persistencia del carrito. Dos áreas de edición en Configuración comercial con campos explicados y vista previa de valores guardados. Errores no reemplazan lo guardado; cambios de texto con revisión abierta se muestran y requieren revisión nueva. [Guía](WHATSAPP_MESSAGES.md).

## Encabezado inspirado en referencia — 17/10/2026

Contenedor crema/blanco, bordes suaves y naranja existente, con búsqueda protagonista y categorías separadas debajo; sin subtítulo bajo la marca ni cuenta de usuario. El lugar de la acción de cuenta de la referencia contiene Horarios con estado Abierto/Cerrado y desplegable semanal. Ubicación abre dirección/enlace con pin SVG; el footer abre Google Maps directamente. Paneles sin mover el contenido, un único abierto con JS, cierre por control/exterior/Escape y retorno del foco. Sin JS conservan apertura nativa y el acceso desde URLs anteriores. Búsqueda/categorías preservan sus filtros GET y están disponibles desde el carrito. Estas reglas reemplazan todas las composiciones anteriores del header/página de ubicación.

## Ajuste del encabezado por mouse — 17/10/2026

Buscador de escritorio hasta 600 px, dejando más espacio para Ubicación/Horarios/carrito, con tipografía mayor, separación de 16 px y controles de 48 px. Categorías sólo texto. Flecha SVG siempre hacia abajo, sin rotación. Pin SVG en lugar del emoji rosado del enlace Maps.

En mouse, abrir al pasar el puntero y permitir llegar al contenido antes de cerrar (200 ms al salir). No mover foco por hover; mantener el contenido mientras se usa su enlace con teclado. Escape cierra y no reabre hasta una nueva entrada del puntero. Teclado y toque conservan apertura/cierre nativos, clic exterior y foco visible; sin JS mantiene details. Conservar responsive y todos los contenidos comerciales existentes.

## Carrito lateral y ajustes de encabezado — 17/10/2026

Carrito abre panel derecho de 500 px, alto completo y fondo suave difuminado; el catálogo conserva geometría, filtros y scroll. Productos en lista vertical desplazable y pie fijo con total/WhatsApp. Bajo 601 px: pantalla completa con volver sencillo; escritorio: cruz pequeña en control táctil de 44 px arriba a la izquierda. Cierre exterior/Escape, retorno al disparador y fondo inert. Review/foto conservan su propio Escape antes del cierre del panel. Vacío presenta total cero y Agregar productos abajo; cierra para seguir usando catálogo.

Buscador sin contorno al clicar/teclear tras un clic; Tab muestra foco en el formulario completo, sin la línea recortada sobre el input. No quitar la señal de teclado ni el fallback sin JS. Ubicación se centra bajo su summary con límites de pantalla; dirección centrada y pin vigente. Sin cambios de negocio ni datos.

## Centrado y lectura del carrito — 17/10/2026

Cards centradas en cada track, incluidos uno/dos/tres tracks con cards limitadas de ancho; conservar espacios vacíos y alineación de filas. Carrito aproximadamente 46% de escritorio, mínimo 520 px en tablet y completo hasta 600 px, sin cambios del catálogo debajo.

Avisos flotantes arriba de la pantalla y contenido alineado vertical/horizontalmente dentro; mensaje/Ver carrito/cierre en una línea cuando hay espacio. Ancho por contenido con límite 960 px; envolver al requerirlo en móvil o con nombres largos, sin truncar ni desbordar. Mantener foco y avisos live/temporizadores actuales. Footer Ubicación abre Maps directamente en otra pestaña; el header sigue desplegando dirección.

## Aclaración del aviso y estabilidad del carrito — 17/10/2026

Recuadro del aviso cerca del borde superior, no en el centro vertical de la pantalla. Texto/acción/cierre centrados y en una fila si caben. Estado Consultando sólo para lectores de pantalla, sin espacio visual antes/durante/después del recálculo. Paginación de 20: primeras páginas de cuatro filas de cinco o cinco filas de cuatro; nunca crear cards de relleno ni cambiar el tamaño para aparentar más resultados.

## Carrito sin avisos repetidos ni parpadeos — 17/10/2026

Catálogo: Se agregó {producto} al carrito. Ver carrito; cruces del tono de cada aviso, sin marco naranja, con hover suave y foco accesible. En carrito sólo errores/cambios relevantes/copiado; no éxitos por cada cantidad/eliminación. Sin Cargando carrito al abrir; fallo real ofrece respaldo.

Conservar visualmente fotos, títulos, fichas, cantidades en edición y scroll; actualizar cantidad/subtotal/total sin desmontar la lista ni ocultar todos los importes durante una consulta normal. Revisión deshabilitada hasta respuesta válida, errores siguen visibles. Lista larga con alturas naturales, sin comprimir tarjetas y con controles completamente dentro de su borde; pie fuera del scroll.

Copiar como icono de dos hojas a la derecha del label de mensaje, 44 px y nombre accesible. No total redundante sobre el campo ni párrafo explicativo retirado; total en el mensaje y advertencia comercial intactos.

## Zoom sin marco y revisión compacta — 17/10/2026

Sólo foto sobre fondo negro 85%, sin borde blanco añadido por el visor. Cruz blanca fina sin caja ni naranja, fuera del rectángulo de imagen y con objetivo 44 px, arriba derecha del viewport disponible. Mantener foto completa/proporcional sin estirar; Escape/clic exterior y foco de retorno. Diseño consistente entre catálogo/carrito.

Botón de revisión sin parpadeo al cambiar cantidades; bloqueo seguro de consulta conservado. Total como título. Vista previa sin región estática de advertencia: Volver / Enviar a WhatsApp, campo de diez líneas y copiar cerca del texto Mensaje que vas a preparar. Subtotal en mensaje; no quitar total ni datos obligatorios.

Cantidad mínima 1 confirmada. Negativo con No se pueden ingresar valores negativos; cero/fracciones con mensajes breves arriba. No duplicar recuadro dentro de la ficha, ni moverla para añadir error; aria-invalid/descripción accesible permanecen mientras se corrige. No redondear fracciones antiguas ni elegir otra cantidad automáticamente.


## Pesos y cantidades sin símbolos — 18/10/2026

Precios sin ,00 en todas las pantallas, Admin, CSV, PDF y texto de WhatsApp. Cantidad en una caja de al menos 44 px tanto en la card como en detalle. Teclado numérico móvil, edición y navegación normales; símbolos/letras/espacios y pegados mixtos rechazados por completo. El 0 y campo vacío se pueden escribir transitoriamente, pero no confirmar como cantidad válida: mínimo 1; basura con 1, − con más de 1 y + siempre disponible.

Errores y advertencias del carrito/revisión sólo en el aviso superior, con texto centrado y cruz semántica. Las referencias descriptivas accesibles permanecen fuera del flujo visual; ninguna ficha crece o añade recuadros al fallar. Un importe no válido bloquea revisión/WhatsApp; las cantidades históricas fraccionarias no se corrigen automáticamente.


## Texto del pedido — 18/10/2026

Título numerado/subtotal/total con negrita nativa de WhatsApp, marca opcional, cantidad natural por presentación y precio por unidad sin etiqueta de tarifa. Una línea en blanco entre artículos y un separador antes del total. Conservar saludo y nuevo cierre 📌. Descripciones no interpretables se muestran aparte para no perder contenido. Mismo texto en Admin, revisión, copia y apertura con emojis; ningún cambio de cards, controles o distribución del carrito.

## Pedidos: corrección del resultado y detalle — 18/10/2026

Éxito centrado en la ventana principal tras cerrar el carrito; dos párrafos exactos, dos acciones compactas iguales a la derecha y sin enlace adicional. Diálogo nativo con nombre/descripción, teclado y foco de retorno. Formulario con radios horizontales, dirección calle/número en grilla y ciudad debajo, sin campo adicional. CTA con SVG WhatsApp de 24 px y gap 9 px. Detalle en una sola card de 860 px, marca interna, productos compactos con subtotales a la derecha y total destacado; contenido largo fluye sin recorte. Validación a 320/390/768/1280 y axe.

# UX/UI mobile-first

## Objetivo
Catálogo veloz y sencillo, orientado primero a teléfonos móviles. Priorizar navegación, legibilidad de precios, selección de cantidades y revisión del carrito por encima de animaciones.

## Identidad
Tomar como referencia el logotipo provisto del comercio: naranja como color principal, con acentos suaves en fucsia, cyan y amarillo sobre fondos blancos o crema. Los colores del logo son referencias visuales, no se fijan códigos hex exactos hasta definir tokens desde el recurso original y comprobar contraste. Evitar fondos saturados y usar naranja en CTA, estado seleccionado y destacados.

## Vistas previstas
- `/`: buscador accesible, selector nativo de categorías con formulario GET en móvil y chips desde 800 px (espacio suficiente para controles y grilla). Búsqueda conservada sin JavaScript. Grilla de tarjetas adaptativas según espacio.
- `/carrito/`: artículos, cantidades, elección minorista/mayorista, subtotales, total estimado y Quitar individual. Restablecer sólo ante storage corrupto.
- Confirmación de salida: aviso sobre estimación de precios, stock sin confirmar y mayoristas sujetos a revisión; cancelar o continuar a WhatsApp.
- `/admin/`: Django Admin sin interfaz hecha a medida.

## Interacción
- Priorizar 360–430 px, luego tablet y desktop.
- Áreas táctiles de ~44×44 px o más; foco visible y formularios etiquetados.
- Cantidades editables con botones −/+ de 44×44 px; aritmética en centésimos y mínimo del producto. Placeholder discreto «Sin imagen» con espacio estable; sólo se muestran condiciones mayoristas específicas.
- Jerarquía visual: nombre, marca, foto, precio minorista, precio mayorista y condiciones.
- Mostrar unidades junto a precios y cantidades, evitando “$10.000” sin contexto.
- Preselección minorista. No insinuar que el sistema certifica el precio mayorista.
- CTA al carrito fácilmente accesible en móvil, considerando barra inferior pegajosa cuando no tape contenido o controles del sistema.
- Estados vacíos, imagen ausente, producto inactivo, precios actualizados y datos inválidos claramente informados.
- Evitar scroll horizontal, diálogos intrusivos repetidos y navegación innecesaria.
- Feedback flotante fijo superior: éxito verde con «Ver carrito» al agregar, errores rojos, advertencias ámbar e información neutra. Cinco/ocho segundos, cierre manual y pausa por hover/foco; errores que bloquean permanecen también junto al campo/producto. Un solo aviso live visible, sin duplicar anuncios. Confirmaciones administrativas nativas.
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

La fotografía abre un único dialog nativo del catálogo con mismo archivo optimizado, imagen contain, nombre accesible, cierre botón/Escape/fondo y devolución de foco. Sin foto se mantiene Sin imagen; sin JS el enlace abre el archivo. Condición mayorista específica con fondo rosa suave y texto oscuro, sólo en selección mayorista del carrito.

Notifications.show centraliza éxitos/info (5 s), errores/warnings (8 s), reemplazo, cierre y pausa por hover/foco. Componente fijo superior con safe-area, acción Ver carrito, sin alterar scroll/foco/layout. Sólo un aviso visible/live; el diálogo de revisión tiene una ubicación del mismo componente para mantenerlo operable dentro del modal. Explicaciones persistentes de campos/productos/red/almacenamiento permanecen sin anuncios live duplicados. Invalidar cantidad del carrito dispara la validación vigente y bloquea revisión/importes; Admin conserva sus mensajes nativos.

## Segunda iteración — apertura de WhatsApp

Continuar inicia una pestaña provisional desde el clic, sin destino WhatsApp hasta completar la última revalidación. Se anula opener y se fija no-referrer manteniendo el handle para cerrar. Ante precios/datos cambiados se cierra y exige revisión; ante cancelación/error se cierra sin salir. Tras validar se conserva el enlace target blank/noopener/noreferrer para apertura manual si el navegador bloquea o el usuario cierra el contexto nuevo. El carrito permanece en su pestaña, sin borrado ni envío automático. Referencia de comportamiento del navegador: https://html.spec.whatwg.org/multipage/nav-history-apis.html (noopener/noreferrer retornan null; por eso la pestaña provisional se desacopla antes de navegar y el enlace manual usa ambos atributos).

## Correcciones puntuales — composición vigente

Esta solicitud sustituye exclusivamente la disposición de header/footer/fotos/dirección indicada en la segunda iteración; los demás comportamientos anteriores se conservan como historial.

- Tarjetas: marco constante de 210 px con fondo neutro, enlace de altura definida en Flex y fotografía contain centrada. Nunca depender de una fila Grid automática que crezca con el tamaño intrínseco de la foto. Una única imagen optimizada, lazy/async y archivos originales intactos.
- Ampliación: sólo fotografía y × de cierre ≥44 px. Dialog tiene nombre genérico y descripción oculta; alt conserva identificación del producto para lectores. Sin encabezado, marca, descripción o texto comercial visible. Botón/Escape/exterior y retorno del foco; enlace nativo sin JS.
- Header: Grid en tres regiones desde 800 px (marca, horarios y navegación Catálogo/Carrito); columna centrada bajo 800 px con ambas acciones juntas y equilibradas. Logo de 64 px, aria-current y controles ≥44 px. Panel horario absoluto centrado en su control, limitado al viewport; seis separadores neutros entre días, sin separar intervalos. Horarios/colores/iconos/textos conservados.
- Ubicación: una región con h1 Ubicación, address/botón centrados desde Admin e iframe existente. Dos columnas 1:2 desde 800 px; una columna bajo ese ancho. Sin título introductorio ni subtítulos decorativos. Sin dirección, aviso claro sin enlace falso. URL/políticas del iframe intactas. URL principal /ubicacion/, redirección 301 desde /como-llegar/.
- Footer: enlaces/iconos, nombre y aviso centrados en todas las resoluciones; mismos destinos y área táctil.

Aceptación verificada en 360/390/430/768/1280 y límite de header 800 px, con capturas/mediciones reales y axe. No hay nuevas dependencias/modelos/migraciones.

## Nueva iteración — composición actual

Sustituye las indicaciones históricas de títulos y toolbar: Nuestros productos, Categoría móvil, Revisá tu carrito y Antes de abrir WhatsApp permanecen accesibles con visually-hidden, sin espacio visual reservado. El placeholder es «Buscar productos, marcas y más...». Catálogo de 12 por página con rango real «Mostrando 1–12 de 45 productos», filtros GET y navegación Anterior/Página/Siguiente; vacío coherente y controles ocultos si no hay más páginas.

El carrito comienza con los artículos; no hay Seguir viendo productos ni Vaciar. Fotos actuales de 56 px contain junto al nombre, Quitar a la derecha; sin foto no se reserva una columna ni se muestra placeholder. Usa el mismo dialog de catálogo, sólo imagen/×, con delegación para HTML recalculado. El título oculto de revisión sigue nombrando el diálogo y recibiendo foco; se retira sólo el párrafo redundante de texto largo. Aviso obligatorio, mensaje/copiar y apertura manual permanecen íntegros.

## Exportación PDF y ajustes puntuales

El header incorpora Ubicación como tercer enlace junto a Catálogo y Carrito. Los tres caben en una fila desde 320 px; marca/horarios/navegación siguen apilados bajo 800 px y alineados en escritorio. Se conserva el logo de 64 px y el desplegable existente.

Admin → Productos ofrece PDF con imágenes y PDF sin imágenes junto al CSV; las dos variantes A4 son listas blancas con texto completo, separadores finos, ARS, inactivos identificados y página/aviso comercial. Sin fotos el texto ocupa todo el ancho. Con fotos, encaje proporcional de aprox. 75 px al inicio del registro; imagen ausente/ilegible sólo muestra un aviso discreto.

Quitar se representa con una papelera SVG inline, naranja secundario, objetivo 44×44 px y aria-label «Quitar [nombre] del carrito». El icono decorativo se oculta a lectores; el producto retirado dispone de una etiqueta contextual accesible. Se conservan handler, almacenamiento y avisos existentes.

Los productos [DEMO] y sus marcas/precios son ficticios; se incorporan únicamente por el comando manual documentado en README, nunca durante navegación o arranque.

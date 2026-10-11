# UX/UI mobile-first

## Objetivo
Catálogo veloz y sencillo, orientado primero a teléfonos móviles. Priorizar navegación, legibilidad de precios, selección de cantidades y revisión del carrito por encima de animaciones.

## Identidad
Tomar como referencia el logotipo provisto del comercio: naranja como color principal, con acentos suaves en fucsia, cyan y amarillo sobre fondos blancos o crema. Los colores del logo son referencias visuales, no se fijan códigos hex exactos hasta definir tokens desde el recurso original y comprobar contraste. Evitar fondos saturados y usar naranja en CTA, estado seleccionado y destacados.

## Vistas previstas
- `/`: buscador accesible, selector nativo de categorías con formulario GET en móvil y chips desde 800 px (espacio suficiente para controles y grilla). Búsqueda conservada sin JavaScript. Grilla de tarjetas adaptativas según espacio.
- `/carrito/`: artículos, cantidades, elección minorista/mayorista, subtotales, total estimado, eliminar y vaciar.
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
- Feedback en flujo normal: éxito verde con «Ver carrito» al agregar, errores rojos, advertencias ámbar e información neutra. Roles de estado/alerta sin sustituir semántica de listas. Confirmaciones administrativas nativas.
- El recálculo conserva altura, controles, foco y scroll del carrito. Mientras se consulta se ocultan sólo importes y se bloquea revisión; ante fallo se mantienen controles y se permite reintentar.
- Horario en franja compacta debajo del header. Details/summary nativo con estado textual y punto verde/neutro, siete días y todos sus intervalos. «Según horarios publicados» visible; sin configuración no se deduce cierre. El desplegable funciona sin JavaScript; el estado en ese caso corresponde a la carga de página.

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

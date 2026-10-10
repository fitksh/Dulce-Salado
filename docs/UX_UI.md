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

## Rendimiento y accesibilidad
HTML semántico, etiquetas y textos alternativos, contraste WCAG AA cuando corresponda. Imágenes responsive, lazy loading de fotos fuera de pantalla y tamaños optimizados. No bloquear render con dependencias grandes. Navegación por teclado y uso con VoiceOver/TalkBack deben funcionar en los flujos principales.

## Criterio de aceptación UX
En móvil se puede encontrar un artículo, identificar ambos precios/condición, ajustar cantidad, revisar y abrir WhatsApp sin zoom forzado ni campos inaccesibles; nunca se confunde la estimación con una compra confirmada.

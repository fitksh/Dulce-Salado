# Especificación funcional — MVP

> Decisión vigente 18/10/2026: solicitudes persistidas, formulario de datos y limpieza posterior al guardado, según [PEDIDOS.md](PEDIDOS.md). Esta decisión reemplaza las referencias históricas a no persistir pedidos, conservar el carrito después de preparar y copiar/vista previa del mensaje. Continúan fuera de alcance pagos, stock, estados y cuentas de clientes.

## 1. Contexto
Catálogo público para Dulce y Salado, comercio pequeño con productos de repostería, dietética y cotillón vendidos por presentación (100 gr, kg, caja, pack, paquete o bolsa). Público principal: clientes que consultan precios y arman pedidos, especialmente desde celular. La comunicación y confirmación final ocurre por WhatsApp.

## 2. Objetivo
Reducir consultas manuales de precios y facilitar pedidos de productos y cantidades, sin crear un comercio electrónico transaccional.

## 3. Actores
- Visitante anónimo: busca, consulta precios, agrega artículos a un carrito local y abre WhatsApp con el texto precargado.
- Administrador del comercio: gestiona categorías y productos con Django Admin.

## 4. Alcance del MVP
- Catálogo público de productos activos, categorías activas, fotos, búsqueda por nombre, marca y descripción (prioridad en ese orden).
- Productos con nombre, categoría, marca opcional, descripción opcional, una imagen opcional, unidad de venta, incremento fijo de una presentación, precio minorista y mayorista cuando corresponda, observación de condiciones mayoristas, estado activo.
- Únicamente precio minorista vigente en catálogo, carrito y mensaje, sin etiqueta Minorista ni selector de tipo de precio. Mayorista y condiciones conservados en administración/exportaciones, sin aplicación pública.
- Cantidad editable respetando unidad/incremento; cálculo de subtotales y total estimado con aritmética decimal o unidades enteras, sin errores de coma flotante de dinero.
- Carrito persistido con `localStorage` en un navegador; no sincronizado entre dispositivos. Guardar como mínimo ID de producto, cantidad y tipo de precio. Ante cambios o desactivación del catálogo se recalcula o informa, sin mostrar precios antiguos como vigentes.
- Pantalla de revisión con totales estimados. Antes de abrir WhatsApp, advertencia explícita: precios estimados y disponibilidad pendiente de confirmación comercial.
- Enlace directo de WhatsApp a número configurado del negocio con texto URL-encoded. El usuario finalmente envía el mensaje en WhatsApp.
- Administración mediante Django Admin, sin panel administrativo propio.

## 5. Sin implementar en MVP
Autenticación de clientes, historial de clientes, estados de pedidos, stock, pagos, pagos a cuenta, logística de envíos, facturación, cupones, promociones complejas, umbrales mayoristas automáticos, múltiples fotografías, ratings, newsletter, notificaciones, chat embebido, API REST pública, WhatsApp Business API, PWA.

## 6. Entidades
**Category**: `name`, `slug`, `sort_order`, `is_active`.
**Product**: `category`, `name`, `brand` (opcional), `description` (opcional), `sale_unit`, `quantity_step`, `retail_price`, `wholesale_price` (opcional), `wholesale_condition` (opcional), `image` (opcional), `is_active`, `created_at`, `updated_at`.

Decisión vigente del 2026-10-18: altas con 100 gr, kg, caja, pack, paquete o bolsa. Incremento fijo en 1, cantidad entera positiva de presentaciones, incluso para kg/100 gr. Una ficha por presentación; la descripción distingue tamaños dentro de una misma unidad. Sin conversiones automáticas de gramos, precios ni fichas antiguas. Los productos anteriores con unidad conservan su etiqueta y se pueden editar, pero no crear nuevas altas con esa unidad. Las fracciones antiguas del carrito requieren corrección explícita y no se redondean. Precios por unidad de venta en ARS en pesos enteros, sin decimales, no negativos; mayorista opcional conservado en administración, CSV y PDF. No inventar un catálogo real ni precios.

## 7. Reglas de cálculo
- Ambos precios expresan el importe por unidad de venta definida para ese producto.
- Cantidad entera positiva. Los botones suman/restan una presentación, sin fracciones ni incrementos configurables.
- Subtotal = precio minorista vigente × cantidad. Total estimado = suma de subtotales.
- No aplicar impuestos, descuentos, cargos de envío ni conversiones de unidad no documentadas.
- No aplicar mayorista en el carrito. Las selecciones antiguas se normalizan a minorista con aviso y nueva revisión antes de continuar.
- Ante producto inactivo/eliminado o precio ausente: impedir envío silencioso de un importe incorrecto; exigir revisión del carrito.
- Carrito vacío: ofrecer Agregar productos; en el panel cierra y devuelve al catálogo, sin CTA de WhatsApp.

## 8. Mensaje WhatsApp (editable desde Administración)

BusinessSettings conserva formatos general y por producto, emojis y vista previa. Formato vigente del 18/10/2026: saludo original, nombre numerado en negrita de WhatsApp, marca opcional, cantidad/presentación en lenguaje natural, precio por unidad comercial sin etiqueta de tarifa y subtotal en negrita. Productos separados por una línea en blanco, un único separador antes del total en negrita. Cierre: «📌 Los precios y la disponibilidad de los productos se confirmarán al procesar el pedido.»

Cantidad entera positiva como en el carrito: 100 gr se expresa como porción/porciones de 100 g; kg conserva kg; caja/pack/paquete/bolsa usan singular/plural. No convertir cantidades ni multiplicar el contenido de cada envase. Product sólo tiene descripción libre: reconocer formas completas acotadas de peso/composición y conservar el resto como Presentación adicional. Nunca inferir contenido de nombre/marca ni descartar texto ambiguo.

General requiere {productos}/{total}; producto requiere {producto}/{precio}/{subtotal} más {cantidad_presentacion}, o los campos compatibles {cantidad}/{unidad}. Nuevos campos {unidad_precio}/{presentacion_adicional}; {numero}/{marca}/{descripcion} siguen disponibles. Reemplazo de campos permitidos, sin ejecución de código/HTML/expresiones. Precios/subtotales/total minoristas vigentes en pesos enteros, sin cambios comerciales. Formatos personalizados anteriores se preservan; 0009 sustituye únicamente defaults conocidos.

El mensaje guardado y el enlace directo api.whatsapp.com/send comparten el mismo texto UTF-8. La vista previa y copia del carrito fueron reemplazadas por el formulario de datos. Evitar wa.me por una corrupción de emojis reproducida en su redirección. Cambio de formato exige nueva revisión, independiente de la revisión de productos. Configuración ausente usa defaults sin crear registros. [Campos, compatibilidad y límites](WHATSAPP_MESSAGES.md).

## 9. Revisión del mensaje

El botón Enviar Pedido abre Completá tus datos: nombre obligatorio, retiro predeterminado o envío con calle, número y ciudad (Viedma editable). Cancelar conserva carrito. Enviar revalida catálogo y formato, persiste una única solicitud idempotente y sólo entonces vacía los artículos preparados. El resultado permite reenviar el mensaje guardado sin crear otro pedido. No existe textarea ni botón de copiar. [Decisión vigente y configuración](PEDIDOS.md).

## 10. Criterios de aceptación MVP
1. Visitante navega y busca sin cuenta y sólo ve productos/categorías activos.
2. Selecciona cantidades y reconoce precio/unidad. Basura con 1, − con más de 1 y + siempre disponible, a la derecha de cada ficha.
3. Cierra y reabre la pestaña; carrito permanece en el mismo navegador.
4. Los precios del carrito se recalculan desde productos vigentes y cambios se comunican.
5. Total/subtotales se calculan sin errores de precisión monetaria.
6. Antes de navegar a WhatsApp hay advertencia y posibilidad de cancelar.
7. El texto precargado contiene cantidades, unidades, precio unitario, subtotales y total estimado.
8. Admin modifica productos, imágenes y categorías mediante Django Admin.
9. Interfaz usable en móvil con teclado, lector de pantalla y controles táctiles.
10. Se persiste la solicitud con su instantánea, sin gestionar estados, pagos ni existencias.

## 11. Configuración comercial pendiente
El dueño debe configurar el número real de WhatsApp por entorno y cargar productos/precios reales en Admin. Denominación inicial: Dulce y Salado. El precio mayorista no se publica en el flujo de compra. Los subtotales multiplican precio entero por cantidad entera y el total suma esos subtotales sin redondeo, con formato ARS es-AR.

## 12. Mejoras complementarias autorizadas
Exportación CSV completa/filtrada desde Admin con permisos de ver/cambiar productos. BusinessSettings central único: dirección comercial y enlace exacto opcional de Google Maps, editables con permisos del modelo. El desplegable Ubicación muestra dirección y enlace con pin SVG; /ubicacion/ y /como-llegar/ redirigen 301 al catálogo con ese panel abierto. Sin dirección informa ausencia y no ofrece enlace ficticio. No se cargan datos comerciales automáticamente. Seed manual autorizado de 45 presentaciones sin prefijo [DEMO] en DEBUG, simulación por defecto y escritura/limpieza con --apply; conserva comerciales, ediciones manuales e identidades dudosas. Los demos no representan oferta real.

BusinessSettings incluye `hours_initialized` («publicar horario semanal»), falso por defecto. OpeningInterval contiene configuración, día lunes=0 a domingo=6, apertura y cierre. Se permiten varios intervalos por día sin superposición ni cruce de medianoche. Apertura incluida y cierre excluido. Día sin intervalos cerrado sólo si la semana se publica; borradores o ausencia de configuración muestran «Horarios no disponibles». Estado según horario publicado en America/Argentina/Buenos_Aires, con desplegable semanal. No hay feriados/excepciones ni reservas; el dueño administra los horarios reales.

## 13. Segunda iteración UX/UI autorizada
Se conservan reglas/modelos y datos comerciales. Horarios integrados en header con panel flotante; categorías móviles automáticas con fallback GET; limpieza de textos y ajustes responsive. El iframe y la página de ubicación se retiraron por la solicitud posterior del encabezado; se usa exclusivamente dirección/enlace de Admin en un desplegable. Imagen única ampliable en dialog; condiciones específicas destacadas suavemente, sin validación automática.

Avisos públicos transitorios flotantes con acción/cierre y pausa; errores que bloquean cantidades/disponibilidad/almacenamiento/revisión siguen visibles hasta corregir. No son notificaciones persistidas ni push. WhatsApp abre otro contexto sólo tras revisión y revalidación; provisional se cierra ante errores/cancelación/cambios y ofrece enlace validado manual si se bloquea. Se conserva pestaña/carrito, sin envío automático ni pedidos persistidos. No hay nuevos modelos/migraciones/dependencias.

## 14. Nuevas exportaciones e importación CSV autorizadas

Se añaden PDF tabla compacta y PDF tabla con imágenes a las listas/CSV existentes, sin cambiar sus resultados. Ambas A4 horizontales, conjunto completo del ChangeList/permisos actuales, sin categoría y sin truncar textos; Unicode/ARS/inactivos/DEMO/paginación. Sólo la tabla con fotos incluye miniatura completa proporcional de unos 51 px. Tarjetas públicas con marco 1:1 y cover centrado, recorte visual documentado; visor/carrito/PDF conservan foto completa sin modificar media.

Importación CSV administrativa sólo de altas, con add_product y CSRF, archivo analizado/vista previa sin escritura y confirmación explícita firmada/vigente. Categoría, nombre, unidad y precio minorista obligatorios; categoría existente no ambigua, sin creación automática. Unidad 100 gr/kg/caja/pack/paquete/bolsa; incremento vacío o 1, se rechaza cualquier otro valor, incluso en CSV antiguos. Textos opcionales vacíos, mayorista vacío None y activo vacío True; sin deducir mínimos ni condiciones. Decimal ARS sin miles/negativos/expresiones, todas las validaciones actuales y sin relación obligatoria entre precios.

Identidad normalizada por categoría/nombre/marca/unidad/descripción; duplicados inequívocos omitidos sin actualizar, ambigüedad/error bloquea lote. Revalidación al confirmar, alta atómica sin parciales, resumen creados/omitidos. Límites y formato canónico documentados en README; plantilla ficticia a reemplazar. Sin imports públicos, imágenes, historial, persistencia de archivos, sincronización o procesamiento asíncrono. Comerciales, demos/seed, configuración, horarios, carrito y WhatsApp conservados.

## 15. Catálogo compacto y presentaciones — 2026-10-17

Cards sin categoría, marca, selector de tarifa, label de cantidad ni botón Agregar. Conservan imagen, nombre/descripción cercanos y un único precio por presentación, sin etiqueta Minorista. Estado inicial sólo +; 1 muestra basura/1/+; más de 1 muestra −/cantidad/+. Cada + guarda una presentación directamente. En catálogo: aviso «Se agregó [nombre] al carrito.» con Ver carrito; eliminación «Producto eliminado». Dentro del carrito no aparecen avisos de agregado/eliminación. Cantidades conservadas al volver y sincronizadas entre pestañas. Catálogo, carrito y mensaje usan sólo minorista vigente; no hay selección de tarifa. Los datos mayoristas permanecen en administración/exportaciones.

Hasta cinco columnas, controles accesibles de 44 px, máximo de card 340 px (300 desde 700 px) y sin estirar un resultado único. Admin: Guardar y agregar otro precarga los datos guardados, incluida una copia independiente de imagen; no muestra Guardar y continuar editando. Descripción incluida en revisión/WhatsApp y huella de cambios para distinguir presentaciones iguales en nombre/unidad. Migración 0005 conserva todos los demás campos y no duplica productos automáticamente. [Actualización y compatibilidad](CATALOGO_COMPACTO.md).

## 16. Ajuste autorizado posterior — 2026-10-17

Las cards de una misma fila deben tener igual altura, determinada por su contenido más alto; se admite espacio vacío. Control izquierdo exclusivamente basura con cantidad 1 o − con cantidad mayor a 1; nunca ambos visibles. Header sólo icono del carrito y contador, conservando nombre accesible. Se autorizó reinicializar el catálogo local de esta PC con datos ficticios después de respaldo, conservando administrador/configuración/horarios; no cambiar la instalación Raspberry ni convertir esa operación puntual en un reset automático del producto.

## 17. Alineación y mensaje editable — 17/10/2026

Título, descripción y precio deben empezar a la misma altura en cada fila, compartiendo el máximo necesario sin cortar contenidos. Catálogo sólo aparece como botón cuando se está en otra página. Se retira Ver horarios sin cambiar el desplegable y se elimina el aviso de persistencia del carrito. Dos campos nuevos de BusinessSettings para formatos general/por producto, editables desde Admin, con migración aditiva 0006 y vista previa; datos existentes conservados.

## 18. Semillas con fotos y títulos repetidos — 17/10/2026

Carga ficticia local de 45 presentaciones con las nueve fotos provistas, sin [DEMO] en títulos: Dietética 12, Cotillón 3, Repostería 30. Productos alimenticios repetidos por 100 gr/kg/paquete/caja/pack/bolsa, con descripción/precio propios; cajas por caja/pack/paquete. Carrito y edición distinguen por PK, sin fusionar por título. Seeder idempotente con identidad categoría/título/unidad/descripción y manifiesto v2, manteniendo protecciones/DEBUG/simulación. Mapa de fotos opcional por título; originales intactos, copias independientes. Manifiesto anterior v1 conservado sin escrituras hasta revisión explícita. Reset puntual autorizado sólo local con respaldo/ensayo, conservando usuarios/configuración/horarios y sin reiniciar secuencias.

## 19. Encabezado con buscador y ubicación desplegable — 17/10/2026

Composición inspirada en la referencia aportada: marca sin «Repostería · Dietética · Cotillón», buscador central y acciones Ubicación, Horarios y carrito; navegación por categorías debajo. No hay cuenta de cliente. Buscador/categorías disponibles también desde el carrito y siempre dirigidos al catálogo. Catálogo como retorno sólo fuera del catálogo.

Se elimina la vista independiente de ubicación y el iframe. Details/summary nativo muestra dirección guardada y un enlace con pin SVG con nombre accesible, target blank/noopener/noreferrer hacia Google Maps; enlace exacto configurado o búsqueda codificada por dirección. Sin dirección, aviso sin enlace ficticio. Footer abre Google Maps directamente con dirección/enlace configurados; el header conserva el panel. Enlaces antiguos redirigen permanentemente al catálogo con ubicación abierta, también sin JS. Horarios conservan semana, reloj de Buenos Aires y datos existentes. No cambia catálogo, carrito, precios ni configuración persistida.

## 20. Espacio del encabezado y apertura por mouse — 17/10/2026

Buscador de escritorio limitado a 600 px, con acciones Ubicación/Horarios/carrito más grandes y separadas. Categorías sólo texto, sin íconos. Flechas SVG pequeñas siempre hacia abajo, sin girar ni cambiar al abrir. Pin de ubicación vectorial reconocible en el control y enlace Maps, reemplazando el emoji anterior.

En dispositivos con mouse y capacidad real de hover, Ubicación/Horarios abren al pasar el puntero, sin mover el foco; cerrar al salir con margen de 200 ms para alcanzar el panel. Conservar abierto mientras el foco esté en su contenido. Escape descarta el panel aunque el puntero siga sobre el control. Clic exterior y cambio de panel conservan cierre; clic de mouse sobre el control lo mantiene abierto. Teclado Enter/Espacio y toque siguen alternando el details nativo. Sin JS permanece esa apertura nativa. Sin cambios de modelos/datos/API/carrito ni migraciones.

## 21. Carrito superpuesto en iframe y foco del buscador — 17/10/2026

Click en carrito o Ver carrito abre iframe del mismo sitio en panel modal de 500 px a la derecha, sin navegar ni desplazar catálogo. Fondo difuminado/atenuado, scroll de productos y pie fijo con total/revisión WhatsApp. En ancho hasta 600 px ocupa toda la pantalla y muestra flecha de volver; escritorio tiene cruz arriba a la izquierda. Clic exterior/Escape también cierran y restauran foco/posición del catálogo. Vacío muestra total cero y Agregar productos en ese mismo pie para cerrar y permitir sumar.

Reutilizar carrito, cantidades enteras y precios del servidor, revisión/mensaje/copiar/validación WhatsApp existentes. Cerrar durante preparación cancela la pestaña provisional; WhatsApp no se envía automáticamente. /carrito/ permanece como acceso directo/fallback; ?panel=1 sirve sólo el carrito sin header/footer. Iframe permitido sólo desde el mismo origen. Sin nuevos datos/modelos/migraciones. El buscador no muestra contorno al clicar; navegación con Tab mantiene un foco visible en su conjunto. Ubicación centrada bajo el control, limitada al viewport.

## 22. Centrado, ancho de carrito y footer directo — 17/10/2026

Cards centradas dentro de sus columnas para equilibrar márgenes en grillas de una, dos y tres columnas, manteniendo máximo de ancho, altura/bloques alineados por fila y hasta cinco columnas. Estado vacío ocupa el ancho de la grilla.

Carrito lateral de aproximadamente 46% del viewport en escritorio, con mínimo de 520 px para lectura en tablet y pantalla completa hasta 600 px; reemplaza el ancho fijo de 500 px. Conserva lista con scroll/pie fijo, revisión, cantidades y cierre.

Avisos flotantes de éxito/error/información/advertencia en la parte superior del viewport donde se opera, con su contenido centrado vertical y horizontalmente dentro del recuadro. Texto, acción Ver carrito y cierre alineados al centro en una fila cuando caben; ancho flexible hasta 960 px y adaptación sin truncar en móvil/textos largos. No cambiar temporizadores, pausa, roles live, errores persistentes junto a campos ni mensajes nativos de Admin.

Footer Ubicación abre Google Maps directamente en otra pestaña con el enlace validado actual de BusinessSettings; ya no abre el desplegable. Sin dirección se muestra indisponibilidad sin enlace ficticio. Header y rutas antiguas conservan su panel. Sin cambios de datos, modelos, dependencias o migraciones.

## 23. Corrección de avisos y filas completas — 17/10/2026

La aclaración del usuario reemplaza la ubicación anterior del recuadro: avisos arriba con margen seguro, centrados horizontalmente; texto/acción/cierre centrados dentro. Ver carrito en la misma fila cuando cabe, con adaptación móvil y textos largos sin recortar.

No mostrar visualmente Consultando el catálogo vigente al sumar/restar: el estado de consulta queda accesible a lectores de pantalla y no reserva espacio. Conservar aria-busy, validación vigente, bloqueo de revisión durante consulta y errores/reintento. Durante recálculos mantener la última presentación verificada sin parpadeo; ocultar importes si la verificación falla.

Paginación fija de 20 presentaciones, reemplazando 12, para completar filas de cuatro y cinco columnas. Mantener orden estable, búsqueda/categoría, rangos y navegación GET sin JavaScript. Con 45 resultados: 20/20/5; a cinco columnas no quedan las filas artificiales de dos productos. La última página de otros conjuntos puede ser parcial según la cantidad real. No ocultar, duplicar ni estirar fichas para rellenar huecos.

## 24. Carrito silencioso y actualización parcial — 17/10/2026

Dentro de /carrito/ y su iframe, sumar/restar/eliminar no muestra avisos de éxito. Errores, cambios de catálogo y resultado de copiar continúan comunicándose. Catálogo usa «Se agregó {producto} al carrito.» y acción Ver carrito. Cruz sutil del mismo tono semántico del aviso, con fondo/borde transparentes y área accesible de 44 px, también en errores/advertencias/información.

Abrir carrito no presenta Cargando carrito ni un enlace de respaldo transitorio; cierre siempre disponible y enlace de respaldo sólo ante error de carga. El iframe se carga una vez al abrir, sin navegación al editar. Recalcular actualiza cantidad/subtotal/total y sólo contenido que cambió; conserva fotos, títulos, fichas intactas, foco y scroll. Datos del servidor siguen siendo autoridad y revisión bloqueada mientras se consulta. Ante fallo se ocultan importes hasta reintentar. Listas extensas no comprimen artículos ni superponen controles: altura natural y scroll propio, total en pie.

Vista previa: icono estándar de copiar a la derecha de Mensaje que vas a preparar, nombre accesible/tooltip y mismo copiado completo/fallback. Se retira el total redundante anterior al textarea y el párrafo WhatsApp abrirá con el texto preparado. Total dentro del mensaje y advertencia comercial se conservan. Sin cambios de datos/modelos/migraciones/endpoints/precios ni envío automático.

## 25. Zoom, revisión simple y validación — 17/10/2026

Visor de catálogo/carrito sin marco blanco ni caja alrededor de la cruz: imagen completa/proporcional, fondo oscuro al 85% y cruz SVG blanca fina, fuera de la foto, arriba a la derecha. Conservar área 44 px, foco visible, cierre por botón/Escape/fondo y retorno al disparador. Nunca ampliar sobre su tamaño natural ni modificar las fotografías.

Botón Revisar y preparar WhatsApp conserva el aspecto durante consultas normales; mantiene bloqueo transitorio y validación del servidor, sin parpadeo por opacidad. Total reemplaza Total estimado en el carrito. Retirar región estática de advertencia de revisión, mantener avisos de cambios reales/errores. Acciones Volver y Enviar a WhatsApp. Textarea pasa de ocho a diez líneas; copiar queda junto al label, con gap pequeño y área accesible.

Mensaje por producto: Subtotal en lugar de Subtotal estimado. Migración 0007 actualiza default y sólo esa frase en formatos guardados, preservando todo el texto personalizado restante y demás datos. Respaldo previo de configuración; reversa no reescribe textos para no deshacer ediciones posteriores.

Mínimo 1 confirmado por el usuario: 1/2/3..., sólo enteros positivos, máximo actual conservado. Negativos: No se pueden ingresar valores negativos. Cero y fracciones rechazados con mensajes breves; sin redondear, convertir unidades ni borrar datos antiguos. Errores de cantidad sólo en aviso superior, con aria-invalid y descripción accesible persistente sin recuadro visible en la ficha. Los demás errores y advertencias del pedido también se anuncian sólo arriba, con referencias accesibles fuera del flujo visual. API/revisión impiden continuar con cantidades inválidas; serial/storage y cálculos Decimal conservados.


## Pesos enteros y edición de cantidades — 18/10/2026

Precios minorista/mayorista no negativos en pesos enteros, sin centavos al mostrar, cargar, exportar o calcular. Decisión explícita: descartar centavos existentes sin redondear ($100,99 → $100), incluida la base local; preservar identidad, fotos, presentaciones, usuarios y configuración. Migración 0008 con respaldo previo; no inventar los centavos al revertir.

Cantidad mínima 1 y máxima 9999999, caja editable en catálogo y carrito. Sólo dígitos ASCII 0–9: bloquear puntos, comas, signos, letras, espacios y pegados mixtos completos; nunca transformar 9,1 en 91. Las cantidades antiguas fraccionarias se mantienen en storage hasta corregir/eliminar y se presentan con campo vacío y aviso superior; no redondear. Enteros v1 con .00 siguen siendo compatibles. Todos los diagnósticos del pedido se anuncian arriba, sin recuadros o saltos dentro del detalle.

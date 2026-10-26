# Arquitectura y decisiones

> Decisión vigente 18/10/2026: solicitudes persistidas, formulario de datos y limpieza posterior al guardado, según [PEDIDOS.md](PEDIDOS.md). Esta decisión reemplaza las referencias históricas a no persistir pedidos, conservar el carrito después de preparar y copiar/vista previa del mensaje. Continúan fuera de alcance pagos, stock, estados y cuentas de clientes.

## Principio
Monolito Django renderizado en servidor. Mantener el número de servicios, abstracciones y dependencias al mínimo para un catálogo pequeño. Docker Compose local incluye `web` y `db`; Nginx, HTTPS, VPS y backups remotos se diseñarán cuando corresponda producción, no ahora.

## Componentes
- Django 5.2 LTS en Python 3.12: templates, rutas, validación, ORM, Django Admin.
- PostgreSQL: categorías, productos, usuarios administradores y precios. No fotos binarias ni carritos. Order conserva solicitudes mínimas con instantánea JSON, sin relaciones a productos borrables.
- JavaScript vanilla: selección, actualización de cantidades, persistencia `localStorage`, advertencia y enlace WhatsApp.
- CSS propio sin frameworks obligatorios.
- Media: un archivo de imagen local por producto, almacenado en `MEDIA_ROOT` dentro de volumen persistente Docker; DB guarda la ruta mediante `ImageField`. La optimización/validación WebP se hará en la fase de administración.
- Static: recursos versionados del sitio. Django puede servirlos durante desarrollo; despliegue pendiente.

## Entrega MVP
Catálogo con Category/Product, Django Admin, PostgreSQL, Docker Compose y CI con lint/check/migraciones/tests y QA de navegador. JavaScript vanilla sin dependencias de runtime. Pillow valida y convierte una imagen opcional por producto a WebP local.

## Flujo del carrito
1. Django sirve catálogo, búsqueda y tarjetas.
2. El frontend gestiona carrito en localStorage (IDs y cantidades; price_type=retail se conserva por compatibilidad v1).
3. Al mostrar, revisar o continuar, un POST protegido por CSRF a una vista Django devuelve HTML con datos vigentes y calcula importes con Decimal. No existe API REST pública. localStorage sólo guarda ID, cantidad, price_type compatible, unidad y hash de revisión; el hash comunica cambios sin guardar precios.
4. Usuario revisa y acepta advertencia en un diálogo nativo; se verifica nuevamente el catálogo. Si cambió, exige nueva revisión. Se genera URL `https://api.whatsapp.com/send?phone=<telefono>&text=<mensaje_codificado>` con el texto completo y teléfono de entorno. Sin teléfono se bloquea la salida.
5. Se persiste Order antes de abrir WhatsApp y vaciar artículos preparados. El usuario decide enviar desde WhatsApp. Consulta histórica sólo por token privado; no hay listado público ni estados. Ver [PEDIDOS.md](PEDIDOS.md).

## Seguridad básica
SECRET_KEY obligatoria desde variable de entorno; DEBUG desactivable; hosts permitidos explícitos; CSRF/sesiones estándar Django. Credenciales de PostgreSQL sólo en `.env` local ignorado. Django Admin requiere un usuario activo con `is_staff`; cada modelo requiere sus permisos correspondientes. Un superusuario activo tiene todos los permisos y es la opción inicial para el dueño. Upload de imágenes debe restringirse por tipo real, tamaño y dimensiones; sanitizar nombres y metadata. No habilitar uploads al público.

## Decisiones diferidas
VPS, dominio, proxy Nginx, TLS, logging centralizado, backup externo, despliegue automático y cloud storage. Se añadirán sólo cuando comience preparación de producción.

## Convenciones
Aplicación `core` para comprobaciones de la base. `catalog` concentra Category/Product, administración, catálogo y cálculos stateless del carrito/WhatsApp. No crear una app `orders` o `users` para clientes.

## Configuración comercial complementaria
BusinessSettings vive en catalog, con PK 1 y constraint para impedir registros múltiples. Admin no permite segunda alta ni borrado. Dirección/enlace Maps se leen sin servicios externos; la vista construye una búsqueda codificada cuando no hay enlace exacto. [Maps URLs oficial](https://developers.google.com/maps/documentation/urls/get-started) define el enlace universal con api=1 sin API key. Sin dirección no se muestra enlace. Exportación CSV utiliza biblioteca estándar y queryset de ChangeList sin paginar, con permisos Admin y protección de fórmulas en textos.

OpeningInterval se administra como inline en la misma configuración. Constraints de día/orden horario y validación de superposiciones en full_clean y formset (conjunto final, omitiendo borrados). Context processor precarga intervalos, calcula estado inicial en Buenos Aires y entrega json_script sin HTML sin escapar. JS compara el reloj local convertido a esa zona cada 15 segundos y al recuperar visibilidad; no consulta al servidor. No se agrega servicio/app ni datos comerciales en migraciones 0003/0004.

## Segunda iteración de interfaz
Sin cambios de modelos/cálculo/persistencia. catalog.js mejora el GET de categorías y reutiliza un dialog de foto; business-hours.js conserva sólo el reloj; header.js centraliza apertura/cierre de los paneles nativos. El posterior encabezado con ubicación desplegable retira directions.html y su iframe, usando dirección/enlace de BusinessSettings.

notifications.js expone Notifications.show: un aviso activo con timer y pausa, una plantilla en página y otra dentro del diálogo de revisión para evitar inert del modal; no se trasladan nodos. Sólo el host activo anuncia, con roles status/alert. Los errores persistentes de campos/filas/storage/red conservan texto y referencias accesibles sin live duplicado. Admin no participa.

Continuar abre about:blank directamente en el clic antes del fetch final. Se desacopla opener y agrega referrer no-referrer antes de navegación, conservando handle para cerrar si se cancela/falla/cambia carrito. Serial descarta respuestas obsoletas; retorno de visibilidad durante verificación no cancela el gesto. Tras respuesta vigente se reemplaza URL del contexto nuevo; la pestaña del carrito se conserva. Enlace validado target blank/noopener/noreferrer ofrece fallback manual. Según [HTML Standard](https://html.spec.whatwg.org/multipage/nav-history-apis.html), usar noopener/noreferrer directamente en window.open devuelve null; por eso se desacopla la provisional antes de navegar conservando el handle. Tests interceptan ambos contextos y comprueban opener/referrer y cierre, sin envíos reales.

## Correcciones visuales — encaje y estructura

Sólo cambian templates/CSS y la retirada del título visual en catalog.js. business-hours.html ahora forma parte de la grilla header-inner entre marca y carrito; relojes/modelos/Admin permanecen idénticos. El encaje Flex de miniaturas limita enlace e imagen al marco definido y evita crecimiento intrínseco de la fila Grid. La página directions.html de esa iteración se retiró posteriormente al integrar Ubicación en el encabezado. El resto del JavaScript y los endpoints, persistencia, seguridad y reglas comerciales no cambia.

## Nueva iteración UX/UI y datos de prueba

/ubicacion/ conserva el nombre de ruta directions como compatibilidad; ambos caminos antiguos usan RedirectView con 301 hacia /?ubicacion=1#ubicacion. Se retiró directions_page. Paginator usa 20 desde la corrección de filas de cinco columnas y mantiene orden name/pk, más search_rank cuando hay búsqueda. image_dialog.html se incluye una vez desde base; catalog.js delega clics, incluyendo miniaturas devueltas por cart_refresh. Carrito mantiene controles conectados/foco/scroll; URLs de fotos sólo provienen de Product, nunca localStorage. CartDataError identifica datos corruptos sin confundirlos con SecurityError; el restablecimiento explícito elimina sólo CartCore.STORAGE_KEY.

seed_demo_catalog pertenece a management/commands y lee 45 especificaciones JSON estáticas. DEBUG obligatorio incluso para simulación/limpieza; no hay hooks de ejecución. --apply confirma alta o --remove, categorías existentes únicas/activas se bloquean y resuelven antes de escribir, transacción protege todos los productos. No introduce campos ni migraciones. Manifiesto de procedencia en MEDIA_ROOT registra PK/created_at/fingerprint de datos y updated_at; la limpieza requiere identidad, estado intacto y nombre no ambiguo. Altas sin manifiesto o demos modificados se conservan. Archivo temporal fsync/replace evita escritura incompleta; base y archivo no forman una única transacción, por lo que una interrupción puede causar conservación de registros por identidad dudosa. README describe su uso y recuperación manual conservadora. Tests del comando usan base/media temporales; Chromium crea fixtures explícitos mediante Admin aislado sin invocar el seed como inicialización.

## Exportación PDF del Admin

ReportLab 5.x es la única nueva biblioteca de aplicación autorizada para PDF. Platypus resuelve párrafos Unicode, tablas sin decoración y paginación A4 en Python con Pillow existente. Se eligió frente a WeasyPrint porque no requiere Pango ni otro motor HTML/renderizado; tampoco navegador headless en producción. Sus fuentes Vera incluidas permiten acentos sin descargas. Referencias: [ReportLab/Platypus](https://docs.reportlab.com/reportlab/userguide/ch5_platypus/), [requisitos WeasyPrint](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html).

catalog/pdf.py recibe productos ordenados y un único parámetro include_images. Genera ambas variantes en BytesIO, devolviendo bytes para una descarga application/pdf; no escribe exportaciones en media, base ni rutas públicas. ProductAdmin comparte export_queryset con CSV: permisos view/change, GET y ChangeList.queryset completo, filtros/búsqueda/orden incluidos. Los tres botones conservan request.GET. No se excluyen inactivos ni [DEMO]; se muestra Estado: Inactivo cuando corresponde.

Fotos existentes se leen desde storage y se reducen sólo en memoria a 240 px, JPEG sobre blanco y encaje máximo 56 pt (aprox. 75 px). Foto ilegible/faltante conserva el producto con aviso discreto. Inline JPEG evita una colisión de la caché drawImage de ReportLab con píxeles idénticos y dimensiones distintas, detectada con fixtures horizontales/verticales uniformes. Sin imágenes hay una única columna de texto completa. Un registro normal permanece junto; uno mayor que la hoja se divide sin truncarlo. No se cambia el procesamiento comercial de uploads ni modelos/migraciones.

Poppler es herramienta exclusiva de QA/CI (lectura de texto, páginas e imágenes y renderizado); no es dependencia de runtime ni se añade al Dockerfile. tests/pdf_examples.py genera dos ejemplos en .qa/pdfs a partir de modelos sin guardar y media temporal: no consulta ni modifica la base comercial. .qa permanece ignorada.

La composición desktop del carrito se resuelve exclusivamente con CSS: padding lateral condicionado por :has(.cart-thumbnail) y miniatura absoluta de 132 px dentro del artículo. Todos los campos siguen en el mismo flujo de contenido a la derecha. Sin foto no se reserva espacio; HTML recalculado cambia la condición automáticamente. No se añade wrapper ni se altera renderCart: los controles permanecen conectados durante las actualizaciones. Bajo 800 px siguen las reglas móviles anteriores.

## Variantes tabulares PDF

build_catalog_table_pdf comparte fuentes, escape, marco/paginación y fotos con las listas, conservadas. A4 horizontal y Table con repeatRows=1, división entre filas y división interna sólo cuando la fila no cabe; columnas de 9 pt, sin categoría. La tabla con fotos utiliza máximo 38 pt, las listas conservan 56 pt por defecto. ProductAdmin añade dos rutas GET al mismo export_pdf, selector table e include_images; queryset/permisos y CSV intactos. Todo BytesIO, sin persistencia ni nuevas dependencias. Referencia de encabezados repetidos: [ReportLab Tables](https://docs.reportlab.com/reportlab/userguide/ch7_tables/).

## Importación CSV de altas

catalog/csv_import.py utiliza csv/Decimal estándar y full_clean del modelo. Categorías existentes y duplicados por identidad normalizada se resuelven sin escrituras en preview_rows. Se rechazan errores/ambigüedad en todo el lote, se omiten duplicados inequívocos y no se actualizan/borran productos. transaction.atomic y select_for_update sobre categorías en orden fijo serializan importaciones y revalidan antes de crear; si falla una fila, todo revierte. No introduce reglas de unicidad para las altas manuales del Admin.

ProductAdmin añade importar-csv (GET/POST) y plantilla-csv (GET), ambas admin_view y add_product obligatorio. Dos formularios simples: analizar archivo y confirmar explícitamente. signing.dumps/loads usa JSON, salt exclusivo, user_id, huella y registros originales, máximo 2 MiB y 15 minutos. El payload firmado viaja en campo oculto con escape de Django; no cifrado, no pickle, archivos permanentes, datos masivos en sesión ni historial. CSRF estándar en ambos POST, permisos revalidados al confirmar. Modificación/vencimiento exige análisis nuevo; cambio de clasificación/categoría devuelve preview actualizada, incluyendo errores. La plantilla versionada sólo contiene ejemplos ficticios y una categoría a reemplazar, sin consultar ni modificar datos reales.

Límites 256 KiB/500 filas/4000 caracteres más los límites del modelo. Punto y coma canónico, coma identificada por los 10 encabezados exactos incluso entrecomillados. Decimal sólo números inequívocos, sin miles/expresiones/no finitos; HTML/fórmulas/control rechazados y contenido siempre escapado al mostrarse. Las fotos se cargan individualmente después. Referencias: [firma Django](https://docs.djangoproject.com/en/5.2/topics/signing/), [transacciones](https://docs.djangoproject.com/en/5.2/topics/db/transactions/) y [select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).

## Ajustes de presentación — 2026-10-11

Sólo CSS para visor/grilla/carrito: fit-content y dimensiones naturales limitadas por viewport, mínimo Grid 250 px y centrado absoluto con top 50%/translateY(-50%) desde 800. Sin wrappers, cambios de renderCart/localStorage ni nuevos handlers.

_page_frame resuelve img/logo.webp mediante finders de Django y ImageReader existente; encaje de 16 mm sin recorte, XObject compartido por documento y fallback textual si falta/está corrupto. No guarda archivos ni modifica el logo. _labelled compone sólo etiquetas de lista en bold usando _escaped_text para valores dinámicos; las tablas siguen con su implementación anterior.

_ImageListRow limita a la lista con fotografías una corrección de paginación: ReportLab acumula padding al dividir MIDDLE y puede no avanzar en filas enormes. split divide en TOP y restaura MIDDLE en cada fragmento visible, sin duplicar foto/texto; datos permanecen TOP. Regresión real de 300 repeticiones con y sin foto. Poppler XML en QA comprueba geometría, logo repetido y fuentes; los tests distinguen fotos inline del logo. Sin nuevas dependencias/modelos/migraciones ni cambios de Admin/CSV/Docker.

## Presentaciones y catálogo compacto — 2026-10-17 (regla actual)

Mismo monolito, sin modelos/servicios/dependencias adicionales. 0005 normaliza quantity_step a 1 y sustituye su constraint por igualdad; mantiene la columna Decimal para compatibilidad, no editable. Choices de altas: 100 gr/kg/caja/pack/paquete/bolsa. La DB permite unidad para conservar filas anteriores; full_clean/save y Admin impiden nuevas altas con unidad y permiten mantenerla únicamente en una fila que ya la tenía. Unidades/valores existentes no se convierten, ni se transforman automáticamente productos en variantes.

cart-core.changeProduct actualiza una cantidad entera, preserva orden y revisión previa, usando tarifa minorista; 1→borrar, >1→restar. cart.js relee storage antes del clic, escribe antes de reflejar éxito y sincroniza DOM en carga/storage/pageshow/visibilidad. localStorage v1 y endpoints POST HTML con CSRF siguen iguales. Django valida enteros incluso al recibir JSON directo y bloquea fracciones antiguas sin redondearlas. La revisión incluye descripción para exigir revisión al cambiar la presentación. Descripción visible en carrito y mensaje WhatsApp, con el mismo escape/neutralización del resto del texto.

CSV mantiene sus diez columnas: incremento vacío/1, otros valores rechazados. Identidad ahora categoría/nombre/marca/unidad/descripción, normalizada salvo unidad; distintas presentaciones pueden coexistir incluso con igual nombre y unidad. Bloqueos/revalidación/atomicidad y no actualización de existentes conservados.

ProductAdmin.response_add genera un token firmado corto, ligado a usuario/PK/updated_at y válido una hora. get_form carga la fuente intacta en initial tanto en GET como POST; cada envío crea otra ficha. No descripciones/precios en URL ni sesión masiva. Una FieldFile inicial se copia a ContentFile acotado y usa el procesamiento WebP existente, obteniendo ruta UUID independiente; quitar/reemplazar no elimina la imagen de origen. Token inválido, vencido, ajeno o fuente cambiada no precarga datos. Botón continuar editando oculto sólo para Product. Sin auto deploy ni cambios de infraestructura.

## Corrección de filas e iconos — ajuste posterior del 17/10/2026

Grid align-items:stretch fija altura por fila a su máximo natural; margin-top:auto del control alinea botones al pie. Sin alturas fijas, wrappers ni JavaScript de medición. Para HTML/SVG se usa toggleAttribute("hidden", ...): asignar la propiedad .hidden al SVG no la reflejaba y dejaba el tacho junto a −. El contador conserva productos diferentes y el texto de accesibilidad se oculta visualmente, sin estilos de badge sobre esos textos.

Las especificaciones del seed cubren las seis unidades y paso 1, manteniendo nombres y guardas/atomicidad/manifiesto del motor. Operación de reset sólo puntual local en .qa, fuera de Git: backup completo, restauración/ensayo en copia, transacción de productos/categorías y seed, comprobación de conservación de usuarios/configuración/horarios y repetición idempotente. Sin reset reusable nuevo, nuevos modelos/dependencias ni migración adicional; 0005 pendiente se aplicó localmente con respaldo.

## Carrito compacto y precio público — ajuste final del 17/10/2026

calculate_cart fuerza retail_price en el servidor y normaliza price_type a retail, admitiendo wholesale sólo como entrada v1 anterior. La conversión avisa y cart_whatsapp compara también price_type para exigir revisión aun con hash vigente. product_revision incluye marcador retail-only y omite campos mayoristas que ya no afectan importes públicos. Datos administrativos/CSV/PDF intactos; sin migraciones nuevas.

Cart conserva el input compacto para edición/corrección explícita de cantidades antiguas, con etiqueta sólo accesible y botones derechos. Un único decremento alterna SVG/span por atributo hidden: basura con 1 y − con más de 1; cantidades inválidas o unidad cambiada permiten quitar la fila. Handler único en cart.js, escritura antes de éxito, borrador enfocado conservado, comparación numérica de cantidades equivalentes y foco de controles conectado durante respuestas. Sin dependencias nuevas.

## Alineación y formatos WhatsApp — 17/10/2026

CSS subgrid de seis tracks por card y subgrid de contenido alinea título/descripcion/precio/controles por fila, manteniendo el fallback flex sin medir DOM en JS. Header contextual por resolver_match, horarios con nombre accesible y recuadro del carrito retirado.

BusinessSettings recibe dos TextField con valores iniciales en migración aditiva 0006. whatsapp_templates valida con string.Formatter campos exactos sin atributos, conversiones ni especificadores; renderiza una sola vez con valores sanitizados y omite sólo líneas totalmente opcionales. No evalúa lenguaje de plantillas ni código. ModelForm/Admin valida longitudes/campos, muestra ejemplo escapado del mismo generador y conserva permisos/CSRF/singleton. Formset horario añade nombres accesibles a sus campos/DELETE, sin cambiar validaciones.

message_configuration lee el singleton actual, aplica formatos iniciales ante ausencia o datos externos inválidos y obtiene hash de ambos textos normalizados. render_review compone una vez con esa configuración; HTML incluye message_revision y cart.js lo presenta al aceptar. cart_whatsapp compara revisión de mensaje y de productos, bloquea una salida con texto cambiado y devuelve el mensaje actualizado. Vista previa/copia/enlace usan ese mismo texto, sin estado de pedido ni envío. No cambios en carrito v1, aritmética Decimal, incrementos o política de precio minorista.

## Semillas por presentación y mapa de imágenes — 17/10/2026

demo_products.json incorpora metadatos de marca/descripción y 45 presentaciones sin prefijo, con títulos repetidos. seed_key serializa categoría normalizada, título, unidad y descripción; manifiesto v2 y colisiones por esa presentación, no por título aislado. Se preservan PK/created_at/fingerprint, huella de foto, archivos compartidos/ediciones y atomicidad/restauración de manifiesto. V1 aborta sin adoptar registros ni borrar archivo. Sin migración de modelos.

--image-map opcional mapea los nombres exactos a archivos o listas de archivos ya validados de --images-dir; una lista alterna vistas de forma reproducible entre presentaciones. Validación completa de mapa/fotos antes de escribir, sin rutas arbitrarias ni lecturas fuera del directorio. Sin mapa se conserva el reparto equilibrado existente. Copias WebP UUID independientes, originales sólo leídos. Operación destructiva puntual en .qa, sin añadir --reset al comando: DB/host/DEBUG y respaldos obligatorios, transacción de catálogo, IDs no reiniciados, conservación de usuarios/BusinessSettings/horarios y repetición idempotente verificadas; ensayo sobre restauración con media temporal antes de aplicar localmente.

## Encabezado y ubicación desplegable — 17/10/2026

base incluye header_search, catalog_navigation y location_panel; home conserva sólo el contenido de catálogo. El context processor incorpora categorías activas para navegar desde el carrito; formularios GET/enlaces apuntan explícitamente a home. CSS Grid cambia composición en 600/1050 px; navegación nativa móvil bajo 800 px. Los paneles absolutos se posicionan respecto de header-actions para permanecer dentro del viewport, sin desplazar contenido.

header.js mejora details/summary sin reemplazar su semántica: un solo panel abierto, clic exterior/Escape y retorno del foco; el enlace del footer tiene fallback GET ubicacion=1, que renderiza open. business-hours.js mantiene exclusivamente el reloj/estado. La dirección se escapa como texto y location_url reutiliza validación/encoding existentes. No iframe ni consultas externas al cargar, dependencias, modelos o migraciones adicionales. La vista/template de ubicación desaparecen; rutas anteriores siguen redirección permanente y el parámetro sólo afecta presentación.

La revisión del encabezado reprodujo además una carrera entre respuesta HTTP de carrito y evento storage de otra pestaña. serial protege peticiones ya reemplazadas dentro de la misma página; ahora refresh compara también selecciones guardadas contra submitted antes de renderizar/persistir. Si difieren, lee/recalcula el estado vigente. Así una respuesta vieja no restaura una eliminación aunque el evento storage todavía no haya llegado. Regresión controlada en Chromium, sin cambios de formato/modelos/API ni importes.

## Hover y espacio del encabezado — 17/10/2026

header.js condiciona pointerenter/pointerleave a pointerType mouse y matchMedia(hover:hover)/(pointer:fine), sin deducir interacción por ancho. Timer por panel de 200 ms permite cruzar el espacio y se cancela al regresar/abrir/Escape/activar por teclado. Un foco dentro del contenido conserva el panel abierto y evita reemplazarlo por un hover accidental en otro control. focusout cierra al salir cuando tampoco hay hover. Clic de mouse sobre summary conserva abierto; Enter/Espacio/toque usan alternancia nativa. Sin focus automático al abrir por mouse. No CSS hover alternativo que reabra un panel descartado con Escape.

site.css limita el buscador a 600 px desde 1050 px y aumenta texto/íconos/espaciado de las acciones (48 px de alto, huecos de 16 px, carrito mínimo 64 px). Se conservan las composiciones móviles anteriores. Se retiran íconos de categorías, emoji Maps y rotación; chevron/pin SVG del sistema existente. Sin dependencias, endpoints o datos nuevos.

## Carrito lateral con iframe — 17/10/2026

base incluye cart_drawer excepto en cart_page. cart-drawer.js mejora los enlaces al carrito con dialog.showModal, iframe lazy por asignación de src y backdrop filtrado. Compensa el ancho de scrollbar al bloquear el documento y restaura padding/foco al cerrar. El iframe se descarga al cerrar. Mensajes de cierre aceptados sólo con origin exacto y source del iframe actual. Cierre notifica sincrónicamente al documento de mismo origen para invalidar revisión y cerrar provisional antes de descargarlo; pagehide también protege la provisional.

cart_page selecciona cart_frame.html sólo con panel=1; el decorador de esa vista fija X-Frame-Options SAMEORIGIN. El resto del sitio conserva la política global. includes/cart_app.html comparte todo el contenedor y endpoints existentes. cart_refresh recibe panel=1 sólo para presentar el CTA vacío; no cambia precios/reglas. El frame carga los mismos módulos de carrito/copia/foto y cart-frame.js para Escape/cierre. Revisión/foto nativas dentro del frame tienen prioridad sobre Escape del panel.

CSS Flex da scroll sólo a la lista dentro del viewport del iframe y mantiene el summary en el pie sin altura fija ni cubrir productos. Vacío conserva ese pie. El guard de respuestas obsoletas/localStorage permanece; storage entre iframe/padre sincroniza catálogo/contador. Modal nativo aporta foco e inert; no se crean pedidos. /carrito/ sin parámetro conserva la vista independiente y enlaces sin JS permanecen operables.

header.js registra modalidad pointer/Tab sólo para enfocar el conjunto del buscador por teclado, conservando fallback :focus-visible sin JS; el input no muestra su contorno nativo al clicar. Posición horizontal de Ubicación calculada desde el centro del summary y limitada a 16 px del viewport, actualizada al abrir/resize, sin mover elementos en flujo.

## Centrado y footer directo — 17/10/2026

product-grid usa justify-items:center porque sus tracks fr eran mayores que el max-width de las cards; se mantiene auto-fill/subgrid y el estado vacío fuerza justify-self:stretch. No cambia orden/paginación ni hay medidas de cards en JS.

cart-drawer usa min(100%, max(520px, 46vw)) y conserva override de pantalla completa hasta 600 px. Avisos posicionados arriba con margen seguro y centrado horizontal mediante left:50%/translateX(-50%), ancho max-content limitado a 960 px/viewport y contenido flex-wrap centrado para acción inline cuando cabe. Mismos hosts de página/revisión/iframe, roles/timer y JS de notificaciones; errores persistentes no se trasladan.

base enlaza footer-location a business.location_url con target blank/noopener/noreferrer; sin dirección, span de indisponibilidad. Se elimina la delegación data-open-location de header.js. Header nativo y compatibilidad de URLs antiguas permanecen. Sin cambios de API/modelos/datos.

## Avisos superiores y paginación compatible con cinco columnas — 17/10/2026

Paginador del servidor con 20 filas, sin detección de viewport, peticiones extra ni tamaños de página diferentes entre JS/HTML. Es múltiplo de cuatro/cinco, respeta el orden vigente y evita el resto artificial de 12%5. No modifica consultas de filtros ni datos.

cart-loading usa visually-hidden con role=status y comienza vacío; refresh sigue actualizándolo para accesibilidad. Se eliminan las reglas min-height/márgenes del estado visible, también en iframe, por lo que añadir/quitar el texto no participa del flujo. Se conservan los guards de recálculo, revisión y errores. Avisos vuelven al borde superior, manteniendo flex/centrado de contenido y temporizadores.

## Actualización parcial y carrito extenso — 17/10/2026

renderCart conserva contenedor, filas por ID y controles. syncBlock compara atributos/HTML de encabezado, descripción, precio, subtotal y errores; sólo aplica cambios reales. Totales válidos y botón de revisión mantienen sus nodos, con actualización del importe/disabled; transiciones de disponibilidad/vacío mantienen fallback de contenido completo. Controles reflejan atributos sólo si cambian, incluyendo QuantityControls.resize. Scroll interno se conserva además del documento. No hay nuevo framework ni endpoints por producto.

refresh conserva la presentación verificada durante consulta con aria-busy y revisión deshabilitada, evitando ocultar todos los importes en cada clic. is-unverified se aplica ante fallo; serial/comparación de storage/CSRF/revalidación vigentes permanecen. Avisos de agregado/eliminación se limitan a catálogo. Mensaje nuevo por nombre, close SVG con color heredado del estado y sin borde naranja.

La lista dentro del frame usa Flex en columna con hijos sin shrink para impedir que las filas Grid auto se compriman en un alto limitado. Scroll/summary siguen en los contenedores existentes. Drawer no muestra estado de carga; aria-busy en iframe y fallback oculto hasta load inválido/error, conservando cierre.

cart_review elimina dos párrafos redundantes y coloca label/copy en flex, icono SVG con aria-label/title. Copiado, texto integral y revalidación de WhatsApp no cambian. Sin cambios de modelos, dependencias, configuración o datos.

## Visor transparente y errores de cantidad — 17/10/2026

image-dialog ocupa el viewport transparente, sin border/radius blanco, con imagen centrada dentro de límites naturales y reserva superior para la cruz de 44 px/SVG blanco fino. ::backdrop negro 85%; mismos listeners de catalog.js, native dialog y documento propio del catálogo/carrito/iframe. No se copia código de referencias ni se agregan dependencias.

Selector de aria-busy mantiene opacidad 1 del botón de revisión durante consulta, sin retirar disabled ni revalidación. Revisión sin aria-describedby a la región retirada, diez líneas de textarea, copiar junto al label y acciones nuevas. Total visible renombrado; cálculos/importe del mensaje no cambian.

calculate_cart clasifica quantity_error y visible_errors sin retirar el error del cómputo de valid/total. Plantilla conserva descripción accesible de cantidad en p visually-hidden; los demás errores siguen en bloque visible. cartMessages prioriza ese texto para el único aviso live superior. Input aria-invalid se conserva al sincronizar. JS/Core dan mensajes breves/negativo exacto; ninguna validación permite fracciones/cero/negativos ni corrige cantidades silenciosamente. Valores canónicos históricos 1.00 siguen equivalentes a entero 1.

0007 cambia el default del formato de producto y reemplaza sólo Subtotal estimado: por Subtotal: en registros que contienen esa frase, con comparación del valor anterior para no sobrescribir una edición concurrente. El resto de formatos/configuración/productos/usuarios/horarios no cambia. Reversa de datos noop deliberada; para volver al texto previo usar el respaldo de configuración, no revertir textos personalizados automáticamente.

Al recibir close en catalog.js, se respeta el foco que el navegador ya restauró o que el usuario movió a otro control. Sólo se usa el fallback si queda en body/dentro del diálogo cerrado. Evita que un cierre pendiente vuelva a enfocar la foto al usar enseguida otro botón.


## Importes enteros y filtro compartido — 18/10/2026

Product.retail_price/wholesale_price conservan DecimalField (12 dígitos), con decimal_places=0. 0008 trunca ambos campos con ROUND_DOWN antes de alterar numeric, conserva nulos y fechas/otros campos y usa el alias de la conexión; reversa de datos noop. save rechaza fracciones para impedir el redondeo implícito de numeric al guardar desde el modelo. Admin valida también el texto crudo; CSV acepta sólo dígitos. SQL/bulk fuera de los flujos de aplicación debe usar enteros: PostgreSQL puede redondear una fracción al convertir directamente a numeric(12,0).

ars compartido en HTML/PDF/WhatsApp usa pesos enteros con separadores de miles y descarte explícito de fracciones por compatibilidad. Carrito multiplica/suma Decimal exactos, sin cuantización centesimal. Seeder/plantilla/preview con precios enteros. Un manifiesto de seed anterior cuyo fingerprint cambie por la migración se conserva: no duplica ni sobrescribe fichas identificadas; --remove se niega a borrar una ficha cuyo fingerprint ya no coincide. No actualizar ownership silenciosamente.

digits-only.js compartido entre Admin, catálogo y ambos carritos intercepta beforeinput, teclado y pegado/drop completos, con fallback de input/IME al último texto válido. No modifica importes o cantidades en almacenamiento como efecto de filtrar caracteres. Text inputs con inputmode=numeric, pattern, maxlength, labels y caja existente. Validación de dominio del servidor intacta, incluso si se omite JS. Diagnósticos en HTML accesible fuera del flujo visual, con floating notice único arriba. Edición de catálogo preserva borrador/foco y confirma escritura antes de reflejar éxito; botones usan el borrador vigente.


## Pedido legible y Unicode — 18/10/2026

whatsapp_presentations.presentation_text deriva cantidad_presentacion/unidad_precio/presentacion_adicional sin persistir ni convertir. Gramática completa acotada, fallback explícito con texto original y sin inferir desde nombre. whatsapp.py centraliza el mensaje; Admin preview, textarea/copia y destino comparten formato/cálculos. Aliases nuevos conservan campos anteriores; validación exige producto/precio/subtotal/cantidad-unidad. Migración 0009 sólo sustituye defaults conocidos, sin pisar formatos propios. Endpoint directo api.whatsapp.com/send con quote UTF-8 estricto evita corrupción reproducida de wa.me. No es API Business, no hay pedidos persistidos ni cambios de carrito/UI/stock/precios.

## Resultado del pedido fuera del iframe

order-result.js controla el único diálogo global de base. cart-drawer.js recibe únicamente datos desde su iframe activo con origin/source exactos y valida destino; cart.js confirma limpieza y libera el popup antes de solicitar el cierre. El fragmento del servidor comunica los valores persistidos; no se recalcula el mensaje. 0011 retira una columna obsoleta sin reescribir instantáneas. Detalle independiente en card única conserva las cabeceras privadas. Ver PEDIDOS.md.

## Producción pública autorizada — 25/10/2026

La decisión de diferir producción queda reemplazada para la Raspberry por
Gunicorn (2 workers gthread/2 threads) detrás de Nginx, con static recolectado
en la imagen y media persistente sólo lectura en el proxy. El túnel existente
comparte únicamente su red con Nginx; DB y Gunicorn no publican puertos. Dos
entradas de Nginx separan HTTPS del túnel y lectura HTTP del catálogo LAN.
Nginx sanea los encabezados antes del opt-in de confianza en Django, cookies
Secure y CSRF de mismo dominio; toda respuesta dinámica lleva private/no-store.
No cambian modelos, reglas comerciales ni pedidos históricos. Configuración,
advertencias de deploy justificadas, pruebas y rollback en
[ACTUALIZAR_RASPBERRY_PORTAINER.md](ACTUALIZAR_RASPBERRY_PORTAINER.md).

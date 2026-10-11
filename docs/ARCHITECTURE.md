# Arquitectura y decisiones

## Principio
Monolito Django renderizado en servidor. Mantener el número de servicios, abstracciones y dependencias al mínimo para un catálogo pequeño. Docker Compose local incluye `web` y `db`; Nginx, HTTPS, VPS y backups remotos se diseñarán cuando corresponda producción, no ahora.

## Componentes
- Django 5.2 LTS en Python 3.12: templates, rutas, validación, ORM, Django Admin.
- PostgreSQL: categorías, productos, usuarios administradores y precios. No fotos binarias, carritos ni pedidos.
- JavaScript vanilla: selección, actualización de cantidades, persistencia `localStorage`, advertencia y enlace WhatsApp.
- CSS propio sin frameworks obligatorios.
- Media: un archivo de imagen local por producto, almacenado en `MEDIA_ROOT` dentro de volumen persistente Docker; DB guarda la ruta mediante `ImageField`. La optimización/validación WebP se hará en la fase de administración.
- Static: recursos versionados del sitio. Django puede servirlos durante desarrollo; despliegue pendiente.

## Entrega MVP
Catálogo con Category/Product, Django Admin, PostgreSQL, Docker Compose y CI con lint/check/migraciones/tests y QA de navegador. JavaScript vanilla sin dependencias de runtime. Pillow valida y convierte una imagen opcional por producto a WebP local.

## Flujo del carrito
1. Django sirve catálogo, búsqueda y tarjetas.
2. El frontend gestiona carrito en localStorage (IDs, cantidades, selección de tarifa).
3. Al mostrar, revisar o continuar, un POST protegido por CSRF a una vista Django devuelve HTML con datos vigentes y calcula importes con Decimal. No existe API REST pública. localStorage sólo guarda ID, cantidad, tarifa, unidad y hash de revisión; el hash comunica cambios sin guardar precios.
4. Usuario revisa y acepta advertencia en un diálogo nativo; se verifica nuevamente el catálogo. Si cambió, exige nueva revisión. Se genera URL `https://wa.me/<telefono>?text=<mensaje_codificado>` con el texto completo y teléfono de entorno. Sin teléfono se bloquea la salida.
5. El usuario decide enviar desde WhatsApp. Sin historial de pedidos.

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
Sin cambios de modelos/cálculo/persistencia. catalog.js mejora el GET de categorías y reutiliza un dialog de foto; business-hours.js añade cierre exterior/Escape al details dentro del header. Mapa iframe fijo en directions.html proporcionado por el dueño, sin API/scripts; dirección/enlace Admin siguen independientes y operables ante fallo del recurso.

notifications.js expone Notifications.show: un aviso activo con timer y pausa, una plantilla en página y otra dentro del diálogo de revisión para evitar inert del modal; no se trasladan nodos. Sólo el host activo anuncia, con roles status/alert. Los errores persistentes de campos/filas/storage/red conservan texto y referencias accesibles sin live duplicado. Admin no participa.

Continuar abre about:blank directamente en el clic antes del fetch final. Se desacopla opener y agrega referrer no-referrer antes de navegación, conservando handle para cerrar si se cancela/falla/cambia carrito. Serial descarta respuestas obsoletas; retorno de visibilidad durante verificación no cancela el gesto. Tras respuesta vigente se reemplaza URL del contexto nuevo; la pestaña del carrito se conserva. Enlace validado target blank/noopener/noreferrer ofrece fallback manual. Según [HTML Standard](https://html.spec.whatwg.org/multipage/nav-history-apis.html), usar noopener/noreferrer directamente en window.open devuelve null; por eso se desacopla la provisional antes de navegar conservando el handle. Tests interceptan ambos contextos y comprueban opener/referrer y cierre, sin envíos reales.

## Correcciones visuales — encaje y estructura

Sólo cambian templates/CSS y la retirada del título visual en catalog.js. business-hours.html ahora forma parte de la grilla header-inner entre marca y carrito; relojes/modelos/Admin permanecen idénticos. El encaje Flex de miniaturas limita enlace e imagen al marco definido y evita crecimiento intrínseco de la fila Grid. directions.html anida información e iframe en una sola sección semántica. El resto del JavaScript y los endpoints, persistencia, seguridad y reglas comerciales no cambia.

## Nueva iteración UX/UI y datos de prueba

/ubicacion/ conserva directions_page y el nombre de ruta directions; RedirectView deriva /como-llegar/ con 301. Paginator existente usa 12 y mantiene orden name/pk, más search_rank cuando hay búsqueda. image_dialog.html se incluye una vez desde base; catalog.js delega clics, incluyendo miniaturas devueltas por cart_refresh. Carrito mantiene controles conectados/foco/scroll; URLs de fotos sólo provienen de Product, nunca localStorage. CartDataError identifica datos corruptos sin confundirlos con SecurityError; el restablecimiento explícito elimina sólo CartCore.STORAGE_KEY.

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

# Dulce y Salado

Actualización del catálogo compacto (17/10/2026): **requiere migración 0005**. Sumar agrega directamente una presentación; alta repetida precargada y seis unidades. [Comportamiento, compatibilidad y pasos manuales de despliegue](docs/CATALOGO_COMPACTO.md). Las instrucciones históricas «sin migraciones» de iteraciones anteriores no aplican a este cambio.

Catálogo comercial mobile-first de repostería, dietética y cotillón. Catálogo público, carrito local y mensaje WhatsApp con precios estimados. El comercio confirma disponibilidad y condiciones; el sitio no registra pedidos ni gestiona stock, pagos o envíos.

**Estado:** MVP y mejoras UX/UI implementados, con cuatro variantes PDF, miniaturas cuadradas e importación CSV de altas con vista previa en Admin; verificación y commits en [EXECUTION_STATUS](docs/EXECUTION_STATUS.md). Cargar y revisar información comercial real mediante Django Admin.

## Inicio local en Windows (PowerShell)

Requisito: Docker Desktop iniciado con contenedores Linux. Ejecutar en este repositorio:

```powershell
git pull --ff-only origin main
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
docker compose build
```

Si `DJANGO_SECRET_KEY` está vacío, generar una clave con Docker:

```powershell
docker compose run --rm --no-deps web python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Copiar la clave en `DJANGO_SECRET_KEY` dentro de `.env` y configurar `POSTGRES_PASSWORD` antes del primer inicio de la base. Las claves locales ya existentes se conservan; cambiar la variable de contraseña no cambia la contraseña de una base ya creada. No versionar ni compartir `.env`.

Configurar `WHATSAPP_PHONE` con el número internacional real del comercio, sólo dígitos, sin `+`, espacios ni guiones. Vacío permite probar catálogo/carrito y copiar el mensaje, pero deshabilita abrir WhatsApp. Django rechaza claves vacías y teléfonos configurados con formato inválido.

```powershell
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Abrir [catálogo](http://localhost:8000/), [carrito](http://localhost:8000/carrito/) y [Admin](http://localhost:8000/admin/). Si cambia `.env`, ejecutar nuevamente `docker compose up -d` para recrear el servicio con la configuración nueva.

## Cargar los primeros productos

1. Ingresar al Admin con el superusuario.
2. En **Catálogo → Categorías**, crear nombre, identificador URL, orden y estado activo.
3. En **Productos**, elegir categoría y completar nombre, marca/descripción opcionales y unidad: 100 gr, kg, caja, pack, paquete o bolsa.
4. El incremento es siempre 1 y no se configura. Los precios son ARS por presentación, en pesos enteros, sin decimales. Crear una ficha por presentación y distinguir tamaños con la descripción. Guardar y agregar otro conserva datos/foto para modificar lo necesario.
5. Cargar precio minorista y mayorista opcional. Los datos mayoristas se conservan para administración y exportaciones; el catálogo/carrito/mensaje utilizan sólo el minorista vigente, sin etiqueta ni selector de tarifa.
6. Adjuntar una imagen opcional JPEG/PNG/WebP hasta 5 MB, 6000 px por lado y 16 MP. Se convierte a WebP de hasta 1200 px, corrige orientación y elimina metadatos. Guardar el producto activo.

Sólo se publican productos activos en categorías activas. Las categorías con productos se protegen contra borrado; se pueden desactivar. El Admin requiere un usuario activo `is_staff` y permisos del modelo; el superusuario tiene todos los permisos.

## Probar el carrito y WhatsApp

- Buscar por nombre, marca o descripción (prioridad en ese orden) y filtrar categorías. En móvil, el selector aplica el filtro automáticamente conservando búsqueda; sin JavaScript usar Filtrar. Tocar + agrega una presentación minorista; con una aparece basura y con más aparece −. Cada pulsación cambia de a 1. Tocar una foto para ampliarla; cerrar por botón, Escape o fondo.
- Agregar al carrito, cerrar/reabrir la pestaña y entrar a `/carrito/`. Modificar cantidades; con 1, la papelera quita el producto; con más de 1, − resta una presentación. + siempre disponible y controles a la derecha. Las fotos pequeñas también se amplían. Catálogo y Carrito permanecen accesibles en el header.
- Cambiar un precio en Admin y volver al carrito: debe mostrar el dato vigente e informar el cambio. Desactivar un producto o cambiar unidad exige corrección. Cambios sólo mayoristas no afectan el carrito público.
- Elegir **Revisar y preparar WhatsApp**, leer el aviso y comprobar el mensaje completo. **Volver al carrito** o Escape cancela; **Continuar a WhatsApp** revalida y abre otro contexto, conservando la pestaña del carrito. Si el navegador bloquea la apertura, usar **Abrir WhatsApp con el mensaje preparado**. Ante cambios/errores se cierra la pestaña provisional y se requiere revisión.
- El sitio no envía: el envío se hace desde WhatsApp. No se vacía automáticamente el carrito. Ante mensaje largo, copiar el texto completo desde la revisión.

El carrito guarda selecciones y referencias en `localStorage`, nunca importes como autoridad. Al abrir, revisar y continuar se calculan importes actuales en Django con Decimal en pesos enteros; el total suma subtotales exactos. Sin almacenamiento local o sin JavaScript, el carrito requiere habilitarlos; el catálogo sigue disponible.

Ante datos guardados corruptos aparece **Restablecer carrito**: requiere clic y elimina únicamente la clave propia, conservando otros datos del navegador. No se ofrece para almacenamiento bloqueado ni para un carrito válido. El catálogo muestra rangos de resultados y páginas de 12, con filtros conservados en los enlaces Anterior/Siguiente.

Los avisos flotantes aparecen arriba incluso con scroll, sin mover contenido ni foco. Éxitos/información duran cinco segundos; errores/advertencias ocho, con pausa por puntero/foco y cierre manual. Al agregar ofrecen Ver carrito. Los errores bloqueantes conservan la explicación junto al campo/producto hasta corregirlos.

## Verificaciones

```powershell
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web ruff check .
```

Con Node 24, los tests de almacenamiento/cantidades y horarios no requieren paquetes:

```powershell
node --test tests/cart.test.cjs tests/hours.test.cjs
```

QA de navegador opcional; Playwright/axe son herramientas de desarrollo aisladas y no forman parte del sitio:

```powershell
npm.cmd --prefix .qa install --no-save --no-package-lock playwright@1.64.0 @axe-core/playwright@4.13.0
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) '.qa/browsers'
node .qa/node_modules/playwright/cli.js install chromium
docker compose run -d --rm --name dulce-salado-qa --publish 127.0.0.1:8001:8001 web python tests/browser_server.py
node --test tests/browser.spec.cjs
docker stop dulce-salado-qa
```

El servidor QA crea una base/media descartables y un administrador sólo de test. Nunca carga fixtures en la base comercial. WhatsApp se intercepta sin salir a la red; se guardan capturas en `.qa/screenshots`. Al detener el servidor se elimina la base QA. CI ejecuta estas comprobaciones con PostgreSQL.

## Detener y conservar datos

```powershell
docker compose down
```

No usar `down -v` para conservar base e imágenes. Los volúmenes `postgres_data` y `media_data` persisten datos locales.

## Documentación y límites

- [AGENTS](AGENTS.md), [especificación](docs/PRODUCT_SPEC.md), [arquitectura](docs/ARCHITECTURE.md), [UX/UI](docs/UX_UI.md), [roadmap](docs/ROADMAP.md).
- [QA y validaciones manuales](docs/QA.md).
- Sólo desarrollo local en main. Servidor Django de desarrollo ligado a localhost; VPS, HTTPS, backups remotos y despliegue quedan fuera del MVP.
- Validación manual pendiente en teléfono real con TalkBack/VoiceOver y WhatsApp del comercio. Logo original provisto en `assets/brand/logo-dulce-salado.jpg`; WebP optimizado en `static/img/logo.webp` con Pillow existente (`scripts/optimize_logo.py`). Naranja principal conservado.

## Exportar catálogo desde Admin

En el listado de productos, «Exportar CSV» descarga todos los productos del conjunto actual, incluidas páginas no visibles. Conserva búsqueda y filtros por categoría, unidad y activo. Sin filtros incluye activos e inactivos. Requiere usuario staff con permiso de ver o cambiar productos. Archivo UTF-8 con BOM y separador `;`, importes con coma decimal para Excel es-AR. Los textos que podrían ejecutarse como fórmulas llevan un apóstrofo protector. La importación de altas tiene permiso independiente de agregar productos y no modifica esta exportación.

Junto al CSV están «PDF con imágenes» y «PDF sin imágenes». Ambas descargas A4 conservan exactamente el mismo conjunto completo y orden del Admin, también inactivos y [DEMO] si el filtro los incluye. El PDF indica los inactivos, precios ARS estimativos y confirmación comercial. La variante con fotos usa miniaturas proporcionales; la otra ocupa todo el ancho con texto. Fotos faltantes/ilegibles muestran un aviso sin interrumpir la descarga. No se almacenan PDFs ni se alteran imágenes comerciales. ReportLab 5.x es la única biblioteca nueva: reconstruir Docker para instalarla.

QA PDF: CI instala Poppler para leer/renderizar los archivos. En entornos sin `pdfinfo`, `pdftotext` y `pdfimages`, las pruebas de inspección se omiten explícitamente; instalar `poppler-utils` para ejecutarlas completas. En Docker puede instalarse temporalmente sólo para QA con `docker compose exec -u root web sh -c 'apt-get update && apt-get install -y --no-install-recommends poppler-utils'`. `docker compose exec web python tests/pdf_examples.py` genera cuatro ejemplos ficticios en `.qa/pdfs`, ignorada por Git, con modelos sin guardar y media temporal. No toca la base comercial. Para inspección: `pdftoppm -png -r 110 archivo.pdf prefijo` y revisar todas las páginas.

«PDF tabla compacta» añade una descarga A4 horizontal con producto, marca, descripción, unidad, $ Min., $ May. y Cond. mayorista. Sin categoría ni fotografías; filas de altura variable, encabezados repetidos, texto completo y las mismas reglas de permisos/filtros/orden. El script de QA también genera `catalogo-tabla-compacta.pdf`.

«PDF tabla con imágenes» conserva los encabezados completos Imagen, Producto, Marca, Descripción, Unidad de venta, Precio minorista, Precio mayorista y Condición mayorista. A4 horizontal, fotos de unos 51 px con proporción completa, sin categoría. Ambas tablas conservan columnas monetarias ARS y legibilidad de 9 pt; descripción excepcionalmente larga continúa sin truncarse. El script genera `catalogo-tabla-con-imagenes.pdf` además de la compacta y las dos listas existentes.

## Preparar e importar productos desde CSV

Admin → Productos → **Importar CSV** requiere permiso de **agregar productos**. Un usuario con permiso exclusivamente de lectura puede exportar, pero no importar. La carga también está en `/admin/catalog/product/importar-csv/`; no hay importación pública. Sólo se crean productos, sin actualizar/borrar existentes, importar fotos, crear categorías ni ejecutar el seed.

Descargar la plantilla desde esa pantalla o abrir [la plantilla versionada](docs/plantilla-productos.csv). Contiene únicamente ejemplos ficticios: reemplazar `CATEGORÍA EXISTENTE` por una categoría ya creada y retirar/reemplazar las filas `[EJEMPLO]` antes de preparar datos comerciales. La categoría ficticia impide que esos ejemplos se importen sin revisión. Guardar como `.csv`, UTF-8 con o sin BOM, **punto y coma** como formato canónico. Mantener las diez columnas en este orden exacto, aun cuando sus valores sean opcionales:

```csv
Categoría;Nombre;Marca;Descripción;Unidad de venta;Incremento de cantidad;Precio minorista;Precio mayorista;Condición mayorista;Activo
CATEGORÍA EXISTENTE;[EJEMPLO] Producto por kg;;;kg;;14500;;;
```

- Obligatorios: Categoría existente, Nombre, Unidad de venta y Precio minorista. Unidad: `100 gr`, `kg`, `caja`, `pack`, `paquete` o `bolsa`; no se deduce del nombre.
- Marca, Descripción y Condición mayorista vacías quedan como cadenas vacías; no escribir `null`. Precio mayorista vacío queda sin precio; no se inventan condiciones ni se exige que sea menor al minorista.
- Incremento vacío o `1`. Otro valor, incluso en archivos anteriores, se rechaza sin importar nada. Cantidades enteras de presentaciones para todas las unidades; no se convierten gramos ni precios.
- Precios ARS: sólo dígitos, por ejemplo `14500`, sin símbolo ni separadores de miles. Se usa Decimal; `1.234`, `1,234`, `1.234,56`, negativos, expresiones y notación científica se rechazan. Sin decimales (incluso `14500,00`/`14500.00` se rechazan); máximo 12 dígitos.
- Activo vacío → Sí. Se admiten `Sí`/`No`, `True`/`False` y `1`/`0`, sin distinguir mayúsculas/acentos. Se conserva la categoría existente aun si está inactiva; no se la reactiva y sus productos no aparecen públicamente mientras siga inactiva.
- Límites: 256 KiB por archivo, 500 filas de productos, 4.000 caracteres por descripción/campo y límites menores del modelo (nombre 180, marca 100, condición 300). Se permiten comillas, `;`, comas y saltos de línea dentro de campos correctamente entrecomillados. HTML, fórmulas y caracteres de control se rechazan; nunca se ejecuta contenido del CSV.

En **Excel**, abrir/importar como UTF-8, conservar encabezados y columnas, preparar una sola hoja y guardar una copia como **CSV UTF-8**. El separador depende de la configuración regional: preferir `;`; si Excel genera comas, también se admite cuando los encabezados exactos permiten identificarlo. En **Google Sheets**, usar Archivo → Descargar → Valores separados por comas (.csv), hoja actual; el importador acepta ese delimitador con los mismos encabezados. Verificar que los precios no tengan separadores de miles. No reemplazar globalmente comas por punto y coma: dañaría campos entrecomillados.

1. Seleccionar el CSV y pulsar **Analizar archivo**. Elegir el archivo no importa nada.
2. Revisar la vista previa: números de fila, datos efectivos (incluidos defaults), nuevos, duplicados y errores. El número corresponde a la línea física inicial del registro; una descripción multilínea puede hacer que el siguiente registro empiece varias líneas después.
3. Corregir todas las filas con errores en la planilla, exportar otra vez y analizar el archivo completo. Cualquier error bloquea todo el lote, aunque otras filas sean válidas.
4. Los duplicados por categoría/nombre/marca/unidad/descripción se omiten sin sobrescribir. La comparación ignora mayúsculas, acentos y espacios repetidos. Categorías o identidades existentes múltiples, y filas de la misma identidad con datos diferentes, requieren revisión y bloquean el lote.
5. Pulsar **Confirmar importación** sólo después de revisar los nuevos registros. La vista previa está firmada para el usuario, vence en 15 minutos y no guarda el archivo ni datos masivos en sesión. Si fue modificada/venció, volver a analizar. Si categorías o duplicados cambiaron, se revalida y puede pedirse confirmar una vista previa nueva; nunca se aplica la anterior silenciosamente.
6. El guardado es atómico: si una fila falla, no se crea ninguna. El mensaje final informa creados/omitidos y vuelve a la carga sin archivo retenido. Repetir un lote omite coincidencias; no actualiza precios ni productos. Cargar después las fotos individualmente desde Admin y revisar datos comerciales antes de publicar productos activos.

La confirmación permite hasta 2 MiB de payload firmado, por debajo del límite de POST de Django. Son lotes pequeños/medianos, sin historial, trabajos en segundo plano ni sincronización. Las importaciones se serializan mediante bloqueos de categorías PostgreSQL y revalidación; el modelo sigue permitiendo altas manuales homónimas, que deben revisarse comercialmente. Las fórmulas que la exportación protegió con apóstrofo tampoco se admiten al importar.

Referencias de formato: [CSV y separadores en Excel](https://support.microsoft.com/es-es/excel/get-started/import-or-export-text-txt-or-csv-files), [UTF-8 en Excel](https://support.microsoft.com/es-es/excel/opening-csv-utf-8-files-correctly-in-excel) y [descarga CSV en Google Sheets](https://www.skills.google/focuses/5828?locale=es&parent=catalog).

## Ubicación
En Admin → Catálogo → Configuración comercial, editar la dirección real y, opcionalmente, el enlace HTTPS compartido por Google Maps. Sin enlace exacto se busca la dirección configurada; sin dirección se muestra un aviso y no se ofrece un destino ficticio.

Ubicación es un desplegable del encabezado con la dirección y un enlace con pin SVG que abre Google Maps en otra pestaña. El footer abre el mismo control. Se retiraron la página independiente y el iframe: Maps sólo se abre al pulsar el enlace. `/ubicacion/` y `/como-llegar/` redirigen 301 a `/?ubicacion=1#ubicacion`, con el panel abierto incluso sin JavaScript. No cambia la configuración existente ni requiere migraciones nuevas; ver [Encabezado y ubicación](docs/ENCABEZADO_UBICACION.md).

## Horarios comerciales
En esa misma configuración, añadir intervalos indicando día, apertura y cierre (hora de Buenos Aires). Para un horario partido, añadir dos filas del mismo día. Se permiten más intervalos; deben terminar el mismo día y no superponerse. Tras completar la semana, activar «Publicar horario semanal» y guardar. Los días sin filas se mostrarán cerrados. Antes de publicar se verá «Horarios no disponibles», incluso si hay intervalos borrador. Una semana publicada sin filas significa todos los días cerrados.

El desplegable dentro del header muestra la semana en un panel flotante que no desplaza contenido; cierra por el control, clic exterior o Escape. El estado se basa en los horarios publicados, sin feriados/excepciones. Con JavaScript usa el reloj del dispositivo convertido a America/Argentina/Buenos_Aires y se actualiza cada 15 segundos sin peticiones. Sin JavaScript refleja el estado al cargar y conserva el desplegable nativo. Migración: `catalog.0004_opening_hours`; no crea dirección ni horarios ficticios. La segunda iteración no agrega migraciones ni dependencias.

## Actualizar una instalación existente

Con Docker Desktop iniciado, ejecutar en el repositorio:

```powershell
git pull --ff-only origin main
docker compose up --build -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py check
```

Conservar `.env` y los volúmenes existentes. Revisar `/`, `/carrito/`, los desplegables de Ubicación/Horarios y Admin; comprobar también la redirección de `/ubicacion/`. Configurar dirección/enlace exacto y horario semanal en Configuración comercial; WhatsApp sigue en `.env`. Los datos comerciales no se generan automáticamente. Ver [QA](docs/QA.md) para pruebas reales de teléfono, accesibilidad, Maps y CSV en Excel.

## Correcciones visuales puntuales

Las tarjetas usan ahora un marco cuadrado 1:1 y fotografía centrada con `object-fit: cover`: llena el área sin deformarla, pero recorta los extremos de fotos no cuadradas. Al abrir la imagen, el visor mantiene `contain` y muestra la fotografía completa; también se conserva contain en el carrito y los PDF. Conviene cargar fotos fuente cuadradas, bien centradas y con etiquetas lejos del borde. La ampliación sólo muestra imagen y ×; mantiene etiquetas accesibles, Escape, cierre exterior/foco y enlace sin JavaScript.

Encabezado en dos niveles: marca sin subtítulo, buscador y ubicación/horarios/carrito en la fila principal desde 1050 px; categorías debajo. De 600 a 1049 px el buscador ocupa una segunda fila, y bajo 600 px se apilan marca, buscador y acciones. Categorías con selector nativo bajo 800 px y enlaces desde ese ancho. Logo de 64 px, carrito sólo icono/contador y enlace Catálogo únicamente fuera del catálogo. Los paneles flotan sin mover el contenido, con cierre exterior/Escape y foco visible. El footer abre el mismo desplegable de ubicación.

## Productos ficticios para pruebas locales

Comando manual, permitido sólo con `DJANGO_DEBUG=1`. Requiere las categorías activas Dietética, Cotillón y Repostería ya creadas en Admin; tolera mayúsculas y acentos, pero rechaza nombres ambiguos o faltantes antes de escribir. No se ejecuta al iniciar Docker, migrar ni preparar fixtures de navegador. Los tests de comportamiento lo invocan expresamente en bases y media temporales.

```powershell
# Simulación por defecto: no escribe productos ni archivos.
docker compose exec web python manage.py seed_demo_catalog
# Crear 45 presentaciones sin prefijo: 12 Dietética, 3 Cotillón y 30 Repostería, sin fotos.
docker compose exec web python manage.py seed_demo_catalog --apply
# Simular limpieza; después aplicarla explícitamente.
docker compose exec web python manage.py seed_demo_catalog --remove
docker compose exec web python manage.py seed_demo_catalog --remove --apply
```

Son datos y precios ficticios en ARS, con títulos sin [DEMO] y marcas vinculadas a las fotos cuando corresponden. Repetir el alta no duplica ni sobrescribe productos, incluidas ediciones manuales de demos. Los precios/condiciones mayoristas permanecen en administración y exportaciones; el flujo público usa minorista. Buscar un título, por ejemplo `Baño de repostería blanco`, permite comparar sus seis presentaciones; la carga completa tiene 45 fichas en tres páginas, con 20 por página (20/20/5); productos comerciales existentes cuentan adicionalmente en el catálogo general.

### Crear demos con fotografías locales

`--images-dir` es opcional; sin él las altas siguen sin fotos. En la Raspberry Pi/Portainer, el montaje de entrada es `/mnt/datos/docker/dulce-salado/demo-images:/app/demo-images:ro`; `/app/media` conserva su volumen persistente. Las fotos se mantienen fuera del checkout/Git. No hace falta cambiar dependencias, modelos ni migraciones. El comando sigue requiriendo `DJANGO_DEBUG=1` y categorías existentes activas.

```sh
# Validar directorio/fotos y simular, sin escribir productos ni archivos.
docker compose exec -T web python manage.py seed_demo_catalog --images-dir /app/demo-images
# Confirmar las nuevas altas con copias independientes.
docker compose exec -T web python manage.py seed_demo_catalog --images-dir /app/demo-images --apply
```

Desde la consola de Portainer del contenedor web, ubicado en `/app`, ejecutar directamente `python manage.py seed_demo_catalog --images-dir /app/demo-images` y después el mismo comando con `--apply`.

Se leen sólo archivos inmediatos con extensión `.jpg`, `.jpeg`, `.png` o `.webp` (sin distinguir mayúsculas), validando también su formato real, tamaño, dimensiones y ausencia de animación. No hay búsqueda recursiva; otros archivos/subdirectorios se ignoran y los enlaces se rechazan. Un candidato corrupto/inválido, error de lectura o directorio sin fotos válidas aborta todo antes de las altas. Los originales sólo se leen.

Se ordenan los nombres y se usa una semilla interna fija para un reparto pseudoaleatorio reproducible con el mismo conjunto de archivos. Sobre 45 nuevas altas, cada fuente aparece la misma cantidad de veces o con diferencia máxima de una: nueve fotos producen cinco copias cada una. Con más de 45 fuentes se eligen 45 distintas. Cada copia pasa por el procesamiento existente, conserva orientación/transparencia, se limita a 1200 px y se guarda como WebP sin metadatos bajo un nombre UUID propio en media; la base nunca apunta al original.

Los demos existentes, incluso los que no tienen foto, no se actualizan. Para regenerarlos, revisar primero la limpieza controlada (`docker compose exec -T web python manage.py seed_demo_catalog --remove`) y aplicarla explícitamente con `--remove --apply`; después ejecutar el alta con `--images-dir ... --apply`. La limpieza no necesita el directorio de entrada y no admite combinar `--remove` con `--images-dir`. Si conserva un demo editado o de identidad dudosa, ese producto también se conserva durante la siguiente alta.

El manifiesto v2 distingue categoría, título, unidad y descripción y registra PK/fecha/huella, ruta de foto y huella de bytes. Un manifiesto v1 aborta sin modificar archivo ni productos y requiere revisión de la carga anterior; nunca se adopta propiedad por coincidencia de nombre. La limpieza sólo elimina copias de productos efectivamente borrados después del commit; conserva demos/fotos editados, compartidos, faltantes o sin procedencia comprobable. Errores de conversión, guardado o manifiesto revierten altas y retiran sus copias, incluidas escrituras parciales, restaurando el manifiesto anterior. Si el almacenamiento impide la limpieza/restauración, el error identifica los archivos que requieren revisión. Los originales nunca se mueven ni se borran.

La limpieza sólo borra altas propias intactas y sin duplicados de la misma presentación; títulos iguales con unidades distintas son independientes. `MEDIA_ROOT/.seed_demo_catalog.json`, dentro del volumen de media ignorado por Git, registra PK, fecha de creación y huella de datos. Conservá este manifiesto junto con la base: si falta, está corrupto o no corresponde a los registros, el comando conserva los productos o aborta. Los demos editados se conservan y deben revisarse manualmente en Admin. No usa el prefijo como permiso de borrado. Las escrituras de productos son transaccionales; el archivo se reemplaza atómicamente. Una interrupción entre archivo y commit puede dejar identidad dudosa, que se conserva por seguridad. No hay nuevos modelos, migraciones ni dependencias.

Capturas de QA en `.qa/screenshots`: `photo-*`, `expanded-*`, `catalog-viewport-*`, `hours-*`, `directions-*` y `footer-*`. Las capturas `live-*` corresponden al entorno comercial local inspeccionado sólo en lectura. Actualizar con los comandos de instalación existente anteriores; no hay migraciones nuevas.

## Probar exportación PDF y ajustes del carrito

1. Reconstruir con `docker compose up --build -d` y hacer Ctrl+F5. No hay migraciones nuevas por esta iteración. En este entorno Docker ya está actualizado.
2. Entrar a Admin → Catálogo → Productos. Aplicar búsqueda/categoría/unidad/activo y, si corresponde, orden por columnas. Pulsar «PDF con imágenes» y luego «PDF sin imágenes». Las descargas incluyen todas las páginas del conjunto filtrado, igual que CSV. Para excluir demos o inactivos, aplicar los filtros/búsqueda necesarios; no se ocultan automáticamente.
3. Abrir ambos PDFs y revisar nombres, acentos, ARS, imágenes completas, salto de páginas y vista previa de impresión A4. Una búsqueda sin resultados genera un PDF válido con el aviso de conjunto vacío. Fotos ilegibles no impiden descargar los otros datos. No son pedidos ni listas de stock.
4. En catálogo/carrito, probar Catálogo/Ubicación/Carrito a 320/360/390/430 y 800/1280 px. Agregar un producto con foto: en escritorio muestra 132 px y datos a la derecha; en móvil, 56 px junto al nombre. Sin foto no queda hueco. Abrir foto, cerrar con Escape, cambiar cantidades, comprobar total vigente y quitar un artículo por papelera/teclado.

Verificación de esa iteración: 88 Django, 7 Node y 25 Chromium, check/Ruff y control de migraciones correctos. Se inspeccionaron todas las páginas de los dos ejemplos PDF ficticios y capturas responsive, también con fotografía comercial sólo en lectura. Los ejemplos usan modelos sin guardar y media temporal. Pendientes manuales: visor/impresora propios, zoom real del navegador y teléfono/lector reales; no se ha realizado una impresión física ni enviado WhatsApp.

## Nuevas exportaciones e importación CSV — validación final

126 pruebas Django, 7 Node y 26 Chromium correctas; check/Ruff y control de migraciones correctos. Los cuatro PDFs se generaron y sus 19 páginas renderizadas se inspeccionaron completas. Capturas comerciales revisadas en 360/390/430/768/1280: marcos cuadrados sin deformación, placeholders uniformes y visor completo. Todos los registros/fotos comerciales conservan sus huellas iniciales; sólo se importaron fixtures en bases aisladas. Confirmaciones simultáneas crean una sola alta; paso importado 0.05 kg compatible con 0.25 kg en el carrito.

Para probar ahora: Ctrl+F5 y Admin → Productos → aplicar filtros/búsqueda/orden → **PDF tabla compacta** y **PDF tabla con imágenes**. Revisar conjunto completo respecto del CSV, A4 horizontal, ARS y fotos completas. Para la carga, seguir [Preparar e importar productos desde CSV](#preparar-e-importar-productos-desde-csv), descargar la plantilla ficticia, reemplazar categoría/productos y analizar antes de confirmar. No se modificaron los modelos, migraciones, reglas ni dependencias de esta iteración. Evidencia/commits/CI en [EXECUTION_STATUS](docs/EXECUTION_STATUS.md) y [QA](docs/QA.md).

## Probar los ajustes actuales de imágenes, catálogo, carrito y PDF

1. Con el entorno existente iniciado (`docker compose up -d`), hacer Ctrl+F5. Esta iteración no requiere dependencias ni migraciones nuevas.
2. Revisar el catálogo a 360/390/430, 768, 1000 y 1280 px: una, dos, tres y cuatro columnas según anchura; 20 productos por página y controles completos. Las imágenes y placeholders siguen cuadrados.
3. Abrir fotografías verticales, cuadradas y horizontales desde catálogo/carrito. El marco se ajusta a la proporción original con 10 px de padding, sin ampliar imágenes pequeñas. Probar también 844×300, Escape, botón de cierre y retorno del foco.
4. Desde 800 px, revisar que la foto de 132 px queda centrada en toda la tarjeta del carrito, incluidos nombres/condiciones extensos. Cambiar cantidades: subtotal vigente, foco y scroll estables. Bajo 800 px conserva la miniatura de 56 px y su composición móvil.
5. En Admin → Productos, aplicar filtros/orden y descargar las cuatro variantes PDF. Todas llevan logo completo de 16 mm y nombre a su derecha en cada página; las listas tienen etiquetas en negrita/valores normales y la fotografía centrada. Revisar textos extensos, ARS/acentos y vista previa A4. Las tablas mantienen sus columnas anteriores.

Validación actual: 130 Django, 7 Node y 26 Chromium completos, check/Ruff y migraciones correctos. Las 19 páginas de cuatro ejemplos ficticios se renderizaron e inspeccionaron; visor en seis viewports y tres proporciones, carrito y catálogo responsive revisados. Cinco anchuras del catálogo comercial y sus ocho fotos inspeccionadas sólo en lectura. Todos los registros y fotos conservan sus huellas iniciales; QA descartada. Zoom nativo, impresión física y teléfono/lector propios siguen como comprobaciones manuales. Evidencia y CI en los documentos de seguimiento.

## Copiar y preparar el mensaje de WhatsApp

El texto usa títulos numerados/subtotales/total con negrita de WhatsApp (un par de asteriscos), marca opcional, precio unitario y cantidades en líneas separadas, con divisores Unicode discretos. Los importes y el mensaje completo se generan en Django; vista previa, copiado y enlace directo de WhatsApp coinciden. Nombres y marcas se muestran en una línea y sustituyen sólo sus marcadores `*`, `_`, `~` y backtick por `∗`, `＿`, `∼` y `ˋ` para no romper el formato; los datos almacenados no se modifican.

Copiar usa Clipboard API cuando se encuentra disponible. Si falta (por ejemplo HTTP de una IP local/Tailscale), intenta `document.execCommand("copy")` síncronamente desde el clic y el mismo textarea; también lo intenta tras un rechazo moderno. Sólo confirma «Mensaje copiado.» con éxito del método. Si el navegador bloquea ambos, selecciona todo y avisa «Copiá el texto seleccionado para pegarlo en WhatsApp.». El fallback es obsoleto y depende del navegador; no garantiza compatibilidad absoluta ni modifica su seguridad. Referencia: [Clipboard API y eventos, W3C](https://www.w3.org/TR/clipboard-apis/).

Para actualizar la Raspberry Pi, ejecutar desde el checkout y el mismo proyecto/archivo Compose que utiliza la instalación existente:

```sh
git pull --ff-only origin main
docker compose up -d --build --no-deps web
docker compose ps
```

Se reconstruye/recrea sólo web, conservando PostgreSQL y sus volúmenes/montajes de media, incluidas las imágenes de demos. Mantener el mismo nombre de proyecto/stack y su configuración local. Con Portainer, actualizar el código/imagen y redeplegar el stack existente conservando sus volúmenes y montajes. No hay migraciones/dependencias nuevas por esta mejora. Después hacer Ctrl+F5, abrir un carrito con varios productos y probar copiar/pegar en HTTP local/Tailscale y en HTTPS; revisar saltos, títulos, importes y total. Continuar sólo prepara el mensaje en otra pestaña; el envío lo hace el cliente.

## Estado local de prueba — 17/10/2026

Catálogo de esta PC reinicializado por pedido expreso: 45 productos DEMO, 3 categorías, 45 imágenes ficticias, seis unidades y paso 1; migración 0005 aplicada. Administrador, configuración comercial y horarios conservados. Respaldo completo y ensayo previo registrados en [Catálogo compacto](docs/CATALOGO_COMPACTO.md#ajuste-de-filas-y-reinicialización-local-autorizada--17102026). Cards de igual altura por fila, basura/− excluyentes y header sólo icono/contador. Abrir http://localhost:8000/ y hacer Ctrl+F5. Operación exclusivamente local; no aplica un reset en Raspberry ni durante el arranque.

## Alineación de catálogo y mensaje editable — 17/10/2026

Las cards alinean título, descripción y precio por fila, reservando el espacio de los textos más altos. Catálogo sólo aparece como botón fuera del catálogo; los horarios conservan su desplegable sin Ver horarios y se retira el recuadro de persistencia del carrito.

Editar mensajes en **Admin → Configuración comercial → Mensaje de WhatsApp**: formato general, formato por producto y vista previa. Incluye emojis 🛍️/💰, viñetas y total monoespaciado iniciales. Los campos se completan con cantidades/precios reales; edición de etiquetas no cambia el cálculo minorista ni la regla de enteros. [Guía, campos, datos y actualización](docs/WHATSAPP_MESSAGES.md).

Migración 0006 aplicada en esta PC con respaldo previo; productos, imágenes, acceso y horarios conservados. Requiere migrate antes de servir código nuevo en otra instalación autorizada. No hubo despliegue en Raspberry.

## Nueva carga local con fotos y presentaciones — 17/10/2026

Catálogo de esta PC reemplazado por pedido expreso, con respaldo y ensayo restaurado previos: 45 fichas sin [DEMO], 45 copias WebP independientes obtenidas de las nueve fotos indicadas por el dueño y mismo título por presentación. Ejemplo: Baño de repostería blanco en 100 gr, kg, paquete de 500 gr, caja, pack y bolsa. Configuración comercial/WhatsApp, administrador y horarios conservados; IDs nuevos sin reasignar carritos anteriores. Precios/presentaciones de simulación.

`--image-map` permite elegir la foto correcta para cada título y alternar varias vistas del mismo producto. Es opcional, requiere `--images-dir` y no se combina con limpieza. [Guía de datos, mapa, respaldo y verificación](docs/DATOS_PRUEBA_FOTOS.md). Sin nuevo modelo/migración/dependencia ni despliegue Raspberry.

## Carrito lateral en iframe — 17/10/2026

El carrito del header/aviso abre panel derecho sobre el catálogo, sin cambiar página ni desplazarlo, con fondo difuminado y total/WhatsApp fijos abajo. Lista desplazable; pantalla completa móvil con volver. Cierre por cruz/exterior/Escape y Agregar productos cuando está vacío. Buscador sin contorno al clicar y Ubicación centrada. Revisión, copia, cantidades y cálculos actuales conservados; /carrito/ sigue disponible como respaldo. Sin migraciones ni cambios de datos; recargar con Ctrl+F5. [Archivos, seguridad y pasos de actualización](docs/CARRITO_LATERAL.md).

## Centrado y lectura — 17/10/2026

Cards centradas en sus columnas al reducir ancho; carrito lateral cerca del 46% de escritorio (mínimo 520 px, completo en móvil). Avisos flotantes arriba, con el contenido centrado dentro del recuadro, con Ver carrito junto al texto cuando cabe. Footer Ubicación abre Maps directamente en otra pestaña usando Configuración comercial. Sin migraciones ni cambio de datos: recargar con Ctrl+F5.

## Carrito silencioso y listas extensas — 17/10/2026

Dentro del carrito no aparecen éxitos por cantidad/eliminación ni aviso Cargando al abrir. Fotos/títulos/filas intactas y scroll se conservan; se actualizan cantidad/subtotal/total verificados. Listas largas mantienen altura natural y controles dentro de su borde. En catálogo: Se agregó {producto} al carrito. Ver carrito, con cruz acorde al aviso. Vista previa con icono de copiar junto al título, sin total/párrafo redundantes. Ctrl+F5; no requiere seed/reset ni migraciones nuevas. Archivos y actualización futura autorizada en [CARRITO_LATERAL.md](docs/CARRITO_LATERAL.md).

## Visor y revisión simplificados — 17/10/2026

Zoom sin marco, cruz blanca fuera de la foto y fondo más oscuro; botón de revisión sin parpadeo, Total, Volver/Enviar a WhatsApp, campo de diez líneas y copiar junto al label. Cantidades enteras desde 1: errores sólo arriba y aviso que desaparece al corregir. Migración 0007 renombra Subtotal estimado a Subtotal en el formato guardado sin sustituir personalizaciones; aplicada local con respaldo, sin modificar los 45 productos/usuarios/horarios. Ctrl+F5. Para una actualización futura autorizada, ver [CARRITO_LATERAL.md](docs/CARRITO_LATERAL.md); no reset ni seed.


## Pesos enteros — 18/10/2026

Precios/cálculos/CSV/PDF/WhatsApp sin centavos; cantidades en cajas sólo con dígitos, mínimo 1, y avisos del pedido sólo arriba. 0008 aplicada local con respaldo y ensayo de restauración: se descartaron centavos sin redondear en 6 de las 45 fichas, preservando fotos y demás datos. No reset ni seed. [Decisión, archivos, respaldo y pasos para otra instalación](docs/PRECIOS_ENTEROS.md). Ctrl+F5 en esta PC; no se modificó Raspberry.


## WhatsApp legible y emojis — 18/10/2026

Se evita una redirección de wa.me que reemplazaba emojis por � usando el enlace directo de WhatsApp con UTF-8. Cantidades como 3 porciones de 100 g o 4 packs de 3 paquetes de 500 g, marca opcional, precio por unidad y título/subtotal/total en negrita. Un separador y cierre 📌. Contenido ambiguo queda como Presentación adicional, sin inventarlo. 0009 aplicada local con respaldo sólo sobre defaults; personalizados y 45 productos/fotos/precios conservados. [Campos, formato, limitación de datos y actualización autorizada](docs/WHATSAPP_MESSAGES.md). Ctrl+F5.


## Actualizar la Raspberry desde Portainer con carpeta local

Para `/mnt/datos/docker/dulce-salado`, seguir [la guía de actualización](docs/ACTUALIZAR_RASPBERRY_PORTAINER.md): mismo proyecto Compose, respaldo PostgreSQL/media, reconstrucción local, migraciones y recreación de web desde Portainer. No se publican imágenes automáticamente con CI. La versión actual puede requerir 0005–0009; 0008 descarta centavos sin redondear. Conservar volúmenes y configuración existentes, sin seed/reset.

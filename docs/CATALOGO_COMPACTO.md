# Catálogo compacto y presentaciones — 17/10/2026

Implementado en el repositorio Django Dulce-Salado. ARCA DYS es otro repositorio de facturación; este cambio no añade integración entre ambos. La referencia https://tiendista.com/3B-mayoristas se revisó en el navegador para entender sus fichas por presentación y suma directa; se conserva la identidad visual, arquitectura y código propio de Dulce y Salado.

## Uso y decisiones

- Catálogo: cards sin categoría/marca/selector de tarifa/label de cantidad/botón Agregar; título y descripción cercanos. Sólo + al inicio; basura/1/+ al agregar; −/cantidad/+ a partir de dos. Agregado con nombre del producto; borrado «Producto eliminado».
- Sumar/restar guarda una presentación, siempre de a 1. Carrito persistente sincronizado en otras pestañas, recarga y regreso. Confirmar escritura antes de cambiar UI; errores persistentes y sin éxito falso. Objetivos táctiles 44×44 y foco de teclado conservado.
- Sólo precio minorista en catálogo/carrito/mensaje, sin etiqueta Minorista, selector ni condiciones mayoristas. Precios mayoristas conservados en Admin/CSV/PDF. Selecciones v1 antiguas se convierten con aviso; continuar exige nueva revisión incluso si la revisión del producto coincide. Precios vigentes se recalculan en Django al abrir/revisar/continuar, sin precios como autoridad en storage. WhatsApp sólo se prepara tras revisión, nunca se envía automáticamente.
- Seis unidades de altas: 100 gr, kg, caja, pack, paquete, bolsa. Cantidad 3 de «100 gr» significa tres presentaciones de 100 gr. No se convierte a 0,3 kg ni se deducen precios.
- Una ficha por presentación; la descripción distingue por ejemplo paquete 500 gr y paquete 1 kg. Se muestra también en carrito/WhatsApp y su cambio exige revisión. CSV distingue categoría/nombre/marca/unidad/descripción; no omite otra presentación como duplicado.
- Guardar y agregar otro abre una nueva ficha con datos previos, estado activo y copia independiente de foto; cambiar campos deseados. Guardar y continuar editando retirado del formulario de productos.
- Cada fila toma la altura de su card más alta, con controles alineados abajo a la derecha y espacio libre cuando corresponda. Contenedor 1360 px, máximo de cinco columnas, reducción progresiva y card máxima de 340 px (300 desde 700 px). Un resultado único no ocupa el ancho completo. Fotos/visor conservados; paginación de 20 para completar filas de cuatro y cinco columnas.

## Datos y compatibilidad

0005_product_presentations cambia **únicamente quantity_step a 1** en todas las filas, sin alterar updated_at ni IDs, nombres, descripciones, unidades, precios, imágenes, estados, categorías, configuración u horarios. Añade constraint de incremento exactamente 1. No duplica, elimina ni divide productos existentes. La prueba de migración compara todos los campos anteriores y posteriores excepto el incremento solicitado.

«unidad» anterior se conserva con su precio/significado en filas previas y se ofrece únicamente al editar esa ficha. Las altas usan las seis unidades nuevas. Elegir otra presentación es una decisión manual con revisión de precio. No existe una conversión segura de una unidad a bolsa/caja/paquete por simple nombre.

localStorage v1 sigue legible, con cantidades anteriores intactas. Fracciones, unidades cambiadas o información inválida bloquean revisión y salida a WhatsApp hasta corregirlas desde carrito o quitar el artículo; no se redondean ni se cambian importes silenciosamente. Valores antiguos enteros siguen válidos. Una revisión previa puede generar un aviso inicial por el nuevo hash con descripción.

CSV conserva diez encabezados para analizar archivos antiguos. Incremento vacío/1; cualquier otro valor requiere corregir/reanalizar. «unidad» no se admite para nuevas importaciones, tampoco por reimportar una exportación antigua: corregir conscientemente presentación/precio o retirar esas filas del lote, sin sobrescribir productos existentes. Mantener la descripción consistente para que se reconozca la misma presentación; modificarla representa otra ficha al importar.

Las futuras altas DEMO usan incrementos 1 y unidades permitidas. No se ejecutó el seed sobre datos comerciales. Una migración de incrementos puede hacer que un demo previo ya no coincida con su huella del manifiesto: la limpieza lo conservará para revisión manual, sin saltarse la protección.

## Archivos

Aplicación: catalog/models.py, migración catalog/migrations/0005_product_presentations.py, catalog/admin.py, catalog/cart.py, catalog/csv_import.py, catalog/whatsapp.py; templates/base.html, home.html, cart_contents.html e includes/quantity_control.html; static/js/cart-core.js, cart.js, quantity.js y static/css/site.css. Datos ficticios y plantilla: catalog/management/demo_products.json y docs/plantilla-productos.csv.

Pruebas: catalog/test_presentations.py; fixtures/regresiones en catalog/tests.py, test_cart.py, test_csv.py, test_csv_import.py, test_images.py, test_seed.py, test_views.py, test_whatsapp.py; tests/cart.test.cjs, browser.spec.cjs y browser_server.py. Documentación: README, PRODUCT_SPEC, ARCHITECTURE, UX_UI, ROADMAP, EXECUTION_STATUS, QA y esta guía.

## Actualización manual (no ejecutada en Raspberry)

Publicar primero el cambio revisado. Utilizar el checkout y el mismo proyecto/archivo Compose o stack de Portainer existentes, con sus montajes y volúmenes PostgreSQL/media. Respaldar base, media, .env y versión/imagen anterior; ensayar la restauración y migración sobre una copia aislada antes de actualizar. No crear otro stack vacío ni usar down --volumes. Los comandos siguientes son para el operador de esa instalación, con la configuración existente.

Respaldo de la base en el contenedor y copia al directorio privado de respaldos elegido:

```sh
mkdir -p .qa/backups
docker compose exec -T db sh -c 'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/dys-antes-presentaciones.dump'
docker compose cp db:/tmp/dys-antes-presentaciones.dump .qa/backups/dys-antes-presentaciones.dump
```

La carpeta .qa está ignorada por Git y no es pública; conservar además una copia del respaldo fuera del equipo. Respaldar también el volumen media, que incluye el manifiesto DEMO, y conservar .env en privado. Una vez verificado el ensayo en copia y decidido el mantenimiento:

```sh
git pull --ff-only origin main
docker compose build web
docker compose run --rm --no-deps web python manage.py migrate --plan
docker compose stop web
docker compose run --rm --no-deps web python manage.py migrate
docker compose up -d --no-deps web
docker compose exec -T web python manage.py check
docker compose ps
```

En Portainer, disponer del código/imagen nuevos, ejecutar migrate con esa imagen durante mantenimiento y recrear sólo web del mismo stack, conservando db/media/configuración. La migración normaliza incrementos; volver atrás en esquema no recupera sus valores anteriores y las unidades nuevas pueden impedir los constraints antiguos. Para retroceder utilizar respaldo y versión/imagen correspondiente, ensayados en copia.

Después: Ctrl+F5, catálogo móvil y 1440 px, búsqueda única, +/basura/−, controles compactos y precio público en carrito, regreso al catálogo, pestaña adicional y alta repetida. Revisar conscientemente las cantidades fraccionarias anteriores y presentaciones «unidad». No hay dependencias ni servicios nuevos. En la preparación inicial sólo se verificó la migración en bases descartables. En el ajuste local posterior expresamente autorizado, se respaldó y reinicializó el catálogo de esta PC, se aplicó 0005 y se cargaron 45 demos con imágenes. La Raspberry permanece sin acceso ni despliegue.

## Ajuste de filas y reinicialización local autorizada — 17/10/2026

Las cards de una misma fila se estiran hasta la mayor altura de esa fila, sin imponer una altura global ni recortar contenido. Los controles quedan al pie. El icono SVG se oculta mediante su atributo hidden: con 1 se ve sólo basura y con más de 1 sólo −, además del +. Header compacto: sólo icono de carrito y contador de productos diferentes; conserva nombre y número accesibles para lectores.

Se eliminaron los 52 productos y las 3 categorías del catálogo local de esta PC, después de guardar respaldos completos y ensayar su restauración/migración/carga en una base aparte. Se conservaron exactamente usuarios administradores, configuración y horarios. La carga final contiene 45 productos DEMO (15 por categoría), 45 copias de imágenes ficticias y las seis unidades con paso 1. No se reiniciaron secuencias de IDs: referencias de carritos anteriores no se reasignan a otro producto. Repetir el seeder se verificó sin cambios ni duplicados. El motor conservador de seed/limpieza no se relajó; sus especificaciones ahora cubren las seis unidades.

Respaldos privados en .qa/backups/20261017-reset-local/: database-before-apply.dump y media-before-apply.tar.gz son la copia inmediata anterior a la limpieza; checksums.json guarda SHA-256. database.dump y media.tar.gz corresponden al respaldo inicial, restaurado en el ensayo. rehearsal-result.json y reset-result.json documentan conteos, destino local y conservación de acceso/configuración. Todo ignorado por Git; ningún respaldo, foto ni operación destructiva puntual se incorporó al código versionado. La copia de ensayo y el servidor QA se retiran al terminar; permanece el servidor local habitual en http://localhost:8000/.

Pruebas posteriores: 39 Django afectados (seed/vistas), 40 Chromium completos, check/Ruff/migraciones/diff correctos. Verificación adicional del catálogo local en cinco anchos con axe y comprobación real de alturas, fotos y alternancia; capturas local-reset-1440, local-reset-390, local-reset-trash, local-reset-minus y local-reset-header inspeccionadas. Actualizar con Ctrl+F5. No se envió WhatsApp ni se tocó ARCA DYS o Raspberry.

## Carrito compacto y precio único — ajuste final del 17/10/2026

Catálogo con controles al pie derecho. Carrito conserva composición e imágenes, reduce espacios y utiliza basura/1/+ o −/cantidad/+ a la derecha; no hay papelera adicional. Campo entero compacto editable para cantidades/correcciones antiguas, con etiqueta accesible. Un único precio minorista sin texto Minorista, selector de tarifa, marca o condición mayorista; subtotal y total estimado permanecen. Mensaje WhatsApp usa el formato editable vigente descrito en [WHATSAPP_MESSAGES.md](WHATSAPP_MESSAGES.md) y el mismo importe actual del servidor.

Mayorista y condiciones permanecen en Product/Admin/CSV/PDF. Carritos anteriores siguen legibles; el servidor convierte selecciones mayoristas a retail con aviso y bloquea continuación directa hasta revisar, incluso con revisión vigente. Cambios sólo mayoristas ya no invalidan la huella pública. Esta iteración no requiere migración, limpieza, seed ni modificación de datos locales; los 45 demos existentes permanecen. Actualización en la PC: Ctrl+F5 en http://localhost:8000/ y /carrito/. Pasos remotos anteriores sólo para un futuro despliegue autorizado.

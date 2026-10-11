# Dulce y Salado

Catálogo comercial mobile-first de repostería, dietética y cotillón. Catálogo público, carrito local y mensaje WhatsApp con precios estimados. El comercio confirma disponibilidad y condiciones; el sitio no registra pedidos ni gestiona stock, pagos o envíos.

**Estado:** MVP, dos iteraciones UX/UI y correcciones visuales puntuales implementados; verificación y commits en [EXECUTION_STATUS](docs/EXECUTION_STATUS.md). Cargar y revisar información comercial real mediante Django Admin.

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
3. En **Productos**, elegir categoría y completar nombre, marca/descripción opcionales y unidad: kg, unidad o paquete.
4. Dejar incremento vacío para usar 0,1 kg o 1 unidad/paquete; o definir un incremento positivo (entero para unidad/paquete). Los precios son ARS por unidad de venta, con dos decimales.
5. Cargar precio minorista y mayorista opcional. Cuando exista mayorista, describir sus condiciones: el cliente lo elige manualmente y el comercio confirma su aplicación.
6. Adjuntar una imagen opcional JPEG/PNG/WebP hasta 5 MB, 6000 px por lado y 16 MP. Se convierte a WebP de hasta 1200 px, corrige orientación y elimina metadatos. Guardar el producto activo.

Sólo se publican productos activos en categorías activas. Las categorías con productos se protegen contra borrado; se pueden desactivar. El Admin requiere un usuario activo `is_staff` y permisos del modelo; el superusuario tiene todos los permisos.

## Probar el carrito y WhatsApp

- Buscar por nombre, marca o descripción (prioridad en ese orden) y filtrar categorías. En móvil, el selector aplica el filtro automáticamente conservando búsqueda; sin JavaScript usar Filtrar. Editar cantidad o usar −/+; minorista aparece por defecto. Tocar una foto para ampliarla; cerrar por botón, Escape o fondo.
- Agregar al carrito, cerrar/reabrir la pestaña y entrar a `/carrito/`. Modificar cantidades/tarifa, quitar productos y vaciar.
- Cambiar un precio en Admin y volver al carrito: debe mostrar el dato vigente e informar el cambio. Desactivar un producto, quitar mayorista o cambiar unidad: debe exigir corrección.
- Elegir **Revisar y preparar WhatsApp**, leer el aviso y comprobar el mensaje completo. **Volver al carrito** o Escape cancela; **Continuar a WhatsApp** revalida y abre otro contexto, conservando la pestaña del carrito. Si el navegador bloquea la apertura, usar **Abrir WhatsApp con el mensaje preparado**. Ante cambios/errores se cierra la pestaña provisional y se requiere revisión.
- El sitio no envía: el envío se hace desde WhatsApp. No se vacía automáticamente el carrito. Ante mensaje largo, copiar el texto completo desde la revisión.

El carrito guarda selecciones y referencias en `localStorage`, nunca importes como autoridad. Al abrir, revisar y continuar se calculan importes actuales en Django con Decimal y redondeo a dos decimales (mitad hacia arriba); el total suma subtotales redondeados. Sin almacenamiento local o sin JavaScript, el carrito requiere habilitarlos; el catálogo sigue disponible.

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

En el listado de productos, «Exportar CSV» descarga todos los productos del conjunto actual, incluidas páginas no visibles. Conserva búsqueda y filtros por categoría, unidad y activo. Sin filtros incluye activos e inactivos. Requiere usuario staff con permiso de ver o cambiar productos. Archivo UTF-8 con BOM y separador `;`, importes con coma decimal para Excel es-AR. Los textos que podrían ejecutarse como fórmulas llevan un apóstrofo protector. No existe importación.

## Ubicación
En Admin → Catálogo → Configuración comercial, crear una única configuración con la dirección real. El enlace exacto de Google Maps es opcional: pegar un enlace HTTPS compartido por Maps o dejarlo vacío para buscar la dirección. Luego editar ese mismo registro. La página pública `/ubicacion/` está enlazada desde el footer. Si falta dirección muestra un aviso sin destino ficticio. Migración nueva: `catalog.0003_business_settings`; ejecutar `docker compose exec web python manage.py migrate` al actualizar.

La segunda iteración incorpora además el iframe fijo de Google Maps provisto por el dueño, también en móvil. Está en `templates/directions.html` y deberá actualizarse si cambia la ubicación; editar dirección/enlace Admin no modifica esa URL. Si Maps no carga, la dirección y el botón siguen funcionando. Sin configuración editable se conserva el aviso; el iframe fijo del comercio permanece disponible. No requiere API key ni Google Maps JavaScript API.

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

Conservar `.env` y los volúmenes existentes. Revisar `/`, `/carrito/`, `/ubicacion/` y Admin. Configurar dirección/enlace exacto y horario semanal en Configuración comercial; WhatsApp sigue en `.env`. Los datos comerciales no se generan automáticamente. Ver [QA](docs/QA.md) para pruebas reales de teléfono, accesibilidad, Maps y CSV en Excel.

## Correcciones visuales puntuales

Las tarjetas muestran la fotografía completa en un marco neutro de 210 px, con proporción original y centrada. La ampliación sólo muestra imagen y ×; mantiene etiquetas accesibles, Escape, cierre exterior/foco y enlace sin JavaScript.

Header desde 800 px: marca, horarios y navegación Catálogo/Carrito en una fila. Bajo 800 px: tres regiones centradas, con ambos enlaces juntos. Logo de 64 px. El panel horario flota sin mover contenido. Ubicación integra información centrada, botón y mapa en una sola región: dos columnas desde 800 px y una por debajo. El footer queda centrado en todas las pantallas. `/como-llegar/` redirige permanentemente a `/ubicacion/`. La dirección completa, por ejemplo «Viedma, Río Grande 1814», se carga manualmente en Admin; no se agrega ni modifica automáticamente.

Capturas de QA en `.qa/screenshots`: `photo-*`, `expanded-*`, `catalog-viewport-*`, `hours-*`, `directions-*` y `footer-*`. Las capturas `live-*` corresponden al entorno comercial local inspeccionado sólo en lectura. Actualizar con los comandos de instalación existente anteriores; no hay migraciones nuevas.

# Dulce y Salado

Catálogo comercial mobile-first de repostería, dietética y cotillón. Catálogo público, carrito local y mensaje WhatsApp con precios estimados. El comercio confirma disponibilidad y condiciones; el sitio no registra pedidos ni gestiona stock, pagos o envíos.

**Estado:** MVP implementado; verificación y commits en [EXECUTION_STATUS](docs/EXECUTION_STATUS.md). La base inicial está vacía: cargar información comercial real mediante Django Admin.

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

- Buscar por nombre/marca y filtrar categorías. Elegir cantidad e incremento válido; minorista aparece por defecto.
- Agregar al carrito, cerrar/reabrir la pestaña y entrar a `/carrito/`. Modificar cantidades/tarifa, quitar productos y vaciar.
- Cambiar un precio en Admin y volver al carrito: debe mostrar el dato vigente e informar el cambio. Desactivar un producto, quitar mayorista o cambiar unidad: debe exigir corrección.
- Elegir **Revisar y preparar WhatsApp**, leer el aviso y comprobar el mensaje completo. **Volver al carrito** o Escape cancela; **Continuar a WhatsApp** revalida y abre el cliente con el texto preparado.
- El sitio no envía: el envío se hace desde WhatsApp. No se vacía automáticamente el carrito. Ante mensaje largo, copiar el texto completo desde la revisión.

El carrito guarda selecciones y referencias en `localStorage`, nunca importes como autoridad. Al abrir, revisar y continuar se calculan importes actuales en Django con Decimal y redondeo a dos decimales (mitad hacia arriba); el total suma subtotales redondeados. Sin almacenamiento local o sin JavaScript, el carrito requiere habilitarlos; el catálogo sigue disponible.

## Verificaciones

```powershell
docker compose exec web python manage.py check
docker compose exec web python manage.py test
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web ruff check .
```

Con Node 24, los tests del almacenamiento no requieren paquetes:

```powershell
node --test tests/*.test.cjs
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
- Validación manual pendiente en teléfono real con TalkBack/VoiceOver y WhatsApp del comercio. Los colores son provisionales hasta disponer del logo original.

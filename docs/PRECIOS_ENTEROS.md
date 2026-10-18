# Precios enteros y despliegue

El dueño confirmó descartar los centavos sin redondear: $100,99 pasa a $100. Aplica al precio minorista y mayorista existente; las altas/cambios futuros rechazan decimales. No hay limpieza/reseed en esta tarea. Los 45 productos y sus fotos deben conservarse.

Antes de aplicar 0008: detener escrituras administrativas, guardar un respaldo PostgreSQL completo en un lugar privado y comprobar su restauración en una base aparte. Con código y dependencias actuales, ejecutar `python manage.py migrate --noinput`, `python manage.py check` y reiniciar el servicio web. Comprobar precios, Admin/importación/exportación, catálogo, carrito y mensaje; un carrito con revisión vieja avisa del cambio y exige revisar. Recargar el navegador para traer los scripts actualizados.

Rollback de esquema no recupera centavos: conservar el dump y restaurarlo junto con el código anterior si es necesario; no restaurar encima de datos nuevos sin revisar. Ningún paso de esta tarea autoriza publicar o modificar Raspberry/ARCA DYS.

Los manifiestos de seed anteriores se mantienen conservadores: no sobrescribir ni duplicar fichas por el cambio de representación del precio. La limpieza automática sólo elimina si la huella coincide; después de esta migración puede preservar fichas por seguridad. Para nueva carga ficticia se usan precios enteros.


Aplicado en esta PC el 18/10/2026: respaldo/restauración de ensayo verificados en .qa/backups/20261018-integer-prices, migración 0008 aplicada, 45 fichas y fotos conservadas; 6 fichas perdieron sólo sus centavos. Verificación 194 Django, 9 Node y 81 Chromium, más ocho anchos locales/cuatro del panel, axe y capturas correctos. No hay pasos de migración pendientes en esta PC: recargar con Ctrl+F5.

Archivos principales: catalog/models.py, migrations/0008_integer_prices.py, cart.py, templatetags/catalog_format.py, admin.py, csv_import.py, whatsapp.py y management/demo_products.json; static/js/digits-only.js/quantity.js/cart.js, static/css/site.css y templates/home.html/cart_contents.html/cart_review.html/includes/quantity_control.html/base.html/cart_frame.html. Regresiones y documentación/plantilla CSV actualizadas.

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

## Entrega inicial
Esqueleto Django con página temporal, admin, PostgreSQL, health check sencillo, Docker Compose y CI con lint/check/tests. Sin modelos comerciales hasta la fase correspondiente.

## Flujo futuro
1. Django sirve catálogo, búsqueda y tarjetas.
2. El frontend gestiona carrito en localStorage (IDs, cantidades, selección de tarifa).
3. Al mostrar o enviar, consulta precios vigentes del catálogo; no utiliza precios locales como autoridad.
4. Usuario revisa y acepta advertencia; sitio genera URL `https://wa.me/<telefono>?text=<mensaje_codificado>`.
5. El usuario decide enviar desde WhatsApp. Sin historial de pedidos.

## Seguridad básica
SECRET_KEY obligatoria desde variable de entorno; DEBUG desactivable; hosts permitidos explícitos; CSRF/sesiones estándar Django. Credenciales de PostgreSQL sólo en `.env` local ignorado. Django Admin requiere un usuario activo con `is_staff`; cada modelo requiere sus permisos correspondientes. Un superusuario activo tiene todos los permisos y es la opción inicial para el dueño. Upload de imágenes debe restringirse por tipo real, tamaño y dimensiones; sanitizar nombres y metadata. No habilitar uploads al público.

## Decisiones diferidas
VPS, dominio, proxy Nginx, TLS, logging centralizado, backup externo, despliegue automático y cloud storage. Se añadirán sólo cuando comience preparación de producción.

## Convenciones
Aplicación `core` para página base y rutas generales. La futura app `catalog` concentrará Category/Product y administración. No crear una app `orders` o `users` para clientes.

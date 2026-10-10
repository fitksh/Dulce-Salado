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

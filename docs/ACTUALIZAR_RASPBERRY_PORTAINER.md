# Producción pública en Raspberry y Cloudflare — 25/10/2026

Esta sección describe la configuración vigente. El registro del 18/10 conservado
más abajo es histórico; sus referencias a `runserver`, DEBUG y sitio sólo LAN ya
no describen el despliegue público.

## Servicios y entradas

- Sitio y pedidos: **https://dulceysalado.ar/**. Administrador: **https://dulceysalado.ar/admin/**.
- Raspberry Pi 5 ARM64; checkout `/mnt/datos/docker/dulce-salado/source`, rama `main`.
- Stack Portainer existente `dulce-salado`, ID 20, endpoint 3. No sustituirlo por
  el `compose.yaml` de desarrollo: usar [deploy/portainer.production.yaml](../deploy/portainer.production.yaml)
  junto con las variables comerciales y secretos ya guardados en Portainer.
- `dulce_salado_web`: imagen local `dulce-salado:raspi`, Gunicorn, dos workers
  gthread con dos threads cada uno. Python 3.12/Linux ARM64; Gunicorn 26.2.0 fue
  comprobado en la imagen. Sin puerto publicado ni migraciones al arrancar.
- `dulce_salado_nginx`: imagen local `dulce-salado-nginx:raspi`, un worker Nginx,
  usuario sin privilegios, sistema de archivos de sólo lectura y temporales en
  `/tmp`. Es el único que publica **8003:8000**. Sirve static y fotografías.
- `dulce_salado_db`: PostgreSQL existente, saludable, sin recreación ni puerto
  público. Bind intacto `/mnt/datos/docker/dulce-salado/postgres`.
- Fotos intactas en `/mnt/datos/docker/dulce-salado/media`: web conserva su
  montaje de escritura para Admin; Nginx lo monta sólo lectura en `/srv/media`.
- El SSD real está montado en `/mnt/datos` (`/dev/sda`, ext4); `/mnt` por sí solo
  pertenece a la partición del sistema. No cambiar los binds existentes.

## Cloudflare y confianza del proxy

Se reutilizó el túnel **dulce-salado-rpi**, ID
`c40c7c01-5022-427e-bd66-5e10cd21bd43`, y su contenedor
`cloudflared_dulce_salado`, sin modificarlo ni reiniciarlo.
La ruta publicada es el dominio raíz `dulceysalado.ar`, sin subdominio ni path,
con servicio **`http://dulce_salado_nginx:8080`**. Cloudflare creó únicamente el
CNAME de este hostname hacia `<tunnel-id>.cfargotunnel.com`. No se creó Access,
no se publicaron otros servicios y no se abrieron puertos en el router.

Nginx se une a la red externa existente `cloudflared-dulce-salado_default` y a
la red del stack. La red del túnel observada es `172.23.0.0/16`: el listener
8080, sin publicación en el host, acepta sólo ese origen. Se comprobó el
servicio desde un contenedor de diagnóstico que compartió la red real de
cloudflared. No usar `localhost` como destino de otro contenedor.

Cloudflare [reemplaza X-Forwarded-Proto por el protocolo del visitante](https://developers.cloudflare.com/fundamentals/reference/http-headers/#x-forwarded-proto).
Nginx exige `https` en esa entrada o redirige 301 al dominio HTTPS y luego
envía un valor literal `https` a Django. En la entrada LAN 8000 siempre envía
`http`, ignorando encabezados aportados por el cliente. Limpia además
Forwarded/X-Forwarded-Host/Port/SSL; Django no confía en X-Forwarded-Host y
Gunicorn no agrega otra política de confianza de encabezados.

`SECURE_PROXY_SSL_HEADER` sólo se habilita con `DJANGO_TRUST_PROXY_HTTPS=1`.
Esto es seguro en esta topología porque Gunicorn no publica puertos y Nginx
controla el encabezado. Si cambia la red del túnel, verificar su CIDR y adaptar
Nginx antes de desplegar. No conectar contenedores no confiables a esa red.

## Variables de producción

Conservar en Portainer los valores originales de `DJANGO_SECRET_KEY`,
`POSTGRES_PASSWORD`, `WHATSAPP_PHONE` y cualquier variable comercial.
El stack utiliza:

```text
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=dulceysalado.ar,192.168.0.80,localhost,127.0.0.1
PUBLIC_BASE_URL=https://dulceysalado.ar
ORDER_ALLOW_LOCAL_URLS=0
DJANGO_SECURE_COOKIES=1
DJANGO_TRUST_PROXY_HTTPS=1
DJANGO_CSRF_TRUSTED_ORIGINS=https://dulceysalado.ar
```

Sesión y CSRF usan cookies Secure; se conservan HttpOnly/SameSite de Django.
El catálogo se puede leer por `http://192.168.0.80:8003/`. Admin redirige al
dominio público; realizar pedidos y autenticarse desde HTTPS, ya que los
navegadores no envían cookies Secure sobre HTTP de la LAN.

El Dockerfile ejecuta `collectstatic` durante la construcción con un valor
descartable sólo para ese paso; la imagen no incorpora la clave real y exige
su entorno al arrancar. El proxy copia los estáticos de esa misma imagen web.
Media permite sólo lectura de extensiones de imagen, sin índices, manifiestos
privados, archivos ocultos ni enlaces simbólicos. Django no sirve media en
producción. El Compose de desarrollo mantiene explícitamente `runserver`.

## Caché y comprobaciones de seguridad

Nginx fija `Cache-Control: private, no-store` en todas las respuestas dinámicas,
incluidos pedidos, errores y Admin. Los detalles conservan `noindex` y
`Referrer-Policy: no-referrer`; Cloudflare respondió DYNAMIC, sin Age ni HIT.
Sólo static/fotos tienen caché pública. No activar reglas Cache Everything
para HTML ni rutas de pedidos. Los access logs de Nginx/Gunicorn están
desactivados para no registrar los tokens privados de las URL.

`python manage.py check --deploy` devuelve sólo dos advertencias, sin silenciar:

- **security.W008**: `SECURE_SSL_REDIRECT=False` permite leer el catálogo LAN.
  La entrada pública de Nginx fuerza HTTPS. Se verificaron 301 por HTTP y 200
  por HTTPS, también enviando valores X-Forwarded-Proto falsos, sin bucles.
- **security.W004**: HSTS permanece en cero para no imponer una política
  persistente antes de evaluar todos los nombres/subdominios. HTTPS y cookies
  Secure ya funcionan; no se habilita includeSubDomains ni preload.

Referencias: [confianza del proxy en Django](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-proxy-ssl-header),
[Gunicorn](https://gunicorn.org/reference/settings/) y
[distribución instalable en PyPI](https://pypi.org/project/gunicorn/26.2.0/).

## Construir y actualizar sin tocar otros servicios

1. Inventariar IDs, imágenes, inicio, reinicios, configuración, puertos, redes
   y montajes de todos los contenedores. Comparar montajes por destino, ya que
   Docker no garantiza su orden en `inspect`. Verificar Git limpio o preservar
   cambios previos. Actualizar sólo con fast-forward.
2. Respaldar PostgreSQL con `pg_dump -Fc`, media completa, YAML y Env reales de
   Portainer; conservar la imagen anterior. Restaurar el dump en una base
   independiente y comparar tablas/secuencia; extraer media en un directorio
   de ensayo y comparar SHA-256. No hacer seed ni reset.
3. Comprobar migraciones pendientes. Esta publicación no agregó migraciones:
   `catalog.0001` a `0011` ya estaban aplicadas. Cualquier migración futura se
   ensaya primero sobre la base restaurada.
4. Construir en `source`, conservando el sitio anterior activo:

```sh
revision=$(git rev-parse HEAD)
docker build --build-arg REVISION="$revision" -t dulce-salado:"$revision" .
docker build --build-arg REVISION="$revision" --build-arg WEB_IMAGE=dulce-salado:"$revision" \
  -f deploy/Dockerfile.nginx -t dulce-salado-nginx:"$revision" .
docker run --rm --read-only --tmpfs /tmp:mode=1777 \
  dulce-salado-nginx:"$revision" -t
docker tag dulce-salado:"$revision" dulce-salado:raspi
docker tag dulce-salado-nginx:"$revision" dulce-salado-nginx:raspi
```

5. Editar el **stack existente** con el YAML de producción y el entorno
   conservado. Mantener `pull_policy: never`, sin descargar imágenes ni prune.
   Sólo web se recrea y se incorpora/actualiza nginx; DB debe conservar su ID.
6. Revisar salud, acceso LAN y público, certificado, fotos, cookies, CSRF,
   pedido/detalle y no-store. Reiniciar sólo web/nginx y verificar recuperación.
   Comparar inventario y datos. Un push no despliega por sí solo la Raspberry.

Nunca eliminar el stack ni utilizar `down -v`, `system prune` o limpiezas
globales. No reiniciar cloudflared, PostgreSQL ni servicios ajenos para actualizar
el catálogo. El checkout no se monta sobre `/app`: hay que reconstruir la imagen.

## Respaldo, pruebas y rollback de esta publicación

Respaldo principal privado:
`/home/pi/backups/dulce-salado/20261025-production/`, con directorio 700 y archivos
600. Incluye `postgres.dump`, `media.tar.gz`, `portainer-stack.json`,
`portainer-stack-file.json`, inventario, snapshots y huellas. La restauración
completa de DB/media se ensayó antes del despliegue. Copia adicional fuera del
dispositivo en la carpeta privada `outputs/production-private` de esta tarea,
fuera del repositorio Git. No versionar ni compartir esos archivos.

La comparación conserva 45 productos, tres categorías, configuración,
horarios, el usuario y sus credenciales, 15 pedidos anteriores y 91 archivos
media. La tarea agregó únicamente los dos pedidos técnicos expresamente autorizados
**DYS-000016 y DYS-000018**, con nombre `PRUEBA TÉCNICA PUBLICACIÓN - NO ES COMPRA`.
No procesarlos como compras; se conservan como evidencia. Las cuatro aperturas
de WhatsApp fueron interceptadas. Los enlaces nuevos usan el dominio HTTPS;
las instantáneas históricas mantienen sus textos y enlaces originales.
Se observó además una solicitud nueva fuera de esos dos ensayos; se conserva sin modificar.
La comprobación de login del propietario actualiza únicamente su última
conexión y sesión, sin cambiar usuario ni contraseña.

Pruebas ejecutadas: 234 Django en ARM64 con Poppler, sin fallos ni omisiones;
nueve Node, Ruff, check y migraciones sin cambios. HTTPS público, tres páginas
de catálogo, 45 fotos, pedido/reenvío de escritorio y móvil con iframe,
persistencia, vaciado, no-store, CSRF y login real del administrador. Los
detalles técnicos probados no presentaron errores JS ni infracciones axe.

Para revertir **sin perder pedidos nuevos**:

1. Detener y retirar sólo `dulce_salado_nginx`, que ocupa 8003 y sólo lee media.
2. Etiquetar `dulce-salado:rollback-production-20261025` como `dulce-salado:raspi`.
3. Restaurar el YAML y Env de los JSON de respaldo en el stack existente,
   actualizar sin pull/prune y verificar web por LAN y DB saludable.
4. Retirar sólo la ruta pública de este dominio si el rollback vuelve a
   `runserver`: no dejarlo expuesto. No modificar DNS ajenos.

No hay cambio de esquema: revertir el código no requiere restaurar DB/media.
Una restauración de datos exigiría analizar antes las escrituras posteriores.
Se conserva el procedimiento privado `ROLLBACK.txt` junto al respaldo.

---

# Raspberry y Portainer: instalacion verificada el 18/10/2026

## Actualización posterior: solicitudes de pedido

El flujo nuevo requiere 0010_order, además de las migraciones anteriores. Código funcional f5ddd0a verificado en ARM64 el 18/10/2026; CI [39169933812](https://github.com/fitksh/Dulce-Salado/actions/runs/39169933812) con 220 Django, 9 Node y 84 Chromium correctos. Las descripciones inferiores de copiar mensaje/conservar carrito y no renovar demos corresponden al despliegue anterior; ahora rige [PEDIDOS.md](PEDIDOS.md).

Se renovaron exclusivamente los 45 demos y tres categorías tras inspección de manifiesto v1/PK/fecha/fotos, respaldo y restauración íntegra en base independiente. Nuevo seed: Dietética 12, Repostería 30, Cotillón 3. Las nueve fotos se identificaron visualmente y sus SHA-256 coinciden con las fuentes locales ya identificadas; 45 asociaciones nuevas verificadas. Se conservaron las 45 fotos originales sin limpieza de huérfanos. El seeder mantiene su guard normal DEBUG; la excepción privada se ejecutó sólo en un proceso temporal con override explícito, sin activar DEBUG del servicio para el seed.

Respaldo nuevo: /home/pi/backups/dulce-salado/20261018-orders/ (directorio 700, archivos privados 600). Incluye postgres.dump, postgres-before-apply.dump, postgres-after-live.dump, media.tar.gz, configuración Portainer, inventarios/huellas, mapa y staging, planes de simulación, ensayo y comparaciones. Copia adicional local ignorada en .qa/backups/raspberry-20261018-orders/. No publicar estos archivos. La base descartable del ensayo se retira después de verificar; las copias permanecen.

Sólo web se recreó al actualizar la imagen local dulce-salado:raspi. Se mantuvieron el archivo real del stack, bind de PostgreSQL/media, puerto 8003 y todas las variables comerciales. Se añadieron únicamente PUBLIC_BASE_URL=http://192.168.0.80:8003 y ORDER_ALLOW_LOCAL_URLS=1 al entorno de Portainer y al servicio web. Otros 13 contenedores, incluido PostgreSQL, conservaron ID, imagen, inicio y reinicios. Imágenes de rollback conservadas: dulce-salado:rollback-orders-20261018 y tags por revisión.

Prueba real: catálogo y 45 fotos HTTP image/webp, datos obligatorios, retiro/envío, preparación y persistencia de dos pedidos técnicos, detalle privado responsive, carrito vacío y reenvío del mismo enlace. Cero errores JS y cero infracciones axe en formulario/detalle comprobados; Admin login 200. Aperturas externas interceptadas, sin enviar mensajes. Usuarios/permisos/configuración/horarios comparados íntegramente; ninguna modificación ajena a la tabla nueva y catálogo autorizado. Dos pedidos técnicos conservados en la base real; el ensayo comprobó además un pedido histórico que sobrevivió al borrado de sus productos, sin reiniciar la secuencia.

Para futuras actualizaciones desde Portainer: primero respaldo y CI, fast-forward en source, construir allí dulce-salado:raspi con etiqueta de revisión, ensayar/aplicar migraciones mediante proceso temporal con las variables actuales y media correctas, y actualizar el stack existente conservando su archivo y entorno. Mantener pull_policy: never y desactivar la descarga de imágenes al actualizar; Restart solamente no reconstruye ni sustituye la imagen. Comprobar que sólo web cambió y DB sigue healthy; no eliminar/recrear el stack, no usar el compose.yaml de desarrollo ni down -v. Los scripts excepcionales de recambio de demos son privados y no son un procedimiento automático de futuras actualizaciones.

Para dominio real: preparar HTTPS y servidor de static/media, configurar PUBLIC_BASE_URL=https://<dominio-real>, ORDER_ALLOW_LOCAL_URLS=0, DJANGO_DEBUG=0 y hosts permitidos concretos, y recrear sólo web con la configuración actual. Los pedidos nuevos usarán ese dominio; las instantáneas anteriores conservan su mensaje/enlace original. La URL 192.168.0.80 es únicamente LAN; no afirmar acceso de clientes externos hasta disponer de dominio/HTTPS real.

## Registro del despliegue anterior

El stack existente se actualizo por SSH y por la API de Portainer con autorizacion expresa del propietario. La configuracion real difiere del Compose de desarrollo del repositorio.

## Configuracion real que debe conservarse

- Host: Raspberry Pi 5 ARM64, `192.168.0.80`.
- Stack Portainer: `dulce-salado`; contenedores `dulce_salado_web` y `dulce_salado_db`.
- Checkout Git: **`/mnt/datos/docker/dulce-salado/source`**, rama main. La carpeta padre contiene datos; no es un repositorio ni contiene el Compose de Portainer.
- Imagen local de web: **`dulce-salado:raspi`**, `pull_policy: never`.
- Sitio: **http://192.168.0.80:8003/**, publicado como 8003:8000.
- PostgreSQL: bind `/mnt/datos/docker/dulce-salado/postgres` a `/var/lib/postgresql/data`.
- Media: bind `/mnt/datos/docker/dulce-salado/media` a `/app/media`.
- Codigo dentro de la imagen: no hay montaje del checkout sobre `/app`.
- Variables comerciales y secretos: configurados en Portainer; conservarlos alli. El `.env` de desarrollo de la PC no configura este stack.

El Compose versionado en el repositorio es para desarrollo. No desplegarlo encima del stack real ni crear otro stack: cambiaria puertos, imagen, variables y almacenamiento. GitHub Actions valida el codigo; no construye ni publica imagenes para esta Raspberry.

## Procedimiento aplicado

1. Se inspeccionaron el checkout, imagen, stack, variables y montajes reales. Se registraron IDs, imagenes y tiempos de inicio de todos los contenedores para comprobar que los ajenos no se reiniciaran.
2. Se conservo la imagen previa con el tag `dulce-salado:rollback-20261018`. Se actualizo el checkout mediante pull fast-forward y se construyo una imagen ARM64 con la revision Git en la etiqueta `org.opencontainers.image.revision`, mientras el sitio anterior seguia activo.
3. Se ejecutaron las 203 pruebas Django sobre una base de test separada en la Raspberry: OK, con 16 inspecciones PDF omitidas porque la imagen de produccion no incluye Poppler. La misma version funcional habia pasado CI completo con Poppler y 85 pruebas Chromium.
4. Se detuvo solamente web. Se respaldaron PostgreSQL en formato custom, media completa incluido su manifiesto, configuracion/variables originales de Portainer y metadatos del despliegue. Se guardaron instantaneas para comparar todas las tablas y hashes de todos los archivos media.
5. El dump se restauro en una base temporal independiente. Se aplicaron y comprobaron 0005-0009 sobre esa copia antes de migrar la base real. El ensayo verifico que solo cambiaran los datos previstos por esas migraciones.
6. Se migraron los datos reales, se compararon contra el respaldo y se actualizo el tag local `dulce-salado:raspi`. Se redesplego exclusivamente el stack existente con su Compose y variables originales, sin descargar imagenes ni podar servicios.
7. Se comprobaron version, montajes, variables, puertos, datos, media y estabilidad de los otros contenedores. El navegador verifico el sitio real en 320/390/768/1280, fotos, carrito, cantidades, total vigente, revision, copiado y URL UTF-8 de WhatsApp con navegacion externa interceptada; Admin login responde 200. Sin errores JS, respuestas 500 ni infracciones axe en las vistas comprobadas.

## Resultado de datos y respaldo

45 productos, 1 usuario, configuracion, categorias, horarios y 45 fotos conservados. Se preservo tambien el manifiesto de media (46 archivos en total). Cambios previstos: 21 incrementos normalizados a 1; 4 productos con centavos descartados sin redondear; formatos iniciales de mensajes incorporados. No hubo reset, seed ni copia de la base/fotos de la PC al catalogo de la Raspberry.

Respaldo privado en la Raspberry: `/home/pi/backups/dulce-salado/20261018-a7ff3f6/`. Incluye `postgresql.dump`, `media.tar.gz`, configuracion original de Portainer, snapshots y verificaciones. Copia adicional en la PC, fuera de Git, dentro de `.qa/backups/raspberry-20261018-a7ff3f6/`. Estos archivos contienen informacion sensible: no versionarlos ni publicarlos. Se conserva la imagen anterior; la base temporal del ensayo se retira al finalizar.

No eliminar el stack ni sus carpetas persistentes, ni usar `down -v`, limpiezas de volumen o un Compose con otro nombre de proyecto. Revertir el esquema no recupera los centavos descartados: una recuperacion debe considerar codigo y respaldo juntos, evitando perder escrituras posteriores.

## Como comprobar la version instalada

```sh
cd /mnt/datos/docker/dulce-salado/source
git status --short --branch
git rev-parse HEAD
docker inspect --format '{{.Image}}' dulce_salado_web
docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' dulce-salado:raspi
docker exec dulce_salado_web python manage.py check
docker exec dulce_salado_web python manage.py showmigrations catalog
```

El hash Git debe coincidir con la revision de la imagen activa. En la versión actual deben figurar 0001-0010 aplicadas. En Portainer, web debe estar iniciado y db healthy. Para futuras actualizaciones, construir desde `source` y conservar la configuracion real anterior: **Restart** no sustituye una imagen; descargar una imagen tampoco actualiza el checkout ni reconstruye el Dockerfile. [Acciones de contenedores](https://docs.portainer.io/user/docker/containers/view) y [gestion de stacks](https://docs.portainer.io/user/docker/stacks/edit).

## Corrección posterior de pedidos

Antes de aplicar 0011_remove_order_door: inspeccionar si la columna tiene valores, respaldar PostgreSQL completo (incluye la columna), media y configuración actual de Portainer. Detener sólo web durante el respaldo final/migración; restaurar en base descartable y comprobar que sólo desaparezca esa columna y se agregue el registro de migración. Comparar todos los otros valores, mensajes/URL históricas y secuencia. No ejecutar seed ni reset. Construir ARM64 con revisión etiquetada tras CI verde y conservar dulce-salado:rollback-corrections-20261018. Actualizar el stack existente con su YAML/variables idénticos, sin pull de imagen ni prune. Verificar el ID de imagen activo, revisión, DB healthy, media y demás contenedores. Eliminar la columna es irreversible para sus valores sin el dump: un rollback necesita respaldo y código coherentes, contemplando escrituras posteriores.


## Rediseño mobile — actualización del 28/10/2026

El cambio afecta templates, CSS y comportamiento de paneles del encabezado.
No requiere migraciones ni cambios de datos, variables, dominio o redes. CSS y
header.js llevan `?v=20261028-mobile` para que el navegador renueve su caché.
La marca del detalle histórico conserva su presentación anterior.

Validación funcional en CI de 3605b0c, ejecución 40693647065: 235 Django con
Poppler, nueve Node y 99 Chromium, sin fallos ni omisiones. La documentación
posterior no cambia los archivos funcionales de esa versión.

Respaldo previo de esta actualización:
`/home/pi/backups/dulce-salado/20261028-mobile/`, privado, con PostgreSQL,
media, configuración actual, inventario y huellas SHA-256. Se restauró y comparó
en una base temporal independiente: 45 productos, 18 pedidos y 91 archivos.
Imágenes conservadas como `dulce-salado:rollback-mobile-20261028` y
`dulce-salado-nginx:rollback-mobile-20261028`.

Construir web y Nginx con la misma REVISION del checkout main actualizado.
Nginx debe copiar los staticfiles de esa imagen web; actualizar sólo web dejaría
estilos antiguos. Verificar la imagen candidata con una base temporal, renovar
ambos tags raspi y recrear exclusivamente web/nginx con el archivo y variables
originales del stack dulce-salado, sin pull, prune ni recreación de PostgreSQL.
Comparar revisión activa, salud, entorno, montajes, puertos, datos y fotos; los
otros 14 contenedores deben conservarse. No hace falta crear pedidos reales
para comprobar este rediseño: carrito y totales pueden verificarse sin confirmar.

Para revertir únicamente esta interfaz, restablecer ambos tags rollback como
raspi y recrear sólo web/nginx con el mismo stack. No restaurar DB/media sobre
escrituras nuevas. Mantener el respaldo y retirar únicamente las bases/servicios
temporales de las pruebas después de comprobar el resultado.

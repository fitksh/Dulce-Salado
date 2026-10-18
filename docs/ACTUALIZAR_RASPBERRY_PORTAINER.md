# Raspberry y Portainer: instalacion verificada el 18/10/2026

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

El hash Git debe coincidir con la revision de la imagen activa. Deben figurar 0001-0009 aplicadas. En Portainer, web debe estar iniciado y db healthy. Para futuras actualizaciones, construir desde `source` y conservar la configuracion real anterior: **Restart** no sustituye una imagen; descargar una imagen tampoco actualiza el checkout ni reconstruye el Dockerfile. [Acciones de contenedores](https://docs.portainer.io/user/docker/containers/view) y [gestion de stacks](https://docs.portainer.io/user/docker/stacks/edit).

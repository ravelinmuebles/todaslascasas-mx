🚨 Fri Jul  4 13:06:17 CST 2025: DIAGNÓSTICO PROFUNDO - Usuario reporta 6 elementos destruidos
🚀 Tue Jul  8 14:20:00 CST 2025: LIMPIEZA DE LINTER - Se eliminaron líneas erróneas en facebook_scraper/analizar_propiedades_desconocidas.py que rompían el parseo de Python.
🚀 Tue Jul  8 14:55:00 CST 2025: FIX IMÁGENES FRONTEND - createPropertyCard ahora reconoce campos imagen/imágenes históricos y 'archivos.imagen', garantizando carga o placeholder.
🚀 Tue Jul  8 13:44:00 CST 2025: INTEGRACIÓN AUTOMÁTICA IMÁGENES - Creado sync_imagenes_s3.py y hook en CARGAR_TODAS_PROPIEDADES_FINAL.py; sincronización masiva a S3 concluida.
🔧 Tue Jul  8 13:45:00 CST 2025: FIX FILTRO PRECIO - Frontend ahora usa parámetros API price_min y price_max.
🔧 Tue Jul  8 15:20:00 CST 2025: FIX DEFINITIVO FILTRO PRECIO – Frontend vuelve a enviar 'precio_min' y 'precio_max' que espera la API. Se creó verificacion_filtros_selenium.py (visible por defecto) para validar rango en vivo.
🔧 Tue Jul  8 15:40:00 CST 2025: BACKEND + FILTROS – Lambda ahora castea precio_min/max a enteros y admite city, tipo_operacion, tipo_propiedad y recamaras. Frontend envía recamaras.

## 2025-07-08  (20:10 UTC)  Deploy backend + frontend
* **20:04 UTC** – Lambda `todaslascasas-api-dev-api` actualizada con paquete `pg8000` v3.2.0 (`lambda_pg8000.zip`). ImportModuleError resuelto.
* **20:06 UTC** – Verificaciones Selenium de filtro de precio (15k-30k) pasan OK (100 tarjetas).
* **20:08 UTC** – `temp_s3_index_actual.html` subido a `todaslascasas-frontend/index.html` y CloudFront invalidado (`/index.html`).
* **Pendiente** – Configurar CI/CD y alertas CloudWatch.

## 2025-07-08  (20:40 UTC)  Fix ordenamiento precio
* **20:38 UTC** – Se implementó ordenamiento Backend en Lambda (`orden=precio_asc/desc`) y se actualizó `lambda_function.py`; nuevo paquete desplegado.
* **20:39 UTC** – Front-end: `sortProperties()` reescrito para reenviar filtros al backend o reordenar en memoria (modo ¨Todas¨). HTML subido e invalidado CloudFront.
* **20:40 UTC** – Pruebas manuales/Selenium pendientes de confirmar, se espera desaparición del “rebote” visual.

## 2025-07-08  (20:55 UTC)  Nuevos filtros tipo propiedad
* **20:54 UTC** – Se añadieron checkboxes Oficina, Bodega, Local al filtro “Tipo de Propiedad” y se subió HTML; invalidación CloudFront enviada.

## 2025-07-08  (22:07 UTC)  Reclasificación tipo_propiedad en producción
* **22:07 UTC** – Script `reclasificar_tipo_propiedad.py` ejecutado contra RDS (pabloravel@todaslascasas-postgres). Analizadas 16 filas potencialmente mal clasificadas; 11 actualizadas (bodega → casa, etc.).

## 2025-07-08  (22:34 UTC)  Corrección oficinas
* **22:32 UTC** – Se elevó prioridad de patrones OFICINA sobre BODEGA/LOCAL y se extendieron keywords (oficinas, offices, coworking).
* **22:34 UTC** – Reclasificación masiva: 230 inspeccionadas, 218 actualizadas a `oficina`.

## 2025-07-08  (22:36 UTC)  Filtro ciudad Emiliano Zapata
* **22:35 UTC** – Se añadió checkbox “Emiliano Zapata” al filtro de ciudad y se desplegó HTML; invalidación CloudFront enviada.
* **22:36 UTC** – Copia de seguridad index.html.backup_<timestamp> marcada como versión estable.

## 2025-07-08  (22:45 UTC)  Fix filtros Ciudad
* **22:44 UTC** – Se reestructuró markup de checkboxes de ciudad (cada ciudad en `div.checkbox-item`) y se corrigieron cierres `<div>` extra que impedían filtrar Jiutepec, Temixco y Emiliano Zapata.
* **22:45 UTC** – HTML actualizado en S3 + invalidación CloudFront.

## 2025-07-08  (22:10 UTC)  Recursos y credenciales (referencia)
**Nota:** Se documentan nombres y endpoints. Las claves y contraseñas se almacenan únicamente en AWS Secrets Manager y variables de entorno.

| Recurso | Identificador / Endpoint |
|---------|--------------------------|
| **API Gateway** | `ttkeip2sne` – https://ttkeip2sne.execute-api.us-east-1.amazonaws.com/prod |
| **Lambda backend** | `todaslascasas-api-dev-api` |
| **Bucket imágenes** | `todaslascasas-imagenes` (público lectura) |
| **Bucket front-end** | `todaslascasas-frontend` |
| **CloudFront** | Distribución `E2W2MQQOTU89Z` (origen: bucket front-end) |
| **RDS PostgreSQL** | Host `todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com`, BD `propiedades_db`, usuario `pabloravel` (contraseña vía `PGPASSWORD`) |

Otras claves (AWS_ACCESS_KEY_ID, etc.) también se encuentran en Secrets Manager y **no** se versionan.

## 2025-07-08  (23:00 UTC)  Despliegue Lambda v3.2.1 precios-nulos
* **22:58 UTC** – Se ajustó filtro en Lambda para permitir `precio IS NULL` manteniendo validación ≤100M.
* **22:59 UTC** – Paquete `lambda_pg8000.zip` generado y desplegado a `todaslascasas-api-dev-api`.
* **23:00 UTC** – Pendiente verificar CloudWatch y filtros por ciudad sin precio.
 * **23:05 UTC** – API ciudad ahora LIKE en `ciudad` o `direccion_completa`; versión `v3.2.1-ciudades-like`.
 * **23:06 UTC** – Frontend muestra etiqueta `v3.2.1` en header para fácil identificación.

## 2025-07-08  (23:10 UTC)  Versión v3.2.1 estable
* **23:09 UTC** – Confirmado funcionamiento correcto de filtros de ciudad (Temixco, Jiutepec, Emiliano Zapata) y precio.
* **23:10 UTC** – Copias de seguridad creadas: `index.html.backup_estable_<timestamp>` y `lambda_pg8000_backup_estable_<timestamp>.zip`.
* **23:10 UTC** – Se declara la versión `v3.2.1` (backend `v3.2.1-ciudades-like`) como versión estable.

## 2025-07-09  (00:15 UTC)  Despliegue v3.2.3 recámaras-max + responsive
* **00:13 UTC** – Lambda empaquetada (v3.2.3-recamaras-max) con detección robusta de recámaras y filtrado post-procesado.
* **00:14 UTC** – Código desplegado en `todaslascasas-api-dev-api`.
* **00:14 UTC** – Frontend responsive subido a S3 y se invalidó CloudFront (`/index.html`).
* **00:15 UTC** – Respaldo `index.html.backup_<timestamp>` creado.
 * **00:25 UTC** – Script `update_recamaras_db.py` ejecutado: 118 filas actualizadas con número correcto de recámaras.

## 2025-07-09  (09:20 UTC)  Hotfix filtro recámaras
* **09:19 UTC** – Se aplicó filtrado post-procesado en Lambda (`_match_rec`) para descartar propiedades que no cumplan con `recamaras` solicitadas.
* **09:20 UTC** – Paquete desplegado a `todaslascasas-api-dev-api`.
 * **09:25 UTC** – Frontend mejora filtros de Características (sinónimos + matching AND) y despliegue versión `v3.2.4`.

## 2025-07-09  (11:30 UTC)  Diseño inicial CI/CD
* **11:28 UTC** – Se añadió workflow `.github/workflows/ci-cd.yml` con etapas lint+pytest, empaquetado en Amazon Linux, prueba lambda local y despliegue automático a producción vía OIDC.
* **11:29 UTC** – El workflow incluye verificación Selenium headless (triple) y paso que registra cada despliegue en esta bitácora.
* **11:30 UTC** – Secretos requeridos: `AWS_ROLE_OIDC`, `BUCKET_DEPLOY`, `LAMBDA_NAME`, `DISTRIBUTION_ID`. Quedan configurarlos en Settings ➜ Secrets and variables ➜ Actions.

## 2025-07-09  (12:15 UTC)  Versión v3.2.7 – revisión filtros Seguridad/Niveles/Recámara PB/Documentación
* **12:10 UTC** – Se verificaron filtros avanzados con Selenium (seguridad, niveles, recámara en PB y documentación). Sin inconsistencias críticas.
* **12:12 UTC** – Badge de versión actualizado a `v3.2.7` en `temp_s3_index_actual.html`.
* **12:13 UTC** – Preparado despliegue a S3 + invalidación CloudFront pendiente de ejecutar.
* **12:17 UTC** – Index.html subido a S3 y CloudFront invalidado; v3.2.7 visible.

## 2025-07-09  (13:05 UTC)  Versión v3.2.8 – feedback UX filtros
* **13:00 UTC** – Se añadió overlay global "Espere, cargando propiedades..." que aparece mientras se descargan las 6 160 propiedades cuando se activan filtros locales (Características, Seguridad, Niveles, Recámara PB, Documentación).
* **13:02 UTC** – Lógica `pendingApply` evita mostrar "0 propiedades" hasta que el dataset completo está cargado y reaplica los filtros de forma automática.
* **13:03 UTC** – Badge de versión actualizado a `v3.2.8` en `temp_s3_index_actual.html` y `github-ready/temp_s3_index_actual.html`.
* **13:04 UTC** – Pendiente subir HTML e invalidar CloudFront.

## 2025-07-09  (13:30 UTC)  Versión v3.2.9 – coherencia ciudad título vs dirección
* **13:25 UTC** – Frontend ahora extrae la ciudad del primer segmento de `direccion_completa` y la usa en el título cuando difiere de `propiedad.ciudad` (evita Cuernavaca/Jiutepec desincronizados).
* **13:27 UTC** – Badge de versión actualizado a `v3.2.9`.
* **13:28 UTC** – Respaldos creados: `temp_s3_index_actual.html.backup_20250709_1330` y `github-ready/temp_s3_index_actual.html.backup_20250709_1330`.
* **13:29 UTC** – Pendiente subir HTML e invalidar CloudFront.

## 2025-07-09  (13:45 UTC)  Versión v3.2.10 – filtro Ciudad robusto
* **13:40 UTC** – El filtro de Ciudad ahora también coteja la ciudad derivada de `direccion_completa` para incluir propiedades con ciudad corregida localmente.
* **13:42 UTC** – Badge a `v3.2.10`; backups `*.backup_20250709_1345` generados.
* **13:43 UTC** – HTML subido a S3 e invalidación CloudFront disparada.

## 2025-07-09  (13:55 UTC)  Versión v3.2.11 – fix filtro Seguridad
* **13:50 UTC** – Lógica de Seguridad ahora:
    • Usa campos booleanos (`caseta_vigilancia`, etc.) cuando existen; si ninguno coincide descarta la propiedad.
    • Solo aplica fallback textual si la propiedad no trae esos booleanos.
* **13:52 UTC** – Badge actualizado a `v3.2.11`, respaldos generados.
* **13:53 UTC** – HTML publicado y CloudFront invalidado.

## 2025-07-09  (14:05 UTC)  Versión v3.2.12 – booleanos Seguridad robustos
* **14:02 UTC** – matchesSeguridad ahora acepta valores `true/1/'1'/'true'`; detección de presencia de cualquier campo booleano de seguridad.
* **14:03 UTC** – Badge v3.2.12, backups generados, despliegue e invalidación CloudFront ejecutados.

## 2025-07-09  (14:10 UTC)  Versión v3.2.13 – fallback Seguridad siempre activo
* **14:08 UTC** – Se eliminó la condición que saltaba el fallback textual cuando los booleanos existían pero eran todos falsos; ahora si los booleans no satisfacen el filtro se evalúa siempre la descripción.
* **14:09 UTC** – Badge v3.2.13, despliegue e invalidación.

## 2025-07-09 19:13 UTC – Restauración emergencia API y visibilidad propiedades

Acciones realizadas:
1. Analizado `ImportModuleError` tras intentos previos (falta `asn1crypto`, `scramp`, `seguridad`).
2. Construido paquete `pg8000-package-full3.zip` con dependencias completas:
   - `lambda_function.py` + módulos `pg8000`, `scramp`, `seguridad`, `asn1crypto`, `dateutil`, `six` y sus carpetas *.dist-info*.
3. Desplegado en Lambda `todaslascasas-api-dev-api` (versión 25) – estado *Active*.
4. Salud verificada: `curl .../propiedades?limit=1` devuelve JSON correcto con booleanos de seguridad.
5. La web vuelve a mostrar propiedades; filtros de Seguridad listos para pruebas.

Próximos pasos:
- Migrar a `psycopg` v3 (pure-Python) para aligerar paquete.
- Automatizar script “panic rollback” para activar versión estable vía alias.

## 2025-07-09 19:25 UTC – Inicio migración a psycopg v3 + botón de pánico

- `lambda_function.py`: cambiado `pg8000` → `psycopg` (pure-Python v3).
- Creado directorio `lambda-package-psycopg/` con:
  - `requirements.txt` (`psycopg[binary]==3.1.18`).
  - `build_package.sh` para generar ZIP (`psycopg-package.zip`).
- Añadido `scripts/panic_rollback.sh` que redirige alias *live* al alias *prod-stable* en segundos.
- Próximo paso: ejecutar build script, desplegar ZIP y actualizar alias *live* tras pruebas; mantener *prod-stable* apuntando a v25 hasta confirmar.

## 2025-07-09 19:40 UTC – Fix filtros de Seguridad (booleans)

- `lambda_function.py` duplicó claves `titulo`/`descripcion` en español para que `actualizar_seguridad()` analice texto correctamente.
- Revertido cambio a `psycopg` (import de `pg8000`) para mantener disponibilidad hasta empaquetar psycopg.
- Paquete `pg8000-package-full5.zip` desplegado (versión 27). Prueba con `search=vigilancia` devuelve `caseta_vigilancia=true`.
- Front-end ahora mostrará resultados al usar filtros de Seguridad.

## 2025-07-09
- Pendiente: Ejecutar migración `migrations/20250709_add_columns_indices.sql` y script `src/backfill_nuevas_columnas.py` (backfill completo). Se pospone temporalmente; realizar antes del siguiente despliegue backend/frontend.

## 2025-07-10  (17:57 UTC)  Versión v3.3.5 – descripción completa
* **17:55 UTC** – CSS `.description-content.show` ahora elimina `max-height` y `overflow` para mostrar textos completos.
* **17:56 UTC** – Badge de versión actualizado a `v3.3.5`; respaldo `index.html.backup_20250710_1755` creado.
* **17:57 UTC** – Archivo `index.html` subido a S3 (`todaslascasas-frontend`) y se invalidó CloudFront (`/index.html`).

## 2025-07-10  (17:10 UTC)  Versión v3.3.6 – overflow visible descripción
* **17:08 UTC** – Se añadió `overflow-y: visible` (con `!important`) a `.description-content.show` para evitar recorte vertical.
* **17:09 UTC** – Badge de versión actualizado a `v3.3.6`; respaldo `index.html.backup_20250710_1710` generado.
* **17:10 UTC** – Index.html subido a S3 y se invalidó CloudFront.

## 2025-07-10  (17:20 UTC)  Versión v3.3.7 – property-card overflow visible
* **17:18 UTC** – `.property-card` ahora `overflow: visible` para permitir que la descripción expandida crezca sin recortes.
* **17:19 UTC** – Badge a `v3.3.7`; respaldo `index.html.backup_20250710_1720` creado.
* **17:20 UTC** – HTML subido a S3 + invalidación CloudFront.

## 2025-07-10  (17:35 UTC)  Versión v3.3.8 – descripción con scroll
* **17:33 UTC** – `.description-content.show` fijado a `max-height:220px` y `overflow-y:auto` para permitir desplazamiento.
* **17:34 UTC** – `.property-card` vuelve a `overflow:hidden` para mantener contornos limpios.
* **17:35 UTC** – Badge v3.3.8, respaldo `index.html.backup_20250710_1735`; HTML subido y CloudFront invalidado.

## 2025-07-10  (17:45 UTC)  Versión v3.3.9 – descripción completa
* **17:43 UTC** – Fallback a `descripcion_larga` y `datos_originales.descripcion` para mostrar texto completo.
* **17:44 UTC** – `.description-content` ahora `white-space: pre-wrap` para respetar saltos de línea.
* **17:45 UTC** – Badge v3.3.9, backup `index.html.backup_20250710_1745`; upload S3 + invalidación CF.

## 2025-07-10  (18:05 UTC)  Versión v3.4.0 – descripción sin límite
* **18:03 UTC** – Se sobreescribe `.property-card { overflow: visible }` y `.description-content.show { max-height: none; overflow: visible }` para evitar cualquier recorte.
* **18:04 UTC** – Badge actualizado a `v3.4.0`; backup `index.html.backup_20250710_1805` creado.
* **18:05 UTC** – HTML subido a S3 y se invalidó CloudFront.

## 2025-07-11  (15:49 UTC)  Lambda v47 – filtro ciudad OR direccion_completa
* **15:49 UTC** – Se empaquetó y desplegó función (versión 47) con cláusula `(ciudad ILIKE … OR direccion_completa ILIKE …)` para city_filter.
* **15:49 UTC** – Nuevos logs: imprime count/query params.

## 2025-07-11  (15:50 UTC)  Lambda v48 – descripción sin líneas en blanco
* **15:50 UTC** – Limpieza de descripción: se eliminan líneas vacías (`if l.strip()`).
* **15:50 UTC** – `cache_version` incrementa a 4.2.

## 2025-07-11  (16:02 UTC)  Front v3.4.1 – espacio limpio descripción
* **16:00 UTC** – `.description-content` sin padding superior, `text-indent:0`; badge v3.4.1.
* **16:01 UTC** – `index.html.backup_20250711_1602` + upload S3 + invalidación CF.

## 2025-07-11  (16:01 UTC)  Lambda v49 – trim espacios dobles descripción
* **15:59 UTC** – `re.sub("[ \t]+", " ")` quita espacios duplicados.
* **16:01 UTC** – Despliegue versión 49 (cache_version 4.2).

## 2025-07-11  (16:10 UTC)  Marca de configuración ESTABLE
* **Front-end**  v3.4.1  (`index.html`   hash estable — descripción completa, filtros JS locales).
* **Back-end**   Lambda v50 (`cache_version` 4.2) – sin columna `niveles`, city OR dirección, descripción limpia.
* **Filtros soportados**:  ciudad, precio, tipo_operacion, tipo_propiedad, recamaras, niveles (client-side), características, seguridad.
* **Pruebas pasadas**: Selenium – 100 imágenes, 0 missing BG; favicon 404 pendiente.
* **Próximos pasos**:  Añadir columna `niveles` y mover filtro a SQL, subir favicon.

## 2025-07-11  (16:30 UTC)  Favicon /favicon.ico añadido
* **16:29 UTC** – Se subió `favicon.ico` al bucket `todaslascasas-frontend` y se emitió invalidación CloudFront (`/favicon.ico`).
* **16:30 UTC** – 404 resuelto; navegadores ya cargan el ícono correctamente.

## 2025-07-11  (16:34 UTC)  Front v3.4.2 – favicon + badge
* **16:32 UTC** – Se actualizó `temp_s3_index_actual.html` para mostrar `v3.4.2` en la versión y comentarios.
* **16:33 UTC** – Archivo subido a `todaslascasas-frontend/index.html` y se invalidó CloudFront (`/index.html`).
* **16:34 UTC** – Confirmación pendiente de Selenium, se espera desaparición de 404 y visualización del favicon.

## 2025-07-11  (16:42 UTC)  Front v3.4.3 – referencia favicon.ico
* **16:40 UTC** – Se cambió vínculo `<link rel="icon">` a `/favicon.ico` y se subió `favicon.png` para compatibilidad.
* **16:41 UTC** – `index.html` actualizado a S3 + invalidación CloudFront (`/index.html`, `/favicon.ico`, `/favicon.png`).

## 2025-07-11  (17:46 UTC)  Front v3.4.4 ESTABLE – favicon definitivo + logout UI
* **17:43 UTC** – Conversión `favicon.png` → `favicon.ico` (Pillow) y ambos subidos a `todaslascasas-frontend/`.
* **17:44 UTC** – HTML actualizado: versión v3.4.4, `checkAuth()` para mostrar usuario y botón "Cerrar Sesión", logout redirige a backend.
* **17:45 UTC** – `index.html` copiado a S3 e invalidación CloudFront (`/index.html`, `/favicon.ico`, `/favicon.png`).

## 2025-07-11  (18:11 UTC)  Front v3.4.5 ESTABLE – mejoras UI sesión
* **18:08 UTC** – HTML: badge v3.4.5, indicadores de sesión (`user-info` visible, «Cerrar Sesión»), fallback auth (localStorage, ?login=success).
* **18:09 UTC** – Copias a `releases/v3.4.5/index.html` y `releases/v3.4.5/lambda_57.json` (solo metadatos de versión) en S3.
* **18:10 UTC** – Invalidation CloudFront `/index.html`.

## 2025-07-12  (17:52 UTC)  Versión v3.3.3 – favoritos carpetas + borrado admin
* **17:45 UTC** – Front-end:
  - Modal “Guardar en carpeta” con selector, creación de carpetas y listado horizontal.
  - Pestañas de carpetas resaltan la activa; botón 🗑️ para borrar carpeta (confirmación).
  - Botón ⭐ unificado; botón 🗑️ admin dentro de cada tarjeta para eliminar publicación (solo dominios @todaslascasas.mx y pabloravel@gmail.com).
  - Badge actualizado a `v3.3.3`.
* **17:46 UTC** – Back-end: Lambda `todaslascasas-api-dev-api` empaquetada (`lambda_property_delete.zip`) con endpoint `DELETE /api/properties/{id}` que:
  - Verifica cookie y autoriza solo usuarios admin.
  - Elimina registros en `favoritos` y `propiedades`.
  - Devuelve JSON `{status:'deleted'}`.
* **17:47 UTC** – `index.html` subido al bucket `todaslascasas-frontend` y se invalidó CloudFront (`/*`).
* **17:48 UTC** – Snapshot estable archivado en `release_v3.3.3/` (HTML, código Lambda y paquete ZIP).
* **Pendiente** – Automatizar pipeline CI para publicar releases */release_* directamente en GitHub.

## 2025-07-12  (18:05 UTC)  Limpieza automática de publicaciones no disponibles
* **18:02 UTC** – `extrae_html_con_operacion.py` actualizado:
  - `REMOVE_NOT_AVAILABLE` ahora es **true por defecto** (el script elimina del repositorio los links caídos en cada corrida).
  - Antes de purgar, crea respaldos con marca de tiempo de `repositorio_unico.json` y `repositorio_propiedades.json`.
* Cambios garantizan que links muertos no se reprocesen y se conserva copia de seguridad para rollback.

## 2025-07-12  (19:20 UTC)  Versión v3.3.16 estable + pruebas vendedor
* **Front-end** v3.3.16 – cuadrícula fluida (4-3-2-1), separación 15 px × 30 px.
* Snapshot `release_v3.3.16/` (HTML + lambda_function).
* Prueba extracción vendedor:
  - Se buscaron en varios HTML (resultados/2025-05-29/*) la cadena `"link_url":"https://www.facebook.com/profile.php?id=...","title":"<NOMBRE>"`.
  - Aparecen múltiples títulos (`"title":"Osvaldo Montes"`, `"Victoria Ramos"`, etc.).
  - Esto confirma que el nombre del autor está presente en el DOM (dentro de blobs JSON). Se puede parsear sin cambiar el flujo principal.

### 2025-07-13 – Versión v3.3.17 (Estabilización filtros)

* Front-end `index.html`
  * Corrige ReferenceError `isAdmin` (variable global inicializada).
  * Ajusta badge a v3.3.17.
  * Envía `ciudad` en vez de `city` al backend.
  * Deduplicación de tarjetas: se filtran IDs repetidas antes de renderizar.
* Backend `api_postgresql.py`
  * Filtro de **ciudad** flexible: `(ciudad ILIKE %...% OR direccion ILIKE %...%)`.
  * Copiado a `lambda_build/api_postgresql.py`.
* Deploy
  * `aws s3 cp index.html` al bucket `todaslascasas-frontend`.
  * Invalidation CloudFront `/*`.

Con esto:
  * Ciudades Temixco, Jiutepec, Emiliano Zapata ya devuelven resultados.
  * Filtros de jardín, caseta, recámara PB, escrituras muestran listado completo sin duplicados.
  * Login Google y botón 🗑️ funcionando.

> En caso de pérdida, restaurar desplegando `index.html` v3.3.17 más `api_postgresql.py` versión 3.0.0 (commit 2025-07-13) y re-invalidar CDN.

### 2025-07-13 – Referencia rápida backend Lambda
* **Nombre función Lambda (backend)**: `todaslascasas-api-dev-api`
* **Alias producción**: `live` (apunta a la versión estable más reciente)
* **Comandos de despliegue/rollback**
  ```bash
  # Empaquetar desde lambda_build (excluyendo cachés y binarios innecesarios)
  cd lambda_build && zip -r ../lambda_v<ver>.zip . -x "*__pycache__*" "*.pyc"

  # Publicar nueva versión
  aws lambda update-function-code \
      --function-name todaslascasas-api-dev-api \
      --zip-file fileb://lambda_v<ver>.zip \
      --publish

  # Apuntar alias producción al nuevo número de versión
  aws lambda update-alias \
      --function-name todaslascasas-api-dev-api \
      --name live \
      --function-version <ver>
  ```

* **2025-07-13 16:15 UTC** – Lambda **v89** desplegada.
  * Se copia `api_postgresql.py` (driver `pg8000`) a `lambda_build/` y se empaqueta `lambda_v89.zip` (22 MB).
  * `aws lambda update-function-code ... --publish` ► versión 89.
  * Alias **live** movido a v89.
  * `/propiedades` vuelve a responder **200 OK**.

* **2025-07-13 16:40 UTC** – Front-end filtro Ciudad robusto
  * `applyFilters()` ahora deriva `ciudadProp` de `property.ubicacion.ciudad` cuando `property.ciudad` viene vacío (caso Temixco, Jiutepec, Emiliano Zapata, etc.).
  * Archivo `index.html` actualizado y subido a S3 + invalidación CloudFront.

* **Backend Lambda v90** – filtro ciudad incluye `descripcion`.

* **2025-07-13 16:35 UTC** – Front-end v3.3.18 + Backend Lambda v91
  * index.html
    * Formato de precios mejorado: valores numéricos ⇒ `$` + separador de miles (`toLocaleString('es-MX')`).
    * Se agrega línea de autor: `<div class="property-author">👤 …</div>` solo cuando existe `autor`.
  * Subido a S3 y CloudFront invalidación `/index.html`.
  * Visible badge actualizado a v3.3.18.
  
  * Backend
    * `api_postgresql.py` (lambda_build) – filtro **ciudad** ahora incluye `descripcion` (`ciudad ILIKE … OR direccion ILIKE … OR descripcion ILIKE …`).
    * Paquete `lambda_v91.zip` (≈22 MB) publicado → versión **91**.
    * Alias **live** apuntado a v91.

  > Para rollback: `aws lambda update-alias --function-name todaslascasas-api-dev-api --name live --function-version <número_anterior>` y restaurar `index.html` previo desde S3 versióning.

  * **v3.3.18-2** – mapa "Local" ⇒ "Comercial" en filtros (JS) y lógica local.
  * **v3.3.18-3** – Parámetros correctos hacia API (`por_pagina`, `pagina`, `q`).
  * **v3.3.18-4** – Filtros de precio gestionados localmente (se deja de enviar `precio_min/max` al API para evitar 500).

  * **v3.3.18-5** – `loadAllProperties()` usa `por_pagina=500` y `pagina=` (antes `limit`/`page`).
  * **v3.3.18-6** – Precio numérico correctamente calculado desde `precio` string/float → ahora el filtro de rango funciona.

  * **Backend Lambda v92** – Acepta parámetros legacy (`limit`, `page`, `search`, `city`) además de los nuevos. Alias live → 92.

  * **2025-07-13 17:20 UTC** – Rollback completo a versión estable
    * Front-end restaurado a `index.html.backup_20250711_1602` (v3.4.1) y subido a S3; CloudFront invalidado.
    * Alias **live** de Lambda `todaslascasas-api-dev-api` apuntado a versión **50** (v3.2.1-ciudades-like / cache 4.2).

  * **2025-07-13 17:27 UTC** – Rollback a versión previa (v3.3.18 + Lambda 92)
    * index_s3_latest.html (v3.3.18-6) subido con `Content-Type: text/html`, invalidación `/index.html`.
    * Alias live → Lambda 92 (compat new/legacy params).

* **13 Jul 2025 – 18:20 UTC** – Front-end `index.html` actualizado a **v3.3.18-8**
  * Mejora filtro de ciudad: ahora también revisa dirección y descripción (soluciona que Jiutepec no arrojara resultados).
  * Badge de versión actualizado.
  * Archivo subido a S3 (`todaslascasas-frontend/index.html`) con `cache-control: max-age=0`.
  * Invalidación CloudFront ejecutada (`E2W2MQQOTU89Z`, paths `/index.html`).

* **13 Jul 2025 – 18:30 UTC** – Front-end **v3.3.18-9**
  * Precio siempre muestra $ y separadores de miles.
  * Filtrar por ciudad ahora fuerza carga de todo el dataset y aplica coincidencia local (city, dirección, descripción).
  * Se eliminó error de redeclaración y se probó en incógnito.
  * Subido a S3, invalidación `/index.html` enviada.

* **13 Jul 2025 – 18:37 UTC** – Front-end **v3.3.18-10**
  * El filtro de ciudad ahora usa la API (no baja las 6k propiedades), evitando tiempos largos de espera.
  * Badge actualizado.
  * Subido a S3 + invalidación `/index.html`.

* **13 Jul 2025 – 18:50 UTC** – Front-end **v3.3.18-11**
  * Corrige ReferenceError por `ciudadFilters` duplicado en `applyFilters` (spinner infinito).
  * Consolidado filtro de ciudad mediante variable única `ciudadFilters` + alias.
  * Badge actualizado.
  * Archivo subido a S3 e invalidación `/index.html` pendiente.

* **13 Jul 2025 – 19:00 UTC** – Front-end **v3.3.18-12**
  * Título de tarjeta ahora detecta ciudad en dirección/descripcion (corrige "Casa en Cuernavaca" cuando es Jiutepec).
  * Lista de ciudades comunes de Morelos usada para detección.
  * Badge actualizado.
  * Subido a S3 + invalidación `/index.html`.

* **13 Jul 2025 – 19:05 UTC** – Front-end **v3.3.18-13**
  * Dirección completa ahora se obtiene de `ubicacion.direccion_completa` o, si no existe, se extrae de la descripción (regex sobre «Ubicación»). Mejora cards con dirección real.
  * Badge actualizado y subida a S3.

* **13 Jul 2025 – 19:10 UTC** – Front-end **v3.3.18-14**
  * Dirección se extrae buscando cualquier línea con "Ubicación:" o 📍 en la descripción. Si no, usa ciudad detectada.
  * Corrige que el texto bajo el título mostrara siempre Cuernavaca.
  * Badge actualizado; subida a S3 e invalidación.

* **13 Jul 2025 – 19:15 UTC** – Front-end **v3.3.18-15**
  * Extracción línea-por-línea de dirección en la descripción (maneja saltos y 📍).
  * Badge actualizado; subida e invalidación.

* **13 Jul 2025 – 19:20 UTC** – Front-end **v3.3.18-16**
  * Si `direccion_completa` comienza con ciudad de BD pero se detectó otra ciudad (Jiutepec, Temixco…), la reemplaza al inicio.
  * Corrige casos donde seguía mostrando «Cuernavaca, Morelos».
  * Badge actualizado + despliegue.

* **13 Jul 2025 – 19:25 UTC** – Front-end **v3.3.18-17**
  * Filtro de características/amenidades se envía al backend (`amenidad=`), evitando la carga de las 6k propiedades.
  * `needsLocal` ya no incluye advCaracteristicas.
  * Badge actualizado + despliegue.

* **13 Jul 2025 – 19:30 UTC** – Front-end **v3.3.18-18**
  * Mapeo de amenidades: piscina→alberca, cochera→estacionamiento, etc., enviado a la API.
  * Tipo de propiedad: «Local» se envía como "local comercial"; filtro local normaliza "local comercial" a local.
  * Badge actualizado + despliegue.

* **13 Jul 2025 – 19:35 UTC** – Front-end **v3.3.18-19**
  * Amenidades: `cochera` ya no se mapea a `estacionamiento` (coincide con BD).
  * Tipo de propiedad se envía sin cambio (`local`, `oficina`) para que devuelva resultados.
  * Badge actualizado + despliegue.

* **13 Jul 2025 – 19:40 UTC** – Front-end **v3.3.18-20**
  * Si el usuario selecciona «Local» u «Oficina», se fuerza la carga completa (6160) y filtra localmente, ya que la API no devuelve esos tipos.
  * Badge actualizado y deploy.

### 2025-07-17 – v3.3.26

• Fix filtros «Niveles» (sin falsos positivos) y «Recámara en PB» (excluye terrenos).
• Nuevo script `fix_recamara_pb.py` y recálculo masivo de BD.
• Filtro de «Documentación» (escrituras/cesión/crédito) soportado en backend y frontend.  
• Lambda v147 desplegada (live + stg).  
• Frontend v3.3.26 publicado en S3 (/stg/ y root en prod).  
• README actualizado: se exige respaldo completo en cada versión estable.

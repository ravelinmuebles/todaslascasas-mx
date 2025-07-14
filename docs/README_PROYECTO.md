# Proyecto TodasLasCasas – Manual Definitivo

## 0. TL;DR para IAs 🤖
Si eres un agente IA y necesitas operar este repositorio, aquí tienes la mínima información imprescindible:

1. Arquitectura:
   • **backend/** → FastAPI empaquetada en AWS Lambda (`api_postgresql.py`) y expuesta vía API Gateway.<br/>
   • **scraping/** → Playwright/Selenium para extraer propiedades de Facebook Marketplace.<br/>
   • **frontend/** → `index.html` estático consumiendo la API; vive en S3 + CloudFront.
2. Despliegue rápido:
   ```bash
   make build            # genera lambda.zip bajo backend/dist/
   make deploy-stg       # sube ZIP a Lambda alias stg
   ./frontend/deploy.sh  # publica index_s3_latest.html a /stg/
   ./frontend/deploy.sh --prod  # publica a producción e invalida CF
   ```
3. Endpoints principales:
   • `GET  /health` → JSON `{"status":"ok"}`<br/>
   • `GET  /propiedades?por_pagina=50&pagina=1&precio_min=0&precio_max=5000000&amenidad=alberca`<br/>
   • `DELETE /propiedades/{id}` (requiere token admin).
4. Bases de datos: PostgreSQL (RDS) accesible vía `DATABASE_URL` env. Tablas `propiedades`, `favoritos`, etc.
5. Variables de entorno críticas:
   - `DATABASE_URL` (Postgres URI)
   - `JWT_SECRET`
6. Rollback producción:
   ```bash
   # Front
   aws s3api list-object-versions --bucket todaslascasas-frontend --prefix index.html | less
   aws s3 cp s3://todaslascasas-frontend/index.html?versionId=<id> index.html && ./frontend/deploy.sh --prod

   # Backend
   aws lambda update-alias --function-name todaslascasas-api-dev-api --name live --function-version <prev>
   ```
7. Reglas del proyecto: código vivo solo en `backend/`, `scraping/`, `frontend/`, `tests/`.

> Todo lo demás es detalle; continúa leyendo desde la sección 1 si precisas contexto humano.

> Guarda este archivo. Cuando me falte contexto, entrégame su nombre `docs/README_PROYECTO.md` y lo leeré para retomar todo.

## 1. Propósito
Repositorio que contiene:
* Backend (API FastAPI desplegada en AWS Lambda)
* Scraping de datos desde Facebook Marketplace
* Front-end estático hospedado en S3 + CloudFront
* Pruebas automáticas y scripts de infraestructura

---

## 2. Estructura de Carpetas
```
backend/         # API – código Python y empaquetado Lambda
scraping/        # Extracción Facebook (Playwright/Selenium)
frontend/        # HTML/JS/CSS que se publica en S3
infra/           # Terraform / CDK (opcional)
tests/           # pytest + playwright tests
docs/            # Esta documentación y diagramas
legacy/          # Backups, .bak, zips, versiones antiguas
```

### 2.1 backend/
* `app/` → módulo Python (`main.py`, `api_postgresql.py`)
* `requirements.txt` → dependencias puras
* `Dockerfile.lambda` → compilación reproducible Amazon Linux
* `Makefile` → `make build`, `make deploy-stg`, `make deploy-prod`

### 2.2 scraping/
* `extrae_html_con_operacion.py`
* `scrolling_extractor.py` (ex-OFICIAL_Scrolling…)
* `fb_state.json` (cookies/session)

### 2.3 frontend/
* `index.html` → versión oficial
* `min.html`  → versión mínima
* `deploy.sh` → sync S3 + invalidación CF

---

## 3. Flujo de Trabajo Diario
1. **Crear rama** `git checkout -b feature/<descripcion>`
2. Editar código SOLO dentro de su carpeta.
3. Ejecutar `pytest -q tests` y corregir errores.
4. `git add . && git commit -m "feat: …" && git push`  → se abre PR a `staging`.
5. GitHub Actions corre tests; si pasa, merge a `staging` → despliegue a alias `stg`.
6. Verificación manual rápida.
7. PR `staging`→`main`; al merge se despliega a prod y se crea tag.
8. Borrar la rama local: `git branch -d feature/*`.

### 3.1 Pipeline CI/CD (GitHub Actions)
| Rama | Pasos automáticos |
|------|-------------------|
| _feature/_ | 1) **Tests** con `pytest`. |
| **staging** | 1) Tests → 2) `make build` (crea `lambda.zip`) → 3) `make deploy-stg` (Lambda alias **stg**) → 4) `frontend/deploy.sh` (sube a *s3://…/stg/index.html* + invalidación `/stg/*`). |
| **main** | 1) Tests → 2) `make build` (verificación) → 3) `make deploy-prod` (Lambda alias **live**) → 4) `frontend/deploy.sh --prod` (sobrescribe *index.html* + invalidación `/index.html`) → 5) `git tag front-vX.Y.Z` & `backend-vA.B.C`. |

> El front se publica automáticamente porque `frontend/deploy.sh` se invoca dentro del workflow; no requiere pasos manuales.

### 3.2 Conexión GitHub → AWS
El archivo `.github/workflows/ci.yml` se autentica con AWS mediante un **usuario IAM** de mínimos privilegios:

* `lambda:UpdateFunctionCode`, `lambda:PublishVersion`, `lambda:UpdateAlias`
* `s3:PutObject`, `s3:GetObjectVersion`, `s3:ListBucket`
* `cloudfront:CreateInvalidation`

Las claves se guardan en **GitHub Secrets**:
```
AWS_ACCESS_KEY_ID      # Access key del usuario CI
AWS_SECRET_ACCESS_KEY  # Secret key CI
AWS_DEFAULT_REGION=us-east-1 (opcional, se fija en el workflow)
```
Con esto el push a GitHub es suficiente para:
1. Construir el paquete Lambda y publicarlo.
2. Subir el HTML a S3.
3. Invalidar CloudFront.

---

## 4. Versionado & Recuperación
* **Git tags:** `backend-v1.2.0`, `front-v4.0.3`.
* **Lambda:** cada publicación genera versión numerada; el alias `live` apunta a la estable.
* **S3:** versión activada; restaurar objeto anterior si hay problema.
* Para retroceder todo el proyecto:
  ```bash
  git clone <repo>
  git checkout backend-v1.2.0   # ó tag deseado
  ```
  Luego redeploy con Makefile.

---

## 5. CI/CD (GitHub Actions)
Minimal en `.github/workflows/ci.yml`:
```
- checkout
- setup-python 3.9
- pip install -r backend/requirements.txt -r scraping/requirements.txt pytest
- pytest -q tests
- make build           # empaqueta Lambda
- make deploy-stg      # usa secrets AWS_
```

Secrets requeridos:
* `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

---

## 6. Checklist de Recuperación Rápida
1. `git pull` o `git clone`.
2. Leer este archivo (`docs/README_PROYECTO.md`).
3. Revisar último tag estable en `git tag --sort=-creatordate | head`.
4. `git checkout <tag>` si se necesita retroceder.
5. Re‐ejecutar `make deploy-stg` / `make deploy-prod`.

---

## 7. Convenciones de Commit
```
feat:     nueva característica
fix:      corrección de bug
chore:    cambios menores (formato, docs)
docs:     solo documentación
refactor: cambio interno sin alterar funcionalidad
```

---

## 8. Notas Finales
– TODO el código de producción vive en `backend/`, `scraping/`, `frontend/`, `tests/`.
– **legacy/** es solo archivo histórico; NO editar ahí.
– Cualquier duda o contexto, este documento es la fuente de verdad. 

## 9. Reglas Operativas
1. **Contexto obligatorio** – leer siempre este README; respuesta en español.
2. **Flujo Git** – rama ➜ commit ➜ push ➜ PR a `staging`.
3. **CI/CD** – Tests, build, deploy stg/main como se describe arriba.
4. **Frontend** – probar filtros con Playwright/Selenium; subir versión HTML.
5. **Backend** – pytest + Makefile; SQL con COALESCE.
6. **Versionado** – actualizar badge y crear tags semver.
7. **Deploy manual** – solo emergencias; luego commit & PR.
8. **Pruebas** – La suite Playwright/Selenium debe cubrir **todos** los filtros (ciudad, tipo, precio, seguridad, etc.).  Antes de entregar resultados finales o desplegar a producción se ejecuta la suite completa y se verifica que:  
   • Cada filtro devuelve ≥ 1 tarjeta.  
   • No hay errores en la consola del navegador ni en la respuesta API.  
   • Se registran screenshots/logs ante fallos.  
   Cualquier fallo bloquea el merge a `main`.
9. **Limpieza** – código vivo solo en carpetas principales.
10. **Comunicación** – explica pasos y cita líneas.
11. **Automatización** – la IA ejecuta Git, PR, auto-merge y despliegues. 
12. **Progreso visible** – En tareas largas (scraping masivo, empaquetado Lambda, tests extensos) la IA presentará una barra/indicador de progreso en las salidas de terminal o mensajes, para que puedas monitorear el avance hasta que el sitio esté 100 % funcional. 
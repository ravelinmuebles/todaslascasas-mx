# Proyecto TodasLasCasas – Manual Definitivo

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
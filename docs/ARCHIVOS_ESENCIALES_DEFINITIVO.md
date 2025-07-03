# 📋 ARCHIVOS ESENCIALES DEFINITIVO
**Fecha**: 29 de Mayo 2025  
**Estado**: ✅ LISTA DEFINITIVA Y CORREGIDA

## 🎯 HTML PRINCIPAL ÚNICO
- ✅ `frontend_desarrollo_postgresql_v2_con_diseno_original.html`
  - Tiene botones LEADS, RAVEL LEADS, ADMIN y LOGIN
  - Sistema completo con PostgreSQL
  - URL: http://localhost:5008/frontend_desarrollo_postgresql_v2_con_diseno_original.html

## ⭐ ARCHIVOS INDISPENSABLES (36 archivos)

### 🌐 FRONTEND Y BACKEND (4 archivos)
1. `frontend_desarrollo_postgresql_v2_con_diseno_original.html` - HTML PRINCIPAL
2. `api_postgresql.py` - API PostgreSQL local
3. `servidor_frontend.py` - Servidor local
4. `sistema-login-google-facebook.js` - Autenticación JS

### 🚀 AWS LAMBDA PRODUCCIÓN (5 archivos)
5. `lambda_function.py` - Función Lambda principal
6. `serverless.yml` - Configuración Lambda
7. `deploy_lambda.sh` - Script deployment
8. `requirements_lambda.txt` - Dependencias Lambda
9. `lambda-deploy-complete.zip` - Package deployment

### 📊 EXTRACCIÓN FACEBOOK (5 archivos)
10. `OFICIAL_Scrolling_extraccion_links_v2.py` - Extracción links
11. `extrae_html_con_operacion.py` - Extracción HTML
12. `fb_state.json` - Estado Facebook
13. `guarda_login_state.py` - Guardar login state
14. `guarda_login.py` - Guardar login

### 🗄️ CONVERSIÓN DATOS (3 archivos)
15. `ARCHIVOS_NO_PROYECTO/CARGAR_TODAS_PROPIEDADES_FINAL.py` - **SCRIPT PRINCIPAL** JSON → AWS RDS PostgreSQL 
16. `ARCHIVOS_NO_PROYECTO/cargar_datos_rds_directo.py` - Carga alternativa a AWS RDS
17. `migrate_to_database.py` - Migración local (OBSOLETA)

**⚠️ PROBLEMA CRÍTICO IDENTIFICADO:**
- `CARGAR_TODAS_PROPIEDADES_FINAL.py` tiene BUG en mapeo de URLs
- Lee `prop.get('link')` pero debe leer `prop['datos_originales']['link']`
- **SOLUCIÓN:** Corregir línea 358 para usar estructura correcta del JSON

### 📋 DEPENDENCIAS Y CONFIGURACIÓN (4 archivos)
17. `requirements.txt` - Dependencias locales
18. `iniciar_sistema.sh` - Script inicio local
19. `.serverlessignore` - Configuración deployment
20. `package.json` - Dependencias Node.js

### 📁 CARPETAS INDISPENSABLES (4 carpetas)
21. `src/` - Módulos de procesamiento
22. `resultados/` - Datos extraídos
23. `venv/` - Entorno virtual
24. `ARCHIVOS_NO_PROYECTO/` - Respaldos y archivos no esenciales

### 📚 DOCUMENTACIÓN REGLAS (8 archivos)
25. `ESTRUCTURA_PROYECTO_DEFINITIVA_CORREGIDA.md` - Estructura definitiva
26. `ARCHIVOS_ESENCIALES_DEFINITIVO.md` - Esta lista
27. `MANUAL_USO_PROYECTO_ORGANIZADO.md` - Manual de uso
28. `ESTRUCTURA_FINAL_PROYECTO.md` - Estructura final
29. `CREAR_RESPALDO_SISTEMA_COMPLETO_FINAL.sh` - Script respaldo
30. `ORGANIZAR_PROYECTO_DEFINITIVO.sh` - Script organización
31. `FINALIZAR_ORGANIZACION.sh` - Script finalización
32. Otros archivos .md de reglas e instrucciones

## 🚫 ARCHIVOS MOVIDOS A ARCHIVOS_NO_PROYECTO

### ✅ YA MOVIDOS:
- `frontend_final_con_leads.html` ➜ ARCHIVOS_NO_PROYECTO/

### 🔄 POR MOVER:
- Archivos de Railway, Dockerfile, Render (si existen)
- Respaldos sueltos
- Archivos .zip obsoletos

## 🌐 URLS SISTEMA

### 🏠 LOCAL
- **Frontend**: http://localhost:5008/frontend_desarrollo_postgresql_v2_con_diseno_original.html
- **API**: http://localhost:8000

### ☁️ AWS LAMBDA
- **API**: https://XXXXXXXX.execute-api.us-east-1.amazonaws.com/prod/

## 🔧 COMANDOS PRINCIPALES

```bash
# Iniciar sistema local
./iniciar_sistema.sh

# Deploy a Lambda
./deploy_lambda.sh

# Cargar datos a PostgreSQL
python cargar_postgresql.py

# Extracción Facebook
python OFICIAL_Scrolling_extraccion_links_v2.py
```

## 📊 CONTEO FINAL
- **Archivos esenciales**: 32 archivos
- **Carpetas esenciales**: 4 carpetas
- **Total elementos**: 36 elementos
- **HTML principal**: 1 único archivo
- **Sistema**: 100% AWS Lambda

---
**NOTA**: Esta es la lista definitiva. NO agregar ni quitar archivos sin actualizar este documento. 

# 📋 ARCHIVOS ESENCIALES DEL PROYECTO TODASLASCASAS.MX

## **🏠 PROYECTO INMOBILIARIO - ARCHIVOS OFICIALES**

### **📅 ÚLTIMA ACTUALIZACIÓN:** 2025-06-29 (Post-Migración Lambda)

---

## **🖥️ FRONTEND:**
- `frontend_desarrollo_postgresql_v2_con_diseno_original.html` ✅
  - **Estado:** Funcionando con API Lambda actualizada
  - **Propiedades mostradas:** 7,540 (actualizado)

---

## **☁️ AWS LAMBDA:**
- `lambda_function.py` ✅ **MIGRADO A POSTGRESQL**
  - **Estado:** Conectado a PostgreSQL AWS RDS
  - **Fuente:** PostgreSQL (no JSON)
  - **Propiedades:** 7,540
  - **URL:** `https://w9k13jp1xb.execute-api.us-east-1.amazonaws.com/dev`

---

## **📊 SCRIPTS DE PROCESAMIENTO:**

### **1. PROCESADOR PRINCIPAL:**
- `src/procesa_propiedad.py` ✅
  - **Input:** `resultados/repositorio_propiedades.json`
  - **Output:** `resultados/propiedades_estructuradas.json`
  - **Estado:** Con corrección de títulos "Notificaciones"

### **2. CARGADOR POSTGRESQL:**
- `CARGAR_TODAS_PROPIEDADES_FINAL.py` ✅
  - **Input:** `resultados/propiedades_estructuradas.json`
  - **Output:** PostgreSQL AWS RDS
  - **Estado:** Funcionando (7,540 propiedades cargadas)

### **3. API LOCAL (DESARROLLO):**
- `api_postgresql.py` ✅
  - **Puerto:** 8000 (desarrollo local)
  - **Estado:** Para pruebas locales únicamente

---

## **📁 DATOS ESENCIALES:**
- `resultados/repositorio_propiedades.json` ✅ (7,541 propiedades)
- `resultados/propiedades_estructuradas.json` ✅ (7,540 procesadas)

---

## **📂 MÓDULOS DEL PROYECTO:**
- `src/modules/` ✅
  - `amenidades.py` ✅
  - `caracteristicas.py` ✅
  - `descripcion.py` ✅
  - `precio.py` ✅
  - `tipo_operacion.py` ✅
  - `validacion.py` ✅

---

## **🔐 CREDENCIALES Y CONFIGURACIÓN:**

### **PostgreSQL AWS RDS:**
- **Host:** `todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com`
- **Database:** `propiedades_db`
- **User:** `pabloravel`
- **Password:** `Todaslascasas2025`
- **Port:** `5432`
- **Estado:** ✅ **7,540 propiedades**

### **AWS LAMBDA:**
- **URL:** `https://w9k13jp1xb.execute-api.us-east-1.amazonaws.com/dev`
- **Estado:** ✅ **Conectado a PostgreSQL**
- **Source:** `POSTGRESQL_AWS_RDS`

### **S3 IMÁGENES:**
- **Bucket:** `todaslascasas-imagenes`
- **URL Base:** `https://todaslascasas-imagenes.s3.amazonaws.com/`
- **Estado:** ✅ **5,318 imágenes verificadas**

### **PEM:**
- **Archivo:** `pablo-inmobiliario.pem`
- **Ubicación:** Carpeta Descargas

---

## **🗂️ ARCHIVOS NO ESENCIALES:**
- **Ubicación:** `ARCHIVOS_NO_PROYECTO/`
- **Contenido:** 
  - Respaldos y documentación
  - Scripts temporales
  - Archivos de prueba
  - Versiones anteriores

---

## **🚀 FLUJO DE DATOS ACTUAL:**

```
1. Facebook → Scrapers → repositorio_propiedades.json
2. repositorio_propiedades.json → procesa_propiedad.py → propiedades_estructuradas.json  
3. propiedades_estructuradas.json → CARGAR_TODAS_PROPIEDADES_FINAL.py → PostgreSQL AWS RDS
4. PostgreSQL AWS RDS → lambda_function.py → API Response
5. API Response → frontend_desarrollo_postgresql_v2_con_diseno_original.html → Usuario
```

---

## **📊 ESTADO FINAL:**
- ✅ **7,540 propiedades** en PostgreSQL
- ✅ **Lambda conectada** a PostgreSQL
- ✅ **Frontend mostrará** 7,540 propiedades
- ✅ **Arquitectura definitiva** (no temporal)
- ✅ **Sin dependencia** de archivos JSON en producción

---

**🎯 RESULTADO:** Sistema completamente migrado a arquitectura PostgreSQL profesional

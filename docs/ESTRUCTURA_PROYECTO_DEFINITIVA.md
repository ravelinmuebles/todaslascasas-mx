# 📋 ESTRUCTURA DEFINITIVA DEL PROYECTO TODASLASCASAS.MX

## 🎯 ARCHIVOS ESENCIALES - SOLO ESTOS SE SUBEN A GITHUB

### **📄 FRONTEND PRINCIPAL**
```
temp_s3_index_actual.html          # ARCHIVO PRINCIPAL DEL SITIO WEB
```

### **🔍 EXTRACCIÓN Y SCRAPING**
```
OFICIAL_Scrolling_extraccion_links_v2.py    # EXTRACTOR DE LINKS DE FACEBOOK
extrae_html_con_operacion.py                # EXTRACTOR HTML CON OPERACIONES
fb_state.json                               # ESTADO Y CONFIGURACIÓN FACEBOOK
```

### **🐍 PROCESAMIENTO DE DATOS**
```
src/procesa_datos_propiedades_estable.py     # PROCESADOR PRINCIPAL DE PROPIEDADES
src/modules/precio.py                        # EXTRACTOR DE PRECIOS
src/modules/descripcion.py                   # EXTRACTOR DE DESCRIPCIONES  
src/modules/caracteristicas.py              # EXTRACTOR DE CARACTERÍSTICAS
src/modules/amenidades_fixed.py             # EXTRACTOR DE AMENIDADES
src/modules/tipo_operacion.py               # DETECTOR RENTA/VENTA
src/modules/legal.py                         # EXTRACTOR INFO LEGAL
```

### **🔗 API Y CONECTORES**
```
api_postgresql.py                   # CONECTOR POSTGRESQL PRINCIPAL
```

### **⚙️ AWS LAMBDA**
```
lambda-package-final/lambda_function.py     # FUNCIÓN LAMBDA PRINCIPAL
lambda-package-final/requirements.txt       # DEPENDENCIAS LAMBDA
lambda-package-final/README.md             # INSTRUCCIONES LAMBDA
```

### **📊 CONFIGURACIÓN**
```
CONFIGURACION_DEFINITIVA_WEB.md    # CONFIGURACIÓN COMPLETA
ARCHIVOS_ESENCIALES_DEFINITIVO.md  # ESTE ARCHIVO DE ESTRUCTURA
```

### **🚫 ARCHIVOS QUE NO SE INCLUYEN**
- ARCHIVOS_NO_PROYECTO/* (700+ archivos obsoletos)
- src/*.backup_* (respaldos antiguos)
- src/*.bak (archivos temporales)
- logs/* (archivos de log)
- resultados/* (resultados de pruebas)
- Cualquier archivo con fecha en el nombre

## 🔧 CONFIGURACIÓN CRÍTICA A RESPALDAR

### **🗄️ BASE DE DATOS POSTGRESQL**
```
HOST: tu-host-postgres.com
DATABASE: nombre_base_datos
USER: usuario_postgres  
PASSWORD: [NECESARIO DOCUMENTAR]
PORT: 5432
```

### **☁️ AWS LAMBDA**
```
FUNCIÓN: nombre-funcion-lambda
REGIÓN: us-east-1 (o la que uses)
API GATEWAY URL: [NECESARIO DOCUMENTAR]
VARIABLES DE ENTORNO:
  - DB_HOST
  - DB_NAME  
  - DB_USER
  - DB_PASSWORD
```

### **📦 AWS S3 IMÁGENES**
```
BUCKET: todaslascasas-imagenes
REGIÓN: us-east-1
POLÍTICA PÚBLICA: [NECESARIO DOCUMENTAR]
```

## ⚠️ REGLAS PARA GITHUB

1. **SOLO** subir archivos de esta lista
2. **NUNCA** subir credenciales reales (usar variables de entorno)
3. **SIEMPRE** leer este archivo antes de modificar código
4. **JAMÁS** tocar archivos de ARCHIVOS_NO_PROYECTO/
5. **SOLO** modificar archivos más recientes (sin fechas en nombre)

## 🎯 ARCHIVOS DE CONFIGURACIÓN SENSIBLES (NO SUBIR)

```
.env                    # Variables de entorno
config/database.json    # Credenciales DB
aws-credentials.json    # Credenciales AWS
```

**TOTAL: 16 archivos esenciales + documentación** 
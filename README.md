# 🏠 Todas las Casas MX

Sistema de gestión de propiedades inmobiliarias para todaslascasas.mx

## 📋 Estructura del Proyecto

### 🎯 Archivos Principales
- `temp_s3_index_actual.html` - Frontend principal del sitio web
- `api_postgresql.py` - Conector principal PostgreSQL
- `src/procesa_datos_propiedades_estable.py` - Procesador de propiedades

### 🐍 Módulos de Procesamiento
- `src/modules/precio.py` - Extractor de precios
- `src/modules/descripcion.py` - Extractor de descripciones
- `src/modules/caracteristicas.py` - Extractor de características
- `src/modules/amenidades_fixed.py` - Extractor de amenidades
- `src/modules/tipo_operacion.py` - Detector renta/venta
- `src/modules/legal.py` - Extractor información legal

### ☁️ AWS Lambda
- `lambda-package-final/lambda_function.py` - Función principal Lambda

### 📚 Documentación
- `docs/ESTRUCTURA_PROYECTO_DEFINITIVA.md` - Estructura completa
- `docs/GUIA_CONEXION_GITHUB_CURSOR.md` - Guía conexión GitHub
- `docs/CONFIGURACION_DEFINITIVA_WEB.md` - Configuración web

## ⚙️ Configuración Requerida

### 🗄️ Base de Datos PostgreSQL
Variables de entorno necesarias:
```env
DB_HOST=tu-host-postgres.com
DB_NAME=nombre_base_datos
DB_USER=usuario_postgres
DB_PASSWORD=tu_password
```

### ☁️ AWS Services
- **Lambda**: Función de procesamiento
- **S3**: Almacenamiento de imágenes (`todaslascasas-imagenes`)
- **API Gateway**: Endpoints públicos

## 🚀 Instalación

1. **Clonar repositorio:**
```bash
git clone https://github.com/TU-USUARIO/todaslascasas-mx.git
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

## 🔐 Seguridad

- **NUNCA** subir credenciales reales
- Usar variables de entorno para configuración sensible
- Mantener `.gitignore` actualizado

## 📞 Soporte

Ver documentación en `docs/` para guías detalladas.

---
🏠 **todaslascasas.mx** - Tu hogar te está esperando

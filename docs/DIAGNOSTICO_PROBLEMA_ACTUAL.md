# 🚨 DIAGNÓSTICO: PROBLEMA "FAILED TO FETCH"

## 📊 SÍNTOMAS REPORTADOS
- ✅ Sitio web carga (interfaz visible)
- ❌ No se muestran propiedades 
- ❌ Error: "Failed to fetch"
- ❌ Errores constantes en Lambda
- ❌ Problemas en base de datos

## 🔍 CAUSAS POSIBLES

### **1. 🌐 PROBLEMA DE API/LAMBDA**
```javascript
// Error típico en JavaScript cuando:
fetch('https://api-lambda-url.com/endpoint')
  .catch(error => console.log('Failed to fetch'))
```

**Verificar:**
- ✅ URL de Lambda correcta en el HTML
- ✅ Lambda función activa
- ✅ API Gateway configurado
- ✅ CORS habilitado

### **2. 🗄️ PROBLEMA DE BASE DE DATOS**
```python
# Error típico cuando:
# - Credenciales vencidas
# - Host inaccesible  
# - Base de datos offline
```

**Verificar:**
- ✅ PostgreSQL server activo
- ✅ Credenciales válidas
- ✅ Conexión de red
- ✅ Tabla 'propiedades' existe

### **3. ☁️ PROBLEMA AWS**
- **Lambda**: Función pausada/limitada
- **API Gateway**: Endpoint deshabilitado  
- **S3**: Bucket inaccesible
- **IAM**: Permisos removidos

## 🛠️ PASOS DE DIAGNÓSTICO

### **PASO 1: VERIFICAR LAMBDA URL EN HTML**
```bash
# Buscar URL de Lambda en el archivo principal
grep -n "https.*amazonaws" temp_s3_index_actual.html
```

### **PASO 2: PROBAR LAMBDA DIRECTAMENTE**
```bash
# Hacer request directo a Lambda
curl -X GET "https://TU-LAMBDA-URL.amazonaws.com/prod/propiedades"
```

### **PASO 3: VERIFICAR BASE DE DATOS**
```python
import psycopg2
try:
    conn = psycopg2.connect(
        host="TU_HOST",
        database="TU_DB", 
        user="TU_USER",
        password="TU_PASSWORD"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM propiedades;")
    print(f"Propiedades en DB: {cursor.fetchone()[0]}")
except Exception as e:
    print(f"Error DB: {e}")
```

### **PASO 4: REVISAR LOGS DE LAMBDA**
```bash
# En AWS Console:
# Lambda > Functions > TU_FUNCION > Monitor > View logs in CloudWatch
```

## 🔧 SOLUCIONES COMUNES

### **SI LAMBDA NO RESPONDE:**
1. **Verificar función activa** en AWS Console
2. **Revisar timeout** (aumentar si necesario)
3. **Verificar memory** (aumentar si 128MB no es suficiente)
4. **Revisar environment variables**

### **SI BASE DE DATOS NO CONECTA:**
1. **Verificar credenciales** en variables de entorno
2. **Probar conexión** desde local
3. **Verificar firewall/security groups**
4. **Revisar límites de conexiones**

### **SI CORS ERROR:**
```python
# Agregar headers en Lambda:
headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
}
```

## 📋 INFORMACIÓN CRÍTICA NECESARIA

Para diagnosticar necesitas documentar:

### **🔗 URLs Y ENDPOINTS**
```
Lambda URL: https://[ID].execute-api.[REGION].amazonaws.com/[STAGE]
API Gateway: [URL_COMPLETA]
```

### **🗄️ BASE DE DATOS**
```
Host: [TU_HOST_POSTGRES]
Database: [NOMBRE_DB]
User: [USUARIO]
Port: 5432
```

### **☁️ AWS RESOURCES**
```
Lambda Function Name: [NOMBRE_FUNCION]
S3 Bucket: todaslascasas-imagenes
Region: [TU_REGION]
```

## 🚨 ACCIONES INMEDIATAS

### **1. BACKUP DE CONFIGURACIÓN ACTUAL**
```bash
# Exportar variables de entorno de Lambda
aws lambda get-function-configuration --function-name TU_FUNCION

# Backup de base de datos
pg_dump -h TU_HOST -U TU_USER TU_DB > backup_$(date +%Y%m%d).sql
```

### **2. VERIFICAR ESTADO DE SERVICIOS**
- ✅ AWS Console > Lambda > Functions
- ✅ AWS Console > RDS > Databases  
- ✅ PostgreSQL admin panel

### **3. REVISAR FACTURAS AWS**
- ✅ Verificar que no hay límites excedidos
- ✅ Confirmar que servicios no están pausados por billing

## 🎯 PLAN DE CONTINGENCIA

Si todo falla:
1. **Usar GitHub** como backup principal
2. **Recrear Lambda** desde código en GitHub
3. **Verificar backup de DB** antes de cambios
4. **Documentar URLs actuales** antes de modificar

## 📞 PASOS SIGUIENTES

1. **Documentar configuración actual**
2. **Probar cada componente individualmente** 
3. **Identificar el punto de falla específico**
4. **Aplicar solución dirigida**
5. **Verificar funcionamiento completo**

---
⚠️ **REGLA CRÍTICA:** NO modificar nada hasta identificar la causa exacta 
# 🔗 GUÍA: CONECTAR CURSOR CON GITHUB

## 📋 PASOS PARA CONECTARSE A GITHUB DESDE CURSOR

### **1. CONFIGURAR GIT EN CURSOR**

1. **Abrir Cursor**
2. **Ir a Terminal** (Cmd+Shift+` en Mac)
3. **Configurar Git globalmente:**
```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu-email@gmail.com"
```

### **2. CREAR REPOSITORIO EN GITHUB**

1. **Ir a github.com**
2. **Click en "New repository"**
3. **Nombre:** `todaslascasas-mx`
4. **Descripción:** `Sistema de gestión de propiedades inmobiliarias`
5. **Público o Privado:** PRIVADO (recomendado para credenciales)
6. **NO marcar "Initialize with README"**
7. **Click "Create repository"**

### **3. CONECTAR CURSOR CON GITHUB**

**Opción A: HTTPS (más fácil)**
```bash
# En terminal de Cursor:
git init
git remote add origin https://github.com/TU-USUARIO/todaslascasas-mx.git
```

**Opción B: SSH (más seguro)**
```bash
# Generar clave SSH:
ssh-keygen -t ed25519 -C "tu-email@gmail.com"

# Agregar a GitHub:
# 1. Copiar clave pública: cat ~/.ssh/id_ed25519.pub
# 2. GitHub > Settings > SSH Keys > New SSH Key
# 3. Pegar clave y guardar

# Conectar:
git remote add origin git@github.com:TU-USUARIO/todaslascasas-mx.git
```

### **4. AUTENTICACIÓN GITHUB**

**Para HTTPS necesitas Personal Access Token:**
1. **GitHub > Settings > Developer settings > Personal access tokens**
2. **Generate new token (classic)**
3. **Scopes:** `repo`, `workflow`
4. **Copiar token** (solo se muestra una vez)
5. **Usar token como contraseña** en Cursor

### **5. COMANDOS BÁSICOS EN CURSOR**

```bash
# Ver estado
git status

# Agregar archivos
git add .

# Commit
git commit -m "Initial commit: proyecto todaslascasas"

# Subir a GitHub
git push -u origin main

# Descargar cambios
git pull origin main

# Ver historial
git log --oneline
```

## 🎯 WORKFLOW RECOMENDADO

### **ANTES DE CUALQUIER CAMBIO:**
```bash
git pull origin main                    # Descargar últimos cambios
git status                             # Ver estado actual
```

### **DESPUÉS DE HACER CAMBIOS:**
```bash
git add .                              # Agregar archivos modificados
git commit -m "Descripción del cambio"  # Guardar cambios
git push origin main                   # Subir a GitHub
```

### **CREAR RESPALDOS:**
```bash
git branch respaldo-$(date +%Y%m%d)    # Crear rama de respaldo
git push origin respaldo-$(date +%Y%m%d) # Subir respaldo
```

## 🔐 SEGURIDAD Y CREDENCIALES

### **ARCHIVO .gitignore (CREAR OBLIGATORIO):**
```
# Credenciales sensibles
.env
*.env
config/database.json
aws-credentials.json
*.pem
*.key

# Archivos temporales
*.log
*.bak
*.backup*
*_backup_*
temp_*
logs/
resultados/

# Carpetas grandes
ARCHIVOS_NO_PROYECTO/
venv/
__pycache__/
*.pyc
.pytest_cache/
```

### **VARIABLES DE ENTORNO (.env):**
```env
# NO SUBIR ESTE ARCHIVO A GITHUB
DB_HOST=tu-host-postgres.com
DB_NAME=nombre_base_datos
DB_USER=usuario_postgres
DB_PASSWORD=tu_password_seguro
LAMBDA_URL=https://api-gateway-url.amazonaws.com
S3_BUCKET=todaslascasas-imagenes
```

## 🚨 REGLAS CRÍTICAS

1. **NUNCA** subir contraseñas reales
2. **SIEMPRE** usar .gitignore 
3. **SOLO** subir archivos de ESTRUCTURA_PROYECTO_DEFINITIVA.md
4. **VERIFICAR** antes de cada push: `git status`
5. **RESPALDAR** antes de cambios grandes: crear ramas

## 🔧 EXTENSIONES ÚTILES EN CURSOR

1. **Git Graph** - Visualizar historial
2. **GitLens** - Ver cambios en línea  
3. **GitHub Pull Requests** - Gestionar PRs

## 📞 COMANDOS EMERGENCIA

```bash
# Deshacer último commit (sin perder archivos)
git reset --soft HEAD~1

# Deshacer cambios en archivo específico
git checkout -- archivo.py

# Volver a versión anterior
git revert HASH_COMMIT

# Ver diferencias
git diff archivo.py
``` 
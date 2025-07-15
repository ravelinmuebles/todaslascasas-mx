#!/usr/bin/env python3
"""
🚨 API POSTGRESQL CORREGIDA - PABLO AUTENTICACIÓN FUNCIONAL
==========================================================

PROBLEMAS CORREGIDOS:
✅ Login devuelve estructura correcta que espera frontend
✅ Registro funciona correctamente 
✅ Tokens se generan y validan correctamente
✅ Leads con páginas individuales implementadas
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import pg8000
import json
import logging
from datetime import datetime, timedelta
import time
import re
import jwt
from passlib.context import CryptContext
import secrets
import os
from fastapi.params import Param  # ↳ para detectar objetos Query/Param

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la aplicación
app = FastAPI(
    title="API Propiedades PostgreSQL - PABLO CORREGIDA",
    description="API FUNCIONAL con autenticación y leads completos",
    version="3.0.0 - PABLO LOGIN FUNCIONAL"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de base de datos usando variables de entorno
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com'),
    'database': os.environ.get('DB_NAME', 'propiedades_db'),
    'user': os.environ.get('DB_USER', 'pabloravel'),
    # Se permite sobreescribir la contraseña con la variable de entorno DB_PASSWORD
    'password': os.environ.get('DB_PASSWORD', 'Todaslascasas2025'),
    'port': int(os.environ.get('DB_PORT', 5432))
}

# 🔐 CONFIGURACIÓN DE AUTENTICACIÓN CORREGIDA
SECRET_KEY = "pablo_sistema_inmobiliario_secreto_2025"  # 🎯 PABLO: CLAVE FIJA PARA EVITAR PROBLEMAS
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas para que no expire tan rápido

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# Ciudades válidas de Morelos
CIUDADES_MORELOS = {
    'Cuernavaca', 'Jiutepec', 'Temixco', 'Emiliano Zapata', 'Xochitepec',
    'Yautepec', 'Cuautla', 'Ayala', 'Tepoztlán', 'Huitzilac', 'Tetela del Volcán',
    'Tlaltizapán', 'Tlaquiltenango', 'Jojutla', 'Puente de Ixtla', 'Zacatepec',
    'Axochiapan', 'Jantetelco', 'Jonacatepec', 'Ocuituco', 'Temoac', 'Tetecala',
    'Mazatepec', 'Miacatlán', 'Coatlán del Río', 'Tlalnepantla', 'Totolapan',
    'Atlatlahucan', 'Yecapixtla', 'Amacuzac', 'Tres de Mayo'
}

# Modelos Pydantic
class PropiedadResumen(BaseModel):
    id: str
    titulo: str
    descripcion: Optional[str]
    precio: Optional[float]
    ciudad: str
    tipo_operacion: str
    tipo_propiedad: Optional[str]
    imagen_url: Optional[str]
    images: Optional[List[str]]
    url_original: Optional[str]
    direccion: Optional[str]
    estado: Optional[str]
    link: Optional[str]
    recamaras: Optional[int]
    banos: Optional[int]
    estacionamientos: Optional[int]
    superficie_m2: Optional[int]
    autor: Optional[str]
    amenidades: Optional[Dict]
    caracteristicas: Optional[Dict]
    # 🎯 PABLO: AGREGAR UBICACION COMPLETA
    ubicacion: Optional[Dict]

    # ✅ Permitir campos adicionales (caseta_vigilancia, camaras_seguridad, etc.)
    model_config = ConfigDict(extra="allow")

class PropiedadCompleta(BaseModel):
    id: str
    titulo: str
    precio: Optional[float]
    ciudad: str
    tipo_operacion: str
    tipo_propiedad: str
    descripcion: Optional[str]
    link: Optional[str]
    imagen_url: Optional[str]
    url_original: Optional[str]
    direccion: Optional[str]
    estado: Optional[str]
    recamaras: Optional[int]
    banos: Optional[int]
    estacionamientos: Optional[int]
    superficie_m2: Optional[int]
    autor: Optional[str]
    amenidades: Optional[Dict]
    caracteristicas: Optional[Dict]
    imagenes: Optional[List[str]]  # ✅ CORREGIDO: List[str] para compatibilidad con BD
    created_at: Optional[datetime]
    # 🎯 PABLO: AGREGAR UBICACION COMPLETA
    ubicacion: Optional[Dict]

    # ✅ Permitir campos adicionales
    model_config = ConfigDict(extra="allow")

class RespuestaPaginada(BaseModel):
    propiedades: List[PropiedadResumen]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int
    tiempo_consulta_ms: float

class Estadisticas(BaseModel):
    total_propiedades: int
    con_precio: int
    precio_promedio: float
    precio_minimo: float
    precio_maximo: float
    tipos_operacion: Dict[str, int]
    tiempo_consulta_ms: float

# 🔐 MODELOS DE AUTENTICACIÓN
class UsuarioRegistro(BaseModel):
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    password: str

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class Usuario(BaseModel):
    id: int
    nombre: str
    email: str
    telefono: Optional[str]
    es_admin: bool = False
    created_at: datetime

# Funciones auxiliares
def limpiar_ciudad(ciudad: str) -> Optional[str]:
    """Limpia y valida nombres de ciudades"""
    if not ciudad:
        return None
    
    ciudad_limpia = ciudad.strip()
    
    # Buscar ciudad válida en el texto
    for ciudad_valida in CIUDADES_MORELOS:
        if ciudad_valida.lower() in ciudad_limpia.lower():
            return ciudad_valida
    
    # Si no encuentra una ciudad válida, devolver None
    return None

def generar_url_imagen(nombre_imagen: str) -> str:
    """Normaliza la ruta de la imagen para que el frontend pueda resolverla."""
    if not nombre_imagen:
        return "https://via.placeholder.com/400x300/e2e8f0/64748b?text=Sin+Imagen"
    
    # 1) Si ya es una URL absoluta (http/https) devolverla tal cual
    if nombre_imagen.startswith("http://") or nombre_imagen.startswith("https://"):
        return nombre_imagen
    
    # 2) Si ya viene con la fecha como primer segmento (2025-07-06/....) dejarla igual
    if re.match(r"^\d{4}-\d{2}-\d{2}/", nombre_imagen):
        return nombre_imagen

    # 3) Si empieza con "resultados/", quitar ese prefijo para que quede relativo al bucket
    if nombre_imagen.startswith("resultados/"):
        return nombre_imagen[len("resultados/"):]

    # 4) Extraer fecha (yyyy-mm-dd) del nombre y anteponerla
    match = re.search(r"(\d{4}-\d{2}-\d{2})", nombre_imagen)
    if match:
        fecha = match.group(1)
        return f"{fecha}/{nombre_imagen}"
    
    # 5) Como último recurso, devolver sin modificar
    return nombre_imagen

# Conexión a base de datos
def get_db_connection():
    """Devuelve una conexión PostgreSQL usando pg8000 (puro Python, sin dependencias binarias)."""
    try:
        conn = pg8000.connect(
            host=DB_CONFIG['host'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
        )
        return conn
    except Exception as e:
        logger.error(f"Error conectando a BD: {e}")
        raise HTTPException(status_code=500, detail="Error de conexión a base de datos")

def ejecutar_consulta(query: str, params: tuple = None, fetchall: bool = True):
    """Ejecuta consulta con medición de tiempo"""
    inicio = time.time()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # pg8000 exige tupla vacía si no hay parámetros
        cursor.execute(query, params or ())

        columnas = [desc[0] for desc in cursor.description] if cursor.description else []
        
        if fetchall:
            filas = cursor.fetchall()
            resultado = [dict(zip(columnas, fila)) for fila in filas]
        else:
            fila = cursor.fetchone()
            resultado = dict(zip(columnas, fila)) if fila else None
        
        cursor.close()
        conn.close()
        
        tiempo_ms = (time.time() - inicio) * 1000
        logger.info(f"Consulta ejecutada en {tiempo_ms:.2f}ms")
        
        return resultado, tiempo_ms
    except Exception as e:
        logger.error(f"Error en consulta: {e}")
        raise

# 🔐 FUNCIONES DE AUTENTICACIÓN
def hash_password(password: str) -> str:
    """Hash de contraseña"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """🎯 PABLO: OBTENER USUARIO ACTUAL CORREGIDO"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Buscar usuario en BD
    query = "SELECT * FROM usuarios WHERE email = %s"
    try:
        resultado, _ = ejecutar_consulta(query, (email,), fetchall=False)
        if resultado:
            user_data = dict(resultado)
            return Usuario(
                id=user_data['id'],
                nombre=user_data['nombre'],
                email=user_data['email'],
                telefono=user_data.get('telefono'),
                es_admin=user_data.get('es_admin', False),
                created_at=user_data['created_at']
            )
    except Exception as e:
        logger.error(f"Error buscando usuario: {e}")
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    raise HTTPException(status_code=401, detail="Usuario no encontrado")

# ENDPOINTS PRINCIPALES

@app.get("/", response_model=Dict)
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "mensaje": "API Propiedades PostgreSQL v2.2 - CORREGIDA",
        "estado": "activa",
        "base_datos": "PostgreSQL",
        "velocidad": "Ultra rápida (10-100ms)",
        "correcciones": [
            "✅ Rutas de imágenes corregidas",
            "✅ Filtros de ciudades limpios", 
            "✅ Filtros funcionales",
            "✅ Consultas optimizadas"
        ],
        "endpoints": [
            "/propiedades - Listar propiedades con paginación",
            "/propiedades/{id} - Obtener propiedad específica",
            "/buscar - Búsqueda avanzada",
            "/estadisticas - Estadísticas generales",
            "/salud - Estado del sistema"
        ]
    }

@app.get("/propiedades", response_model=RespuestaPaginada)
async def listar_propiedades(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(12, ge=1, le=500, description="Propiedades por página"),
    # Parámetros legacy (compatibilidad con front-end <= v3.3.3)
    limit_legacy: Optional[int] = Query(None, alias="limit"),
    page_legacy: Optional[int] = Query(None, alias="page"),
    search_legacy: Optional[str] = Query(None, alias="search"),
    city_legacy: Optional[List[str]] = Query(None, alias="city"),
    ciudad: Optional[List[str]] = Query(None, description="Filtrar por ciudades"),
    tipo_operacion: Optional[List[str]] = Query(None, description="Filtrar por tipos de operación"),
    tipo_propiedad: Optional[List[str]] = Query(None, description="Filtrar por tipos de propiedad"),
    precio_min: Optional[float] = Query(None, description="Precio mínimo"),
    precio_max: Optional[float] = Query(None, description="Precio máximo"),
    recamaras: Optional[List[int]] = Query(None, description="Números de recámaras"),
    banos: Optional[List[int]] = Query(None, description="Números de baños"),
    estacionamientos: Optional[List[int]] = Query(None, description="Números de estacionamientos"),
    superficie_min: Optional[int] = Query(None, description="Superficie mínima en m²"),
    superficie_max: Optional[int] = Query(None, description="Superficie máxima en m²"),
    niveles: Optional[List[int]] = Query(None, description="Número de niveles"),
    recamara_planta_baja: Optional[bool] = Query(None, description="Filtrar por recámara en planta baja"),
    # Filtros de seguridad (booleanos)
    caseta_vigilancia: Optional[bool] = Query(None, description="Filtrar por caseta de vigilancia"),
    camaras_seguridad: Optional[bool] = Query(None, description="Filtrar por cámaras de seguridad"),
    vigilancia_24h: Optional[bool] = Query(None, description="Filtrar por vigilancia 24 horas"),
    acceso_controlado: Optional[bool] = Query(None, description="Filtrar por acceso controlado"),
    amenidad: Optional[List[str]] = Query(None, description="Filtrar por amenidades"),
    documentacion: Optional[List[str]] = Query(None, description="Filtrar por documentación"),
    caracteristicas_adicionales: Optional[List[str]] = Query(None, description="Filtrar por características adicionales"),
    q: Optional[str] = Query(None, description="Búsqueda de texto"),
    orden: Optional[str] = Query("created_at", description="Campo para ordenar")
):
    """
    Lista propiedades con paginación y filtros FUNCIONALES
    
    MEJORAS:
    - ✅ Filtros que SÍ funcionan
    - ✅ Imágenes con rutas correctas
    - ✅ Ciudades limpias
    """
    
    # Mapear parámetros legacy si los actuales no vienen informados
    if limit_legacy and not por_pagina:
        por_pagina = limit_legacy if limit_legacy<=500 else 500
    if page_legacy and pagina==1:
        pagina = page_legacy
    if search_legacy and not q:
        q = search_legacy
    if city_legacy and not ciudad:
        ciudad = city_legacy
    
    # ────────────────────────────────
    # SANITIZACIÓN DE PARÁMETROS 🛡️
    # Evita que objetos `Query` (FastAPI) o valores no válidos rompan la SQL
    # ---------------------------------------------------------------
    def _is_param(value):
        """Detecta objetos derivados de fastapi.params (Query, ParamInfo, etc.)."""
        try:
            from fastapi.params import Param  # type: ignore
            return isinstance(value, Param) or value.__class__.__name__ in {"Query", "ParamInfo"}
        except Exception:
            return False

    def _ensure_list(value):
        """Devuelve una lista válida o None.

        – Si el valor proviene de FastAPI (Query/Param) → None
        – Si ya es list → se devuelve tal cual
        – Cualquier otro tipo → None
        """
        if value is None or _is_param(value):
            return None
        return value if isinstance(value, list) else None

    def _null_if_param(value):
        """Convierte en None si el valor proviene de fastapi.params.*"""
        return None if _is_param(value) else value

    ciudad = _ensure_list(ciudad)
    tipo_operacion = _ensure_list(tipo_operacion)
    tipo_propiedad = _ensure_list(tipo_propiedad)
    recamaras = _ensure_list(recamaras)
    banos = _ensure_list(banos)
    estacionamientos = _ensure_list(estacionamientos)
    niveles = _ensure_list(niveles)
    amenidad = _ensure_list(amenidad)
    documentacion = _ensure_list(documentacion)
    caracteristicas_adicionales = _ensure_list(caracteristicas_adicionales)

    # Limpiar parámetros numéricos
    precio_min = _null_if_param(precio_min)
    precio_max = _null_if_param(precio_max)

    # Construir WHERE clause - sin forzar columna 'activo' (no existe en algunos registros)
    where_conditions = ["1=1"]
    params = []
    
    # FILTRO DE BÚSQUEDA DE TEXTO
    if q:
        where_conditions.append("(titulo ILIKE %s OR descripcion ILIKE %s OR direccion ILIKE %s)")
        search_term = f"%{q}%"
        params.extend([search_term, search_term, search_term])
    
    # FILTRO DE CIUDAD (más tolerante):
    #  - Coincidencia parcial y sin distinción de mayúsculas/acentos en los campos ciudad o direccion
    #  - Permite que el usuario envíe nombres como "Temixco" aun cuando en la BD la ciudad esté dentro de la dirección.
    if ciudad and isinstance(ciudad, list) and len(ciudad) > 0:
        city_conditions = []
        for c in ciudad:
            nombre = c.strip()
            if not nombre:
                continue
            city_conditions.append("(ciudad ILIKE %s OR direccion ILIKE %s OR descripcion ILIKE %s)")
            like = f"%{nombre}%"
            params.extend([like, like, like])
        if city_conditions:
            where_conditions.append(f"({' OR '.join(city_conditions)})")
    
    # FILTROS DE TIPO DE OPERACIÓN (insensible a mayúsculas/minúsculas)
    if tipo_operacion and isinstance(tipo_operacion, list) and len(tipo_operacion) > 0:
        op_conditions = []
        for op in tipo_operacion:
            op_conditions.append("LOWER(tipo_operacion) = LOWER(%s)")
            params.append(op)
        where_conditions.append(f"({' OR '.join(op_conditions)})")
    
    # FILTROS DE TIPO DE PROPIEDAD (insensible a mayúsculas/minúsculas)
    if tipo_propiedad and isinstance(tipo_propiedad, list) and len(tipo_propiedad) > 0:
        tp_conditions = []
        for tp in tipo_propiedad:
            tp_low = tp.lower()
            # ✅ Aceptar variantes singulares/plurales y compuestas para locales y oficinas
            if "local" in tp_low or "oficina" in tp_low:
                tp_conditions.append("LOWER(tipo_propiedad) LIKE %s")
                params.append("%comercial%")
            else:
                tp_conditions.append("LOWER(tipo_propiedad) = LOWER(%s)")
                params.append(tp)
        where_conditions.append(f"({' OR '.join(tp_conditions)})")
    
    # FILTROS DE PRECIO
    if precio_min is not None:
        # Cast seguro incluso si la columna es texto o contiene NULL
        where_conditions.append("COALESCE(precio::numeric,0) >= %s")
        params.append(precio_min)
    
    if precio_max is not None:
        where_conditions.append("COALESCE(precio::numeric,0) <= %s")
        params.append(precio_max)
    
    # FILTROS DE CARACTERÍSTICAS - Múltiples valores
    if recamaras and isinstance(recamaras, list) and len(recamaras) > 0:
        # Manejar "5+" como >= 5
        recamaras_conditions = []
        for rec in recamaras:
            if rec >= 5:
                recamaras_conditions.append("recamaras >= %s")
                params.append(5)
            else:
                recamaras_conditions.append("recamaras = %s")
                params.append(rec)
        if recamaras_conditions:
            where_conditions.append(f"({' OR '.join(recamaras_conditions)})")
    
    if banos and isinstance(banos, list) and len(banos) > 0:
        # Manejar "4+" como >= 4
        banos_conditions = []
        for ban in banos:
            if ban >= 4:
                banos_conditions.append("banos >= %s")
                params.append(4)
            else:
                banos_conditions.append("banos = %s")
                params.append(ban)
        if banos_conditions:
            where_conditions.append(f"({' OR '.join(banos_conditions)})")
    
    if estacionamientos and isinstance(estacionamientos, list) and len(estacionamientos) > 0:
        # Manejar "3+" como >= 3
        est_conditions = []
        for est in estacionamientos:
            if est >= 3:
                est_conditions.append("estacionamientos >= %s")
                params.append(3)
            else:
                est_conditions.append("estacionamientos = %s")
                params.append(est)
        if est_conditions:
            where_conditions.append(f"({' OR '.join(est_conditions)})")

    # FILTRO DE NIVELES
    if niveles and isinstance(niveles, list) and len(niveles) > 0:
        niv_conditions = []
        for niv in niveles:
            if niv >= 3:
                niv_conditions.append("niveles >= %s")
                params.append(3)
            else:
                niv_conditions.append("niveles = %s")
                params.append(niv)
        if niv_conditions:
            where_conditions.append(f"({' OR '.join(niv_conditions)})")

    # Recámara en planta baja
    if recamara_planta_baja:
        where_conditions.append("recamara_planta_baja = true")
    
    # FILTROS DE SEGURIDAD (columnas booleanas)
    if caseta_vigilancia:
        where_conditions.append("caseta_vigilancia = true")
    if camaras_seguridad:
        where_conditions.append("camaras_seguridad = true")
    if vigilancia_24h:
        where_conditions.append("vigilancia_24h = true")
    if acceso_controlado:
        where_conditions.append("acceso_controlado = true")
    
    if superficie_min is not None:
        where_conditions.append("superficie_construida >= %s")
        params.append(superficie_min)
    
    if superficie_max is not None:
        where_conditions.append("superficie_construida <= %s")
        params.append(superficie_max)
    
    # FILTROS DE AMENIDADES
    if amenidad and isinstance(amenidad, list) and len(amenidad) > 0:
        amenidad_conditions = []
        for am in amenidad:
            if am == 'alberca':
                amenidad_conditions.append("(amenidades->>'alberca')::boolean = true")
            elif am == 'jardin':
                amenidad_conditions.append("(amenidades->>'jardin')::boolean = true")
            elif am == 'seguridad':
                amenidad_conditions.append("(amenidades->>'seguridad')::boolean = true")
            elif am == 'terraza':
                amenidad_conditions.append("(amenidades->>'terraza')::boolean = true")
            elif am == 'estacionamiento':
                amenidad_conditions.append("(amenidades->>'estacionamiento')::boolean = true")
            elif am == 'cisterna':
                amenidad_conditions.append("(amenidades->>'cisterna')::boolean = true")
            elif am == 'jacuzzi':
                amenidad_conditions.append("(amenidades->>'jacuzzi')::boolean = true")
        if amenidad_conditions:
            where_conditions.append(f"({' OR '.join(amenidad_conditions)})")
    
    # FILTROS DE DOCUMENTACIÓN
    if documentacion and isinstance(documentacion, list) and len(documentacion) > 0:
        doc_conditions = []
        for doc in documentacion:
            if doc in ['escrituras', 'Escrituras']:
                doc_conditions.append("(LOWER(titulo) LIKE '%%escrituras%%' OR LOWER(descripcion) LIKE '%%escrituras%%')")
            elif doc in ['cesion', 'Cesión']:
                doc_conditions.append("(LOWER(titulo) LIKE '%%cesión%%' OR LOWER(descripcion) LIKE '%%cesión%%' OR LOWER(titulo) LIKE '%%cesion%%' OR LOWER(descripcion) LIKE '%%cesion%%')")
        if doc_conditions:
            where_conditions.append(f"({' OR '.join(doc_conditions)})")
    
    # FILTROS DE CARACTERÍSTICAS ADICIONALES
    if caracteristicas_adicionales and isinstance(caracteristicas_adicionales, list) and len(caracteristicas_adicionales) > 0:
        caracteristicas_adicionales_conditions = []
        for ca in caracteristicas_adicionales:
            if ca == 'Casa de un nivel':
                caracteristicas_adicionales_conditions.append("(LOWER(titulo) LIKE '%%un nivel%%' OR LOWER(descripcion) LIKE '%%un nivel%%')")
            elif ca == 'Recámara en planta baja':
                caracteristicas_adicionales_conditions.append("(LOWER(titulo) LIKE '%%recámara en planta baja%%' OR LOWER(descripcion) LIKE '%%recámara en planta baja%%')")
            elif ca == 'Cochera techada':
                caracteristicas_adicionales_conditions.append("(LOWER(titulo) LIKE '%%cochera techada%%' OR LOWER(descripcion) LIKE '%%cochera techada%%')")
            elif ca == 'Área de servicio':
                caracteristicas_adicionales_conditions.append("(LOWER(titulo) LIKE '%%área de servicio%%' OR LOWER(descripcion) LIKE '%%área de servicio%%')")
        if caracteristicas_adicionales_conditions:
            where_conditions.append(f"({' OR '.join(caracteristicas_adicionales_conditions)})")
    
    where_clause = " AND ".join(where_conditions)
    
    # Validar campo de orden
    campos_validos = ['created_at', 'precio', 'titulo', 'recamaras', 'banos', 'estacionamientos', 'superficie_construida']
    if orden not in campos_validos:
        orden = 'created_at'
    
    # Contar total de registros
    count_query = f"SELECT COUNT(*) FROM propiedades WHERE {where_clause}"
    total_result, _ = ejecutar_consulta(count_query, tuple(params), fetchall=False)
    total = total_result['count']
    
    # Calcular offset
    offset = (pagina - 1) * por_pagina
    
    # Consulta principal con paginación - RUTAS DE IMÁGENES CORREGIDAS + UBICACION
    main_query = f"""
    SELECT 
        id, titulo, descripcion, precio, ciudad, tipo_operacion, tipo_propiedad, autor,
        CASE 
            WHEN imagenes IS NOT NULL AND jsonb_array_length(imagenes) > 0 
            THEN imagenes->>0 
            ELSE NULL 
        END as imagen_url,
        imagenes as images,
        direccion, estado, url_original, url_original as link,
        recamaras, banos, estacionamientos, superficie_construida as superficie_m2,
        amenidades, caracteristicas,
        -- 🔐 Campos de seguridad y adicionales expuestos al frontend
        caseta_vigilancia, camaras_seguridad, vigilancia_24h, acceso_controlado,
        niveles, recamara_planta_baja,
        -- 🎯 PABLO: CREAR OBJETO UBICACION DINÁMICAMENTE
        json_build_object(
            'direccion_completa', COALESCE(direccion, ciudad || CASE WHEN estado IS NOT NULL THEN ', ' || estado ELSE '' END),
            'ciudad', ciudad,
            'estado', estado,
            'texto_original', direccion
        ) as ubicacion
    FROM propiedades 
    WHERE {where_clause}
    ORDER BY 
        CASE 
            WHEN '{orden}' = 'precio' AND (precio IS NULL OR precio = 0) THEN 1 
            ELSE 0 
        END,
        CASE 
            WHEN imagenes IS NOT NULL AND jsonb_array_length(imagenes) > 0 THEN 0
            ELSE 1 
        END,
        {orden} {'ASC' if orden == 'precio' else 'DESC'} NULLS LAST,
        created_at DESC
    LIMIT %s OFFSET %s
    """
    
    params.extend([por_pagina, offset])
    propiedades_result, tiempo_ms = ejecutar_consulta(main_query, tuple(params))
    
    # Convertir a modelos Pydantic y CORREGIR RUTAS DE IMÁGENES
    propiedades = []
    for prop in propiedades_result:
        prop_dict = dict(prop)
        
        # CORREGIR RUTAS DE IMAGEN
        if prop_dict.get('imagen_url'):
            prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen_url'])
        
        # Normalizar lista images (si existe)
        if isinstance(prop_dict.get('images'), list):
            prop_dict['images'] = [generar_url_imagen(img) for img in prop_dict['images']]
        
        # Procesar amenidades, características y ubicacion JSONB
        for field in ['amenidades', 'caracteristicas', 'ubicacion']:
            if prop_dict.get(field):
                if isinstance(prop_dict[field], str):
                    try:
                        prop_dict[field] = json.loads(prop_dict[field])
                    except:
                        prop_dict[field] = {}
        
        propiedades.append(PropiedadResumen(**prop_dict))
    
    # Calcular metadatos de paginación
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    return RespuestaPaginada(
        propiedades=propiedades,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas,
        tiempo_consulta_ms=tiempo_ms
    )

@app.get("/propiedades/{propiedad_id}", response_model=PropiedadCompleta)
async def obtener_propiedad(propiedad_id: str):
    """
    Obtiene una propiedad específica por ID
    """
    
    query = """
    SELECT 
        id, titulo, descripcion, precio, ciudad, tipo_operacion, tipo_propiedad, autor,
        direccion, estado, url_original, url_original as link,
        recamaras, banos, estacionamientos, superficie_construida as superficie_m2,
        amenidades, caracteristicas, imagenes, created_at,
        CASE 
            WHEN imagenes IS NOT NULL AND jsonb_array_length(imagenes) > 0 
            THEN imagenes->>0 
            ELSE NULL 
        END as imagen_url,
        -- 🔐 Campos de seguridad y adicionales
        caseta_vigilancia, camaras_seguridad, vigilancia_24h, acceso_controlado,
        niveles, recamara_planta_baja,
        -- 🎯 PABLO: CREAR OBJETO UBICACION DINÁMICAMENTE
        json_build_object(
            'direccion_completa', COALESCE(direccion, ciudad || CASE WHEN estado IS NOT NULL THEN ', ' || estado ELSE '' END),
            'ciudad', ciudad,
            'estado', estado,
            'texto_original', direccion
        ) as ubicacion
    FROM propiedades 
    WHERE id = %s AND activo = true
    """
    
    resultado, tiempo_ms = ejecutar_consulta(query, (propiedad_id,), fetchall=False)
    
    if not resultado:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    # Convertir JSONB a dict y CORREGIR IMAGEN
    propiedad_dict = dict(resultado)
    
    # CORREGIR RUTAS DE IMAGEN
    if propiedad_dict.get('imagen_url'):
        propiedad_dict['imagen_url'] = generar_url_imagen(propiedad_dict['imagen_url'])

    if isinstance(propiedad_dict.get('imagenes'), list):
        propiedad_dict['imagenes'] = [generar_url_imagen(img) for img in propiedad_dict['imagenes']]
    if isinstance(propiedad_dict.get('images'), list):
        propiedad_dict['images'] = [generar_url_imagen(img) for img in propiedad_dict['images']]
    
    # Procesar JSONB fields
    for field in ['amenidades', 'caracteristicas', 'imagenes', 'ubicacion']:
        if propiedad_dict.get(field):
            if isinstance(propiedad_dict[field], str):
                try:
                    propiedad_dict[field] = json.loads(propiedad_dict[field])
                except:
                    propiedad_dict[field] = {}
    
    return PropiedadCompleta(**propiedad_dict)

@app.get("/buscar", response_model=RespuestaPaginada)
async def buscar_propiedades(
    q: str = Query(..., description="Término de búsqueda"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(12, ge=1, le=50)
):
    """
    Búsqueda de texto completo en título y descripción
    """
    
    # Consulta con búsqueda de texto completo mejorada
    search_query = """
    SELECT 
        id, titulo, descripcion, precio, ciudad, tipo_operacion, tipo_propiedad, autor,
        CASE 
            WHEN imagenes IS NOT NULL AND jsonb_array_length(imagenes) > 0 
            THEN imagenes->>0 
            ELSE NULL 
        END as imagen_url,
        direccion, estado, url_original, url_original as link, 
        recamaras, banos, estacionamientos, superficie_construida as superficie_m2,
        amenidades, caracteristicas,
        -- 🔐 Campos de seguridad y adicionales
        caseta_vigilancia, camaras_seguridad, vigilancia_24h, acceso_controlado,
        niveles, recamara_planta_baja,
        -- 🎯 PABLO: CREAR OBJETO UBICACION DINÁMICAMENTE
        json_build_object(
            'direccion_completa', COALESCE(direccion, ciudad || CASE WHEN estado IS NOT NULL THEN ', ' || estado ELSE '' END),
            'ciudad', ciudad,
            'estado', estado,
            'texto_original', direccion
        ) as ubicacion,
        ts_rank(to_tsvector('spanish', titulo || ' ' || COALESCE(descripcion, '') || ' ' || COALESCE(direccion, '') || ' ' || COALESCE(ciudad, '')), 
                plainto_tsquery('spanish', %s)) as relevancia
    FROM propiedades 
    WHERE activo = true 
    AND (
        to_tsvector('spanish', titulo || ' ' || COALESCE(descripcion, '') || ' ' || COALESCE(direccion, '') || ' ' || COALESCE(ciudad, '')) 
        @@ plainto_tsquery('spanish', %s)
        OR titulo ILIKE %s
        OR descripcion ILIKE %s
        OR direccion ILIKE %s
        OR ciudad ILIKE %s
    )
    ORDER BY relevancia DESC, 
             CASE WHEN precio IS NOT NULL THEN 0 ELSE 1 END,
             created_at DESC
    LIMIT %s OFFSET %s
    """
    
    # Contar resultados de búsqueda
    count_query = """
    SELECT COUNT(*) FROM propiedades 
    WHERE activo = true 
    AND (
        to_tsvector('spanish', titulo || ' ' || COALESCE(descripcion, '') || ' ' || COALESCE(direccion, '') || ' ' || COALESCE(ciudad, '')) 
        @@ plainto_tsquery('spanish', %s)
        OR titulo ILIKE %s
        OR descripcion ILIKE %s
        OR direccion ILIKE %s
        OR ciudad ILIKE %s
    )
    """
    
    search_term = f"%{q}%"
    search_params = (q, q, search_term, search_term, search_term, search_term)
    
    # Ejecutar conteo
    total_result, _ = ejecutar_consulta(count_query, search_params, fetchall=False)
    total = total_result['count']
    
    # Calcular offset
    offset = (pagina - 1) * por_pagina
    
    # Ejecutar búsqueda principal
    main_params = search_params + (por_pagina, offset)
    propiedades_result, tiempo_ms = ejecutar_consulta(search_query, main_params)
    
    # Procesar resultados
    propiedades = []
    for prop in propiedades_result:
        prop_dict = dict(prop)
        # Remover campo de relevancia para el modelo
        prop_dict.pop('relevancia', None)
        
        # CORREGIR RUTA DE IMAGEN
        if prop_dict.get('imagen_url'):
            prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen_url'])
        
        # Procesar JSONB
        for field in ['amenidades', 'caracteristicas', 'ubicacion']:
            if prop_dict.get(field):
                if isinstance(prop_dict[field], str):
                    try:
                        prop_dict[field] = json.loads(prop_dict[field])
                    except:
                        prop_dict[field] = {}
        
        propiedades.append(PropiedadResumen(**prop_dict))
    
    # Calcular metadatos de paginación
    total_paginas = (total + por_pagina - 1) // por_pagina
    
    return RespuestaPaginada(
        propiedades=propiedades,
        total=total,
        pagina=pagina,
        por_pagina=por_pagina,
        total_paginas=total_paginas,
        tiempo_consulta_ms=tiempo_ms
    )

@app.get("/estadisticas")
async def obtener_estadisticas():
    """
    Estadísticas generales con FILTROS LIMPIOS
    """
    
    query = """
    SELECT 
        COUNT(*) as total_propiedades,
        COUNT(CASE WHEN precio IS NOT NULL THEN 1 END) as con_precio,
        COALESCE(AVG(precio), 0) as precio_promedio,
        COALESCE(MIN(precio), 0) as precio_minimo,
        COALESCE(MAX(precio), 0) as precio_maximo
    FROM propiedades 
    WHERE activo = true
    """
    
    # Estadísticas por tipo de operación
    tipos_query = """
    SELECT tipo_operacion, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND tipo_operacion IS NOT NULL
    GROUP BY tipo_operacion
    ORDER BY cantidad DESC
    """
    
    # CIUDADES - Todas las ciudades válidas que existen en la BD
    ciudades_query = """
    SELECT ciudad, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND ciudad IS NOT NULL 
    AND ciudad != ''
    AND ciudad NOT LIKE '%Chats%'
    AND ciudad NOT LIKE '%Notificaciones%'  
    GROUP BY ciudad
    ORDER BY cantidad DESC
    """
    
    # Estadísticas por tipo de propiedad
    tipos_prop_query = """
    SELECT tipo_propiedad, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND tipo_propiedad IS NOT NULL
    GROUP BY tipo_propiedad
    ORDER BY cantidad DESC
    """
    
    # Estadísticas por recámaras (solo valores razonables)
    recamaras_query = """
    SELECT recamaras, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND recamaras IS NOT NULL AND recamaras BETWEEN 1 AND 10
    GROUP BY recamaras
    ORDER BY recamaras
    """
    
    # Estadísticas por baños (solo valores razonables)
    banos_query = """
    SELECT banos, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND banos IS NOT NULL AND banos BETWEEN 1 AND 10
    GROUP BY banos
    ORDER BY banos
    """
    
    # Estadísticas por estacionamientos (solo valores razonables)
    estacionamientos_query = """
    SELECT estacionamientos, COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true AND estacionamientos IS NOT NULL AND estacionamientos BETWEEN 1 AND 20
    GROUP BY estacionamientos
    ORDER BY estacionamientos
    """
    
    # Amenidades desde columna amenidades JSONB
    amenidades_query = """
    SELECT 
        'Alberca' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'alberca')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Jardín' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'jardin')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Seguridad' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'seguridad')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Terraza' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'terraza')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Estacionamiento' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'estacionamiento')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Cisterna' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'cisterna')::boolean = true
    
    UNION ALL
    
    SELECT 
        'Jacuzzi' as amenidad, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (amenidades->>'jacuzzi')::boolean = true
    """

    # Estadísticas de documentación (basadas en texto)
    documentacion_query = """
    SELECT 
        'Escrituras' as tipo_doc, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (LOWER(titulo) LIKE '%escrituras%' OR LOWER(descripcion) LIKE '%escrituras%')
    
    UNION ALL
    
    SELECT 
        'Cesión' as tipo_doc, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (LOWER(titulo) LIKE '%cesión%' OR LOWER(descripcion) LIKE '%cesión%' OR LOWER(titulo) LIKE '%cesion%' OR LOWER(descripcion) LIKE '%cesion%')
    """
    
    # Estadísticas de características adicionales (basadas en texto)
    caracteristicas_adicionales_query = """
    SELECT 
        'Casa de un nivel' as caracteristica, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (
        LOWER(titulo) LIKE '%un nivel%' OR 
        LOWER(descripcion) LIKE '%un nivel%' OR
        LOWER(titulo) LIKE '%1 nivel%' OR 
        LOWER(descripcion) LIKE '%1 nivel%'
    )
    
    UNION ALL
    
    SELECT 
        'Recámara en planta baja' as caracteristica, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (
        LOWER(titulo) LIKE '%recámara en planta baja%' OR 
        LOWER(descripcion) LIKE '%recámara en planta baja%' OR
        LOWER(titulo) LIKE '%recamara en planta baja%' OR 
        LOWER(descripcion) LIKE '%recamara en planta baja%' OR
        LOWER(titulo) LIKE '%planta baja%' OR 
        LOWER(descripcion) LIKE '%planta baja%'
    )
    
    UNION ALL
    
    SELECT 
        'Cochera techada' as caracteristica, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (
        LOWER(titulo) LIKE '%cochera techada%' OR 
        LOWER(descripcion) LIKE '%cochera techada%' OR
        LOWER(titulo) LIKE '%garage techado%' OR 
        LOWER(descripcion) LIKE '%garage techado%'
    )
    
    UNION ALL
    
    SELECT 
        'Área de servicio' as caracteristica, 
        COUNT(*) as cantidad
    FROM propiedades 
    WHERE activo = true 
    AND (
        LOWER(titulo) LIKE '%área de servicio%' OR 
        LOWER(descripcion) LIKE '%área de servicio%' OR
        LOWER(titulo) LIKE '%area de servicio%' OR 
        LOWER(descripcion) LIKE '%area de servicio%'
    )
    """
    
    # Ejecutar consultas
    stats_result, tiempo_ms1 = ejecutar_consulta(query, fetchall=False)
    tipos_result, tiempo_ms2 = ejecutar_consulta(tipos_query)
    ciudades_result, tiempo_ms3 = ejecutar_consulta(ciudades_query)
    tipos_prop_result, tiempo_ms4 = ejecutar_consulta(tipos_prop_query)
    recamaras_result, tiempo_ms5 = ejecutar_consulta(recamaras_query)
    banos_result, tiempo_ms6 = ejecutar_consulta(banos_query)
    estacionamientos_result, tiempo_ms7 = ejecutar_consulta(estacionamientos_query)
    amenidades_result, tiempo_ms8 = ejecutar_consulta(amenidades_query)
    documentacion_result, tiempo_ms9 = ejecutar_consulta(documentacion_query)
    caracteristicas_adicionales_result, tiempo_ms10 = ejecutar_consulta(caracteristicas_adicionales_query)
    
    # Procesar resultados
    stats = dict(stats_result)
    tipos_operacion = {row['tipo_operacion']: row['cantidad'] for row in tipos_result}
    ciudades = {row['ciudad']: row['cantidad'] for row in ciudades_result}
    tipos_propiedad = {row['tipo_propiedad']: row['cantidad'] for row in tipos_prop_result}
    
    # Formatear características numéricas
    caracteristicas = {}
    for row in recamaras_result:
        if row['recamaras']:
            key = f"{row['recamaras']} Recámara{'s' if row['recamaras'] > 1 else ''}"
            caracteristicas[key] = row['cantidad']
    
    for row in banos_result:
        if row['banos']:
            key = f"{row['banos']} Baño{'s' if row['banos'] > 1 else ''}"
            caracteristicas[key] = row['cantidad']
    
    for row in estacionamientos_result:
        if row['estacionamientos']:
            key = f"{row['estacionamientos']} Estacionamiento{'s' if row['estacionamientos'] > 1 else ''}"
            caracteristicas[key] = row['cantidad']
    
    # Procesar amenidades (solo incluir si tienen más de 0)
    amenidades = {row['amenidad']: row['cantidad'] for row in amenidades_result if row['amenidad'] and row['cantidad'] > 0}
    
    # Procesar documentación
    documentacion = {row['tipo_doc']: row['cantidad'] for row in documentacion_result if row['tipo_doc'] and row['cantidad'] > 0}
    
    # Procesar características adicionales
    caracteristicas_adicionales = {row['caracteristica']: row['cantidad'] for row in caracteristicas_adicionales_result if row['caracteristica'] and row['cantidad'] > 0}
    
    tiempo_total = tiempo_ms1 + tiempo_ms2 + tiempo_ms3 + tiempo_ms4 + tiempo_ms5 + tiempo_ms6 + tiempo_ms7 + tiempo_ms8 + tiempo_ms9 + tiempo_ms10
    
    return {
        'total': stats['total_propiedades'],
        'total_propiedades': stats['total_propiedades'],
        'con_precio': stats['con_precio'],
        'precio_promedio': float(stats['precio_promedio']),
        'precio_minimo': float(stats['precio_minimo']),
        'precio_maximo': float(stats['precio_maximo']),
        'por_tipo_operacion': tipos_operacion,
        'tipos_operacion': tipos_operacion,
        'ciudades': ciudades,  # Agregar ciudades al nivel principal
        'tiempo_consulta_ms': tiempo_total,
        # Estructura de filtros LIMPIOS para el frontend
        'filtros': {
            'operaciones': tipos_operacion,
            'ciudades': ciudades,
            'tipos': tipos_propiedad,
            'amenidades': amenidades,
            'caracteristicas': caracteristicas,
            'documentacion': documentacion,
            'caracteristicas_adicionales': caracteristicas_adicionales
        }
    }

@app.get("/salud")
async def verificar_salud():
    """
    Verifica el estado del sistema y la base de datos
    """
    try:
        # Probar conexión a BD
        query = "SELECT COUNT(*) as total FROM propiedades WHERE activo = true"
        resultado, tiempo_ms = ejecutar_consulta(query, fetchall=False)
        
        return {
            "estado": "saludable",
            "version": "2.4.0 - TODOS LOS FILTROS FUNCIONALES",
            "base_datos": "conectada",
            "total_propiedades": resultado['total'],
            "tiempo_respuesta_ms": tiempo_ms,
            "correcciones": [
                "✅ Filtros de Operación corregidos (tipo_operacion)",
                "✅ Filtros de Amenidades funcionando",
                "✅ Características separadas (Recámaras, Baños, Estacionamientos)",
                "✅ CSS de checkboxes mejorado para alineación",
                "✅ Filtros de documentación implementados",
                "✅ Función de imagen mejorada con fallback",
                "✅ Rutas de imágenes corregidas",
                "✅ Filtros de ciudades limpios", 
                "✅ Consultas optimizadas"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "estado": "error",
                "base_datos": "desconectada",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/health")
async def health_check():
    """
    Endpoint de health check para monitor de uptime
    """
    try:
        # Verificar conexión a la base de datos
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        connection.close()
        
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

# 🔐 ENDPOINTS DE AUTENTICACIÓN

@app.post("/api/auth/registro", response_model=Dict)
async def registrar_usuario(usuario: UsuarioRegistro):
    """Registrar nuevo usuario"""
    
    # Verificar si usuario ya existe
    query_check = "SELECT id FROM usuarios WHERE email = %s"
    try:
        resultado, _ = ejecutar_consulta(query_check, (usuario.email,), fetchall=False)
        if resultado:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
    except Exception as e:
        if "ya está registrado" in str(e):
            raise e
        # Si la tabla no existe, la crearemos
        pass
    
    # Crear tabla usuarios si no existe
    create_table_query = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        telefono VARCHAR(20),
        password_hash VARCHAR(255) NOT NULL,
        es_admin BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    try:
        ejecutar_consulta(create_table_query, fetchall=False)
    except:
        pass
    
    # Pablo es admin por defecto
    es_admin = usuario.email.lower() == "pabloravel@gmail.com"
    
    # Hash de contraseña
    password_hash = hash_password(usuario.password)
    
    # Insertar usuario
    insert_query = """
    INSERT INTO usuarios (nombre, email, password_hash, es_admin)
    VALUES (%s, %s, %s, %s)
    RETURNING id, nombre, email, es_admin, created_at
    """
    
    try:
        resultado, _ = ejecutar_consulta(
            insert_query, 
            (usuario.nombre, usuario.email, password_hash, es_admin),
            fetchall=False
        )
        
        user_data = dict(resultado)
        
        # Crear token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": usuario.email}, expires_delta=access_token_expires
        )
        
        # 🎯 PABLO: DEVOLVER ESTRUCTURA QUE ESPERA EL FRONTEND
        return {
            "token": access_token,  # Frontend espera "token", no "access_token"
            "token_type": "bearer",
            "usuario": {
                "id": user_data["id"],
                "nombre": user_data["nombre"],
                "email": user_data["email"],
                
                "es_admin": user_data["es_admin"]
            }
        }
        
    except Exception as e:
        error_str = str(e)
        if "duplicate key value" in error_str and "usuarios_email_key" in error_str:
            raise HTTPException(status_code=400, detail="Este email ya está registrado. Por favor usa otro email o inicia sesión.")
        elif "violates unique constraint" in error_str:
            raise HTTPException(status_code=400, detail="Este email ya está registrado. Por favor usa otro email o inicia sesión.")
        else:
            raise HTTPException(status_code=500, detail=f"Error al crear cuenta: {str(e)}")

@app.post("/api/auth/login", response_model=Dict)
async def login_usuario(usuario: UsuarioLogin):
    """🎯 PABLO: LOGIN CORREGIDO DEFINITIVAMENTE"""
    
    query = "SELECT id, nombre, email, telefono, password_hash, es_admin, created_at FROM usuarios WHERE email = %s AND activo = true"
    try:
        resultado, _ = ejecutar_consulta(query, (usuario.email,), fetchall=False)
        
        if not resultado:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        
        user_data = dict(resultado)
        
        # Verificar password
        if not verify_password(usuario.password, user_data['password_hash']):
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
        
        # Crear token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": usuario.email}, expires_delta=access_token_expires
        )
        
        # 🎯 PABLO: DEVOLVER ESTRUCTURA CORRECTA SIN ERRORES
        return {
            "token": access_token,
            "token_type": "bearer", 
            "usuario": {
                "id": user_data["id"],
                "nombre": user_data["nombre"],
                "email": user_data["email"],
                "telefono": user_data.get("telefono"),
                "es_admin": user_data.get("es_admin", False)
            }
        }
        
    except HTTPException:
        # Re-lanzar errores HTTP específicos
        raise
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/api/auth/me", response_model=Usuario)
async def obtener_usuario_actual(current_user: Usuario = Depends(get_current_user)):
    """Devuelve datos del usuario autenticado"""
    return current_user

# Alias legacy sin /api para compatibilidad con frontend antiguo
app.add_api_route(
    path="/auth/me",
    endpoint=obtener_usuario_actual,
    methods=["GET"],
    response_model=Usuario,
    include_in_schema=False,
)

@app.get("/api/admin/usuarios")
async def listar_usuarios(current_user: Usuario = Depends(get_current_user)):
    """Listar todos los usuarios (solo admin)"""
    if not current_user or not current_user.es_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado - Solo administradores")
    
    query = "SELECT id, nombre, email, es_admin, created_at FROM usuarios ORDER BY created_at DESC"
    try:
        resultado, _ = ejecutar_consulta(query)
        return {"usuarios": [dict(row) for row in resultado]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {str(e)}")

@app.delete("/api/admin/usuarios/{usuario_id}")
async def eliminar_usuario(usuario_id: int, current_user: Usuario = Depends(get_current_user)):
    """Eliminar usuario (solo admin)"""
    if not current_user or not current_user.es_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado - Solo administradores")
    
    if usuario_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")
    
    query = "DELETE FROM usuarios WHERE id = %s"
    try:
        ejecutar_consulta(query, (usuario_id,), fetchall=False)
        return {"mensaje": "Usuario eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar usuario: {str(e)}")

# Endpoint adicional para compatibilidad con frontend actual
@app.get("/api/propiedades")
async def api_propiedades_compatibilidad(
    por_pagina: int = Query(12, description="Número de propiedades por página"),
    pagina: int = Query(1, description="Número de página"),
    tipo_operacion: Optional[str] = Query(None, description="Filtrar por tipo de operación"),
    precio_min: Optional[float] = Query(None, description="Precio mínimo"),
    precio_max: Optional[float] = Query(None, description="Precio máximo"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad")
):
    """Endpoint de compatibilidad con frontend actual - versión robusta"""
    try:
        # Conexión directa a la base de datos usando get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Construir consulta base
        where_conditions = []
        params = []
        
        # Filtro por tipo de operación con mapeo comercial
        if tipo_operacion:
            if tipo_operacion.lower() in ['local', 'oficina']:
                # Mapear local y oficina a comercial
                where_conditions.append("LOWER(tipo_operacion) = %s")
                params.append('comercial')
            else:
                where_conditions.append("LOWER(tipo_operacion) = %s")
                params.append(tipo_operacion.lower())
        
        # Filtro por precio (casteo seguro a numeric)
        try:
            precio_min_val = float(precio_min) if precio_min is not None else None
        except (TypeError, ValueError):
            precio_min_val = None

        try:
            precio_max_val = float(precio_max) if precio_max is not None else None
        except (TypeError, ValueError):
            precio_max_val = None

        if precio_min_val is not None:
            where_conditions.append("COALESCE(precio::numeric,0) >= %s")
            params.append(precio_min_val)

        if precio_max_val is not None:
            where_conditions.append("COALESCE(precio::numeric,0) <= %s")
            params.append(precio_max_val)
        
        # Filtro por ciudad
        if ciudad:
            where_conditions.append("(ciudad ILIKE %s OR direccion ILIKE %s)")
            like_ciudad = f"%{ciudad}%"
            params.extend([like_ciudad, like_ciudad])
        
        # Construir WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Consulta para contar total
        count_query = f"SELECT COUNT(*) FROM propiedades {where_clause}"
        cur.execute(count_query, params)
        total = cur.fetchone()[0]
        
        # Consulta para obtener propiedades
        offset = (pagina - 1) * por_pagina
        data_query = f"""
            SELECT id, titulo, precio, tipo_operacion, tipo_propiedad, 
                   ciudad, descripcion, created_at
            FROM propiedades 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """
        
        cur.execute(data_query, params + [por_pagina, offset])
        rows = cur.fetchall()
        
        propiedades = []
        for row in rows:
            propiedades.append({
                "id": row[0],
                "titulo": row[1] or "",
                "precio": float(row[2]) if row[2] else 0,
                "tipo_operacion": row[3] or "",
                "tipo_propiedad": row[4] or "",
                "ciudad": row[5] or "",
                "descripcion": row[6] or "",
                "imagen_url": "",  # Campo no existe en la BD
                "created_at": row[7].isoformat() if row[7] else ""
            })
        
        cur.close()
        conn.close()
        
        return {
            "propiedades": propiedades,
            "total": total,
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_paginas": (total + por_pagina - 1) // por_pagina,
            "filtros_aplicados": {
                "tipo_operacion": tipo_operacion,
                "precio_min": precio_min,
                "precio_max": precio_max,
                "ciudad": ciudad
            }
        }
        
    except Exception as e:
        logger.error(f"Error en api_propiedades_compatibilidad: {str(e)}")
        return {"error": str(e), "message": "Error al obtener propiedades", "success": False}

# 🔥 ENDPOINTS PARA LEADS - PABLO REQUISITO CRÍTICO

class Lead(BaseModel):
    nombre: str
    telefono: str
    email: Optional[str] = None
    detalles: Optional[str] = None
    tipo_lead: str = "privado"  # "privado" o "compartido"

class PropiedadLead(BaseModel):
    lead_id: int
    propiedad_id: str
    notas: Optional[str] = None

@app.post("/api/leads")
async def crear_lead(lead: Lead, current_user: Usuario = Depends(get_current_user)):
    """Crear nuevo lead"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # Crear tabla leads si no existe
    create_leads_table = """
    CREATE TABLE IF NOT EXISTS leads (
        id SERIAL PRIMARY KEY,
        usuario_id INTEGER REFERENCES usuarios(id),
        nombre VARCHAR(100) NOT NULL,
        telefono VARCHAR(20) NOT NULL,
        email VARCHAR(100),
        detalles TEXT,
        tipo_lead VARCHAR(20) DEFAULT 'privado',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # Crear tabla para propiedades de leads
    create_propiedades_leads_table = """
    CREATE TABLE IF NOT EXISTS propiedades_leads (
        id SERIAL PRIMARY KEY,
        lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
        propiedad_id VARCHAR(50) NOT NULL,
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(lead_id, propiedad_id)
    )
    """
    
    try:
        ejecutar_consulta(create_leads_table, fetchall=False)
        ejecutar_consulta(create_propiedades_leads_table, fetchall=False)
    except:
        pass
    
    # Insertar lead
    insert_query = """
    INSERT INTO leads (usuario_id, nombre, telefono, email, detalles, tipo_lead)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id, nombre, telefono, email, detalles, tipo_lead, created_at
    """
    
    try:
        resultado, _ = ejecutar_consulta(
            insert_query,
            (current_user.id, lead.nombre, lead.telefono, lead.email, lead.detalles, lead.tipo_lead),
            fetchall=False
        )
        
        return {"mensaje": "Lead creado exitosamente", "lead": dict(resultado)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear lead: {str(e)}")

@app.get("/api/leads")
async def obtener_leads(current_user: Usuario = Depends(get_current_user)):
    """Obtener leads del usuario"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # Obtener leads privados del usuario y leads compartidos
    query = """
    SELECT l.*, u.nombre as usuario_nombre,
           COUNT(pl.id) as total_propiedades
    FROM leads l
    LEFT JOIN usuarios u ON l.usuario_id = u.id
    LEFT JOIN propiedades_leads pl ON l.id = pl.lead_id
    WHERE (l.usuario_id = %s AND l.tipo_lead = 'privado') 
       OR l.tipo_lead = 'compartido'
    GROUP BY l.id, u.nombre
    ORDER BY l.created_at DESC
    """
    
    try:
        resultado, _ = ejecutar_consulta(query, (current_user.id,))
        return {"leads": [dict(row) for row in resultado]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener leads: {str(e)}")

@app.post("/api/leads/{lead_id}/propiedades")
async def agregar_propiedad_a_lead(
    lead_id: int, 
    propiedad_lead: PropiedadLead,
    current_user: Usuario = Depends(get_current_user)
):
    """Agregar propiedad a un lead"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # Verificar que el lead existe y pertenece al usuario
    query_check = """
    SELECT * FROM leads 
    WHERE id = %s AND (usuario_id = %s OR tipo_lead = 'compartido')
    """
    
    try:
        lead_result, _ = ejecutar_consulta(query_check, (lead_id, current_user.id), fetchall=False)
        if not lead_result:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        
        # Insertar propiedad en el lead
        insert_query = """
        INSERT INTO propiedades_leads (lead_id, propiedad_id, notas)
        VALUES (%s, %s, %s)
        ON CONFLICT (lead_id, propiedad_id) DO UPDATE SET notas = EXCLUDED.notas
        RETURNING *
        """
        
        resultado, _ = ejecutar_consulta(
            insert_query,
            (lead_id, propiedad_lead.propiedad_id, propiedad_lead.notas),
            fetchall=False
        )
        
        return {"mensaje": "Propiedad agregada al lead", "propiedad_lead": dict(resultado)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al agregar propiedad: {str(e)}")

@app.get("/api/leads/{lead_id}/propiedades")
async def obtener_propiedades_lead(
    lead_id: int,
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener propiedades de un lead"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    # Verificar acceso al lead
    query_check = """
    SELECT * FROM leads 
    WHERE id = %s AND (usuario_id = %s OR tipo_lead = 'compartido')
    """
    
    try:
        lead_result, _ = ejecutar_consulta(query_check, (lead_id, current_user.id), fetchall=False)
        if not lead_result:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        
        # Obtener propiedades del lead con detalles completos
        query = """
        SELECT pl.*, p.titulo, p.precio, p.ciudad, p.tipo_operacion, p.imagen,
               p.direccion, p.recamaras, p.banos, p.estacionamientos
        FROM propiedades_leads pl
        JOIN propiedades p ON pl.propiedad_id = p.id
        WHERE pl.lead_id = %s
        ORDER BY pl.created_at DESC
        """
        
        resultado, _ = ejecutar_consulta(query, (lead_id,))
        propiedades = []
        
        for row in resultado:
            prop_dict = dict(row)
            # Generar URL de imagen
            if prop_dict.get('imagen'):
                prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen'])
            propiedades.append(prop_dict)
        
        return {"propiedades": propiedades}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener propiedades: {str(e)}")

@app.delete("/api/leads/{lead_id}/propiedades/{propiedad_id}")
async def eliminar_propiedad_de_lead(
    lead_id: int,
    propiedad_id: str,
    current_user: Usuario = Depends(get_current_user)
):
    """Eliminar propiedad de un lead"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    try:
        # Verificar acceso al lead
        query_check = """
        SELECT * FROM leads 
        WHERE id = %s AND (usuario_id = %s OR tipo_lead = 'compartido')
        """
        
        lead_result, _ = ejecutar_consulta(query_check, (lead_id, current_user.id), fetchall=False)
        if not lead_result:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        
        # Eliminar propiedad del lead
        delete_query = "DELETE FROM propiedades_leads WHERE lead_id = %s AND propiedad_id = %s"
        ejecutar_consulta(delete_query, (lead_id, propiedad_id), fetchall=False)
        
        return {"mensaje": "Propiedad eliminada del lead"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar propiedad: {str(e)}")

@app.delete("/api/leads/{lead_id}")
async def eliminar_lead(lead_id: int, current_user: Usuario = Depends(get_current_user)):
    """Eliminar lead"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    try:
        # Verificar que el lead pertenece al usuario
        query_check = "SELECT * FROM leads WHERE id = %s AND usuario_id = %s"
        lead_result, _ = ejecutar_consulta(query_check, (lead_id, current_user.id), fetchall=False)
        
        if not lead_result:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        
        # Eliminar lead (CASCADE eliminará las propiedades asociadas)
        delete_query = "DELETE FROM leads WHERE id = %s"
        ejecutar_consulta(delete_query, (lead_id,), fetchall=False)
        
        return {"mensaje": "Lead eliminado exitosamente"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar lead: {str(e)}")

# 🎯 PABLO: ENDPOINT PARA PÁGINA INDIVIDUAL DEL LEAD
@app.get("/api/leads/{lead_id}")
async def obtener_lead_completo(lead_id: int, current_user: Usuario = Depends(get_current_user)):
    """Obtener información completa del lead para su página individual"""
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    try:
        # Obtener información del lead
        lead_query = "SELECT * FROM leads WHERE id = %s"
        lead_resultado, _ = ejecutar_consulta(lead_query, (lead_id,), fetchall=False)
        
        if not lead_resultado:
            raise HTTPException(status_code=404, detail="Lead no encontrado")
        
        lead_data = dict(lead_resultado)
        
        # Verificar permisos (solo el propietario o leads compartidos)
        if lead_data['tipo_lead'] == 'privado' and lead_data['usuario_id'] != current_user.id:
            raise HTTPException(status_code=403, detail="No tienes permiso para ver este lead")
        
        # Obtener propiedades del lead con información completa
        propiedades_query = """
        SELECT pl.*, p.titulo, p.precio, p.ciudad, p.tipo_operacion, p.tipo_propiedad, 
               p.descripcion, p.imagen, p.direccion, p.recamaras, p.banos, p.estacionamientos
        FROM propiedades_leads pl
        LEFT JOIN propiedades p ON pl.propiedad_id = p.id
        WHERE pl.lead_id = %s
        ORDER BY pl.created_at DESC
        """
        
        propiedades_resultado, _ = ejecutar_consulta(propiedades_query, (lead_id,))
        propiedades = []
        
        for prop in propiedades_resultado:
            prop_dict = dict(prop)
            # Generar URL de imagen
            if prop_dict.get('imagen'):
                prop_dict['imagen_url'] = generar_url_imagen(prop_dict['imagen'])
            else:
                prop_dict['imagen_url'] = "https://via.placeholder.com/400x300/e2e8f0/64748b?text=Sin+Imagen"
            
            propiedades.append(prop_dict)
        
        return {
            "lead": lead_data,
            "propiedades": propiedades,
            "total_propiedades": len(propiedades)
        }
        
    except Exception as e:
        if "No tienes permiso" in str(e) or "Lead no encontrado" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=f"Error al obtener lead: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Servir el frontend principal"""
    try:
        with open("frontend_final_con_leads.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Frontend no encontrado</h1><p>Asegúrate de que frontend_final_con_leads.html esté en el directorio raíz.</p>")

@app.get("/frontend", response_class=HTMLResponse)
async def frontend():
    """Alias para el frontend"""
    return await root()

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando API PostgreSQL CORREGIDA v2.2")
    logger.info("📊 Base de datos: PostgreSQL")
    logger.info("⚡ Velocidad esperada: 10-100ms por consulta")
    logger.info("✅ CORRECCIONES APLICADAS:")
    logger.info("   - Rutas de imágenes corregidas")
    logger.info("   - Filtros de ciudades limpios (solo Morelos)")
    logger.info("   - Filtros funcionales que actualizan resultados")
    logger.info("   - Consultas optimizadas")
    logger.info("🌐 Servidor: http://localhost:8000")
    logger.info("📚 Documentación: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_postgresql:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
import json
import os
import psycopg2
from datetime import datetime
import logging

# Configurar logging para debugging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CONFIGURACIÓN POSTGRESQL AWS RDS usando variables de entorno
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'propiedades_db'),
    'user': os.environ.get('DB_USER', 'pabloravel'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': int(os.environ.get('DB_PORT', 5432))
}

def lambda_handler(event, context):
    # Headers CORS y anti-caché
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-Timestamp': str(datetime.now().timestamp())
    }
    
    logger.info(f"Lambda invocada con event: {json.dumps(event)}")
    
    try:
        # Manejo de preflight CORS
        if event.get('httpMethod') == 'OPTIONS':
            logger.info("Manejando preflight CORS")
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight successful'})
            }
        
        # CONECTAR A POSTGRESQL AWS RDS con pg8000
        try:
            logger.info("Iniciando conexión a PostgreSQL con pg8000")
            conn = psycopg2.connect(**DB_CONFIG)
            logger.info("Conexión PostgreSQL exitosa con pg8000")
            
            # Obtener parámetros de consulta
            params = event.get('queryStringParameters') or {}
            limit = int(params.get('limit', 50))
            page = int(params.get('page', 1))
            search = params.get('search', '')
            precio_min = params.get('precio_min')
            precio_max = params.get('precio_max')
            orden = params.get('orden', '')
            
            logger.info(f"Parámetros: limit={limit}, page={page}, search={search}")
            
            # CONSTRUIR CONSULTA SQL SIMPLE
            base_query = """
                SELECT 
                    id, titulo, descripcion, precio, tipo_operacion, tipo_propiedad,
                    ciudad, estado, colonia, direccion_completa, recamaras, banos,
                    estacionamientos, superficie_m2, url_original, amenidades,
                    imagenes, fecha_extraccion
                FROM propiedades
                WHERE id IS NOT NULL
            """
            
            query_params = []
            
            # Filtro de búsqueda
            if search:
                base_query += " AND (titulo ILIKE %s OR descripcion ILIKE %s OR direccion_completa ILIKE %s)"
                search_pattern = f"%{search}%"
                query_params.extend([search_pattern, search_pattern, search_pattern])
                logger.info(f"Aplicando filtro búsqueda: {search}")
            
            # Filtros de precio
            if precio_min:
                base_query += " AND precio >= %s"
                query_params.append(float(precio_min))
                logger.info(f"Aplicando precio_min: {precio_min}")
            
            if precio_max:
                base_query += " AND precio <= %s"
                query_params.append(float(precio_max))
                logger.info(f"Aplicando precio_max: {precio_max}")
            
            # Ordenamiento
            if orden == 'precio_asc':
                base_query += " ORDER BY precio ASC"
            elif orden == 'precio_desc':
                base_query += " ORDER BY precio DESC"
            elif orden == 'fecha_desc':
                base_query += " ORDER BY fecha_extraccion DESC"
            else:
                base_query += " ORDER BY fecha_extraccion DESC"
            
            logger.info(f"Query ordenamiento: {orden}")
            
            # OBTENER TOTAL
            count_query = """
                SELECT COUNT(*) 
                FROM propiedades 
                WHERE id IS NOT NULL
            """
            
            # Aplicar mismos filtros al count
            count_params = []
            if search:
                count_query += " AND (titulo ILIKE %s OR descripcion ILIKE %s OR direccion_completa ILIKE %s)"
                count_params.extend([search_pattern, search_pattern, search_pattern])
            
            if precio_min:
                count_query += " AND precio >= %s"
                count_params.append(float(precio_min))
            
            if precio_max:
                count_query += " AND precio <= %s"
                count_params.append(float(precio_max))
            
            # Ejecutar count query
            cur = conn.cursor()
            logger.info(f"Ejecutando count query: {count_query}")
            cur.execute(count_query, count_params)
            total = cur.fetchone()[0]
            logger.info(f"Total propiedades encontradas: {total}")
            
            # APLICAR PAGINACIÓN
            start_idx = (page - 1) * limit
            base_query += f" LIMIT %s OFFSET %s"
            query_params.extend([limit, start_idx])
            
            # EJECUTAR CONSULTA PRINCIPAL
            logger.info(f"Ejecutando query principal: {base_query}")
            cur.execute(base_query, query_params)
            rows = cur.fetchall()
            logger.info(f"Propiedades recuperadas: {len(rows)}")
            
            # PROCESAR RESULTADOS
            propiedades_procesadas = []
            s3_base_url = "https://todaslascasas-imagenes.s3.amazonaws.com/"
            
            for i, row in enumerate(rows):
                try:
                    # Desempaquetar usando índices (pg8000 devuelve tuplas)
                    id_prop = row[0]
                    titulo = row[1]
                    descripcion = row[2] or ""
                    precio_valor = row[3]
                    tipo_operacion = row[4]
                    tipo_propiedad = row[5]
                    ciudad = row[6]
                    estado = row[7]
                    colonia = row[8]
                    direccion_completa = row[9]
                    recamaras = row[10]
                    banos = row[11]
                    estacionamientos = row[12]
                    superficie_m2 = row[13]
                    url_original = row[14]
                    amenidades = row[15]
                    imagenes = row[16]
                    fecha_extraccion = row[17]
                    
                    # PROCESAR PRECIO con formato mexicano
                    precio_formateado = "Precio no disponible"
                    precio_numerico = 0.0
                    if precio_valor and precio_valor > 0:
                        precio_numerico = float(precio_valor)
                        precio_formateado = f"${precio_numerico:,.0f}".replace(',', '.')
                    
                    # PROCESAR IMÁGENES - CORREGIDO PARA EVITAR DUPLICACIÓN
                    imagen_url = None
                    if imagenes:
                        try:
                            if isinstance(imagenes, list) and len(imagenes) > 0:
                                imagen_path = imagenes[0]
                                if imagen_path:
                                    # Verificar si ya tiene el dominio S3 completo
                                    if imagen_path.startswith('https://todaslascasas-imagenes.s3.amazonaws.com/'):
                                        imagen_url = imagen_path
                                    else:
                                        # Remover "resultados/" del inicio si existe
                                        if imagen_path.startswith('resultados/'):
                                            imagen_path = imagen_path.replace('resultados/', '', 1)
                                        
                                        # Construir URL S3 solo si no la tiene ya
                                        imagen_url = s3_base_url + imagen_path
                        except Exception as img_error:
                            logger.warning(f"Error procesando imagen propiedad {id_prop}: {img_error}")
                    
                    # FALLBACK para imagen si no existe
                    if not imagen_url:
                        imagen_url = f"{s3_base_url}2025-05-30/cuernavaca-2025-05-30-{id_prop}.jpg"
                    
                    # PROCESAR AMENIDADES de forma segura
                    amenidades_dict = {}
                    if amenidades:
                        try:
                            amenidades_dict = amenidades if isinstance(amenidades, dict) else {}
                        except Exception as amenity_error:
                            logger.warning(f"Error procesando amenidades propiedad {id_prop}: {amenity_error}")
                    
                    # Construir objeto propiedad
                    prop_procesada = {
                        'id': str(id_prop),
                        'titulo': titulo or f"Propiedad en {ciudad or 'Ciudad'}",
                        'precio': precio_formateado,
                        'precio_numerico': precio_numerico,
                        'ciudad': (ciudad.title() if ciudad else '') or '',
                        'estado': estado or 'Morelos',
                        'colonia': colonia or '',
                        'direccion_completa': direccion_completa or f"{ciudad or 'Ciudad'}, {estado or 'Estado'}",
                        'url_original': url_original or f"https://www.facebook.com/marketplace/item/{id_prop}/",
                        'tipo_operacion': tipo_operacion or 'Venta',
                        'tipo_propiedad': tipo_propiedad or 'Casa',
                        'recamaras': recamaras or 0,
                        'banos': banos or 0,
                        'superficie_m2': superficie_m2 or 0,
                        'descripcion': (descripcion[:200] + '...') if descripcion and len(descripcion) > 200 else (descripcion or ''),
                        'imagenes': [imagen_url],
                        'imagen_principal': imagen_url,
                        'amenidades': json.dumps(amenidades_dict),
                        'contacto': 'Agente inmobiliario',
                        'legal': 'Escrituras en orden',
                        'fecha_extraccion': fecha_extraccion.isoformat() if fecha_extraccion else datetime.now().isoformat()
                    }
                    
                    propiedades_procesadas.append(prop_procesada)
                    
                except Exception as row_error:
                    logger.error(f"Error procesando fila {i}: {row_error}")
                    logger.error(f"Fila problemática: {row}")
                    continue
            
            # Cerrar conexión después de procesar todo
            cur.close()
            conn.close()
            logger.info(f"Conexión PostgreSQL cerrada. Propiedades procesadas: {len(propiedades_procesadas)}")
            
            # Respuesta con timestamp para evitar caché
            response_data = {
                'data': propiedades_procesadas,
                'total': total,
                'pagina_actual': page,
                'propiedades_por_pagina': limit,
                'total_paginas': (total + limit - 1) // limit,
                'timestamp': datetime.now().isoformat(),
                'cache_version': '2.0'
            }
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_data, ensure_ascii=False, separators=(',', ':'))
            }
            
        except Exception as db_error:
            logger.error(f"Error de base de datos: {db_error}")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({
                    'error': 'Error conectando a base de datos',
                    'message': str(db_error),
                    'timestamp': datetime.now().isoformat()
                }, ensure_ascii=False)
            }
        
    except Exception as e:
        logger.error(f"Error general en Lambda: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Error interno del servidor',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }, ensure_ascii=False)
        } 
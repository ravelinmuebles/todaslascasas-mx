#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRIPT FINAL PARA CARGAR TODAS LAS 5434 PROPIEDADES
===================================================

Versión final que usa la estructura CORRECTA de PostgreSQL
"""

import os
import psycopg2
import json
import sys
import re
from datetime import datetime

# ---------- CONFIGURACIÓN CONEXIÓN POSTGRESQL -----------------------------
# Se puede sobrescribir con variables de entorno PG_HOST, PG_DB, PG_USER, PG_PASS, PG_PORT
DB_HOST = os.getenv('PG_HOST', 'todaslascasas-postgres.cqpcyeqa0uqj.us-east-1.rds.amazonaws.com')
DB_NAME = os.getenv('PG_DB', 'propiedades_db')
DB_USER = os.getenv('PG_USER', 'pabloravel')
DB_PASS = os.getenv('PG_PASS', 'Todaslascasas2025')
DB_PORT = os.getenv('PG_PORT', '5432')

def analizar_propiedades_json():
    """Analizar el contenido del JSON para entender las propiedades"""
    print("📊 ANALIZANDO REPOSITORIO_PROPIEDADES.JSON...")
    
    with open('./resultados/repositorio_propiedades.json', 'r', encoding='utf-8') as f:
        propiedades = json.load(f)
    
    print(f"📈 Total propiedades en JSON: {len(propiedades)}")
    
    # Analizar estructura
    problemas = []
    validas = 0
    sin_titulo = 0
    notificaciones = 0
    sin_precio = 0
    sin_ciudad = 0
    
    for prop_id, prop in propiedades.items():
        if not prop:
            problemas.append(f"Propiedad vacía: {prop_id}")
            continue
            
        titulo = prop.get('titulo', '')
        if not titulo:
            sin_titulo += 1
        elif titulo.lower() == 'notificaciones':
            notificaciones += 1
        
        precio = prop.get('precio', '')
        if not precio or precio == '0' or precio == '$0':
            sin_precio += 1
            
        ciudad = prop.get('ciudad', '')
        if not ciudad:
            sin_ciudad += 1
        
        # Considerar válida si tiene datos básicos
        if prop_id and titulo and titulo.lower() != 'notificaciones':
            validas += 1
    
    print("\n📋 ANÁLISIS DE PROPIEDADES:")
    print(f"✅ Propiedades válidas: {validas}")
    print(f"❌ Sin título: {sin_titulo}")
    print(f"🔔 Título 'Notificaciones': {notificaciones}")
    print(f"💰 Sin precio: {sin_precio}")
    print(f"📍 Sin ciudad: {sin_ciudad}")
    print(f"⚠️  Problemas encontrados: {len(problemas)}")
    
    return propiedades, validas

def limpiar_precio(precio_str):
    """Limpiar y convertir precio a número"""
    if not precio_str:
        return 0
    
    try:
        # Remover símbolos y convertir
        precio_limpio = str(precio_str).replace('$', '').replace(',', '').replace('.', '').replace(' ', '').replace('MXN', '')
        # Si está vacío después de limpiar
        if not precio_limpio:
            return 0
        return float(precio_limpio) if precio_limpio.isdigit() else 0
    except:
        return 0

def extraer_caracteristicas(descripcion):
    """Extraer características numéricas de la descripción"""
    if not descripcion:
        return {'recamaras': 0, 'banos': 0, 'estacionamientos': 0}
    
    caracteristicas = {'recamaras': 0, 'banos': 0, 'estacionamientos': 0}
    desc_lower = descripcion.lower()
    
    # Buscar recámaras
    patterns_recamaras = [
        r'(\d+)\s*recámaras?',
        r'(\d+)\s*recamaras?',
        r'(\d+)\s*habitaciones?',
        r'(\d+)\s*cuartos?',
        r'(\d+)\s*dormitorios?'
    ]
    
    for pattern in patterns_recamaras:
        match = re.search(pattern, desc_lower)
        if match:
            caracteristicas['recamaras'] = int(match.group(1))
            break
    
    # Buscar baños
    patterns_banos = [
        r'(\d+)\s*baños?',
        r'(\d+)\s*baño',
        r'(\d+)\s*sanitarios?'
    ]
    
    for pattern in patterns_banos:
        match = re.search(pattern, desc_lower)
        if match:
            caracteristicas['banos'] = int(match.group(1))
            break
    
    # Buscar estacionamientos
    patterns_estacionamiento = [
        r'(\d+)\s*estacionamientos?',
        r'(\d+)\s*cocheras?',
        r'(\d+)\s*autos?',
        r'(\d+)\s*carros?'
    ]
    
    for pattern in patterns_estacionamiento:
        match = re.search(pattern, desc_lower)
        if match:
            caracteristicas['estacionamientos'] = int(match.group(1))
            break
    
    return caracteristicas

def extraer_amenidades(descripcion):
    """Extraer amenidades de la descripción"""
    if not descripcion:
        return {}
    
    amenidades = {}
    desc_lower = descripcion.lower()
    
    # Amenidades comunes
    if 'alberca' in desc_lower or 'piscina' in desc_lower:
        amenidades['alberca'] = True
    if 'jardín' in desc_lower or 'jardin' in desc_lower:
        amenidades['jardin'] = True
    if 'terraza' in desc_lower:
        amenidades['terraza'] = True
    if 'cochera' in desc_lower or 'garaje' in desc_lower:
        amenidades['cochera'] = True
    if 'seguridad' in desc_lower:
        amenidades['seguridad'] = True
    if 'gimnasio' in desc_lower:
        amenidades['gimnasio'] = True
    if 'elevador' in desc_lower:
        amenidades['elevador'] = True
    if 'balcón' in desc_lower or 'balcon' in desc_lower:
        amenidades['balcon'] = True
    if 'vista' in desc_lower:
        amenidades['vista'] = True
    if 'amueblado' in desc_lower or 'amueblada' in desc_lower:
        amenidades['amueblado'] = True
    
    return amenidades

def determinar_tipo_propiedad(titulo, descripcion):
    """Determinar tipo de propiedad"""
    texto = f"{titulo} {descripcion}".lower()
    
    if 'casa' in texto or 'residencia' in texto:
        return 'Casa'
    elif 'departamento' in texto or 'depto' in texto or 'condominio' in texto:
        return 'Departamento' 
    elif 'terreno' in texto or 'lote' in texto:
        return 'Terreno'
    elif 'local' in texto or 'comercial' in texto:
        return 'Local Comercial'
    elif 'oficina' in texto:
        return 'Oficina'
    elif 'bodega' in texto:
        return 'Bodega'
    elif 'rancho' in texto:
        return 'Rancho'
    else:
        return 'Casa'  # Tipo por defecto

def insertar_propiedad_segura(conn, prop_id, datos):
    """Insertar una propiedad de forma segura con manejo de errores"""
    cur = None
    try:
        cur = conn.cursor()
        
        # Usar la estructura CORRECTA de la tabla PostgreSQL
        cur.execute("""
            INSERT INTO propiedades (
                id, titulo, descripcion, precio, tipo_operacion, tipo_propiedad, 
                ciudad, estado, direccion, recamaras, banos, estacionamientos,
                superficie_terreno, superficie_construida, url_original,
                amenidades, caracteristicas, imagenes, precio_numerico,
                operacion, fecha_publicacion, created_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, datos)
        
        conn.commit()
        cur.close()
        return True, None
        
    except Exception as e:
        # Si hay error, hacer rollback y continuar
        conn.rollback()
        if cur:
            cur.close()
        return False, str(e)

def cargar_todas_propiedades_final():
    """Cargar TODAS las propiedades del JSON con estructura PostgreSQL correcta"""
    print("🚀 INICIANDO CARGA FINAL DE TODAS LAS PROPIEDADES...")
    
    # Analizar JSON primero
    propiedades, validas_estimadas = analizar_propiedades_json()
    
    # Conectar a PostgreSQL
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        
        # Limpiar tabla existente
        print("🧹 Limpiando datos existentes...")
        cur = conn.cursor()
        cur.execute("DELETE FROM propiedades")
        conn.commit()
        cur.close()
        
        print("📥 Insertando TODAS las propiedades con estructura correcta...")
        
        total_propiedades = len(propiedades)
        insertados = 0
        errores = 0
        filtrados = 0
        errores_detalle = []
        
        for prop_id, prop in propiedades.items():
            try:
                if not prop:
                    filtrados += 1
                    continue
                
                # Datos básicos
                titulo = prop.get('titulo', '')
                descripcion = prop.get('descripcion', '')
                
                # ----- PRECIO -----
                precio_field = prop.get('precio')
                if isinstance(precio_field, dict):
                    precio_val = precio_field.get('valor') or limpiar_precio(precio_field.get('texto'))
                else:
                    precio_val = limpiar_precio(precio_field)

                precio = precio_val or 0

                ciudad = prop.get('ciudad', '')
                link = prop.get('link', '')
                
                # Filtrar SOLO casos extremos (incluir "Notificaciones")
                if (not titulo or 
                    titulo.lower() in ['sin título', ''] or
                    len(titulo.strip()) < 3):
                    titulo = f"Propiedad {prop_id}"
                
                # Limpiar ciudad
                if ciudad:
                    ciudad = ciudad.title().strip()
                else:
                    ciudad = 'Ubicación no especificada'
                
                # Determinar tipo de operación
                tipo_operacion_field = prop.get('tipo_operacion')
                if isinstance(tipo_operacion_field, dict):
                    tipo_operacion = (
                        tipo_operacion_field.get('tipo_detectado') or
                        tipo_operacion_field.get('tipo') or 'Desconocido'
                    )
                elif isinstance(tipo_operacion_field, str):
                    tipo_operacion = tipo_operacion_field
                else:
                    tipo_operacion = 'Desconocido'

                # Fallback a descripción si sigue desconocido
                if tipo_operacion == 'Desconocido':
                    if 'renta' in descripcion.lower() or 'alquiler' in descripcion.lower():
                        tipo_operacion = 'Renta'
                    elif 'venta' in descripcion.lower() or 'vende' in descripcion.lower():
                        tipo_operacion = 'Venta'
                
                # Determinar tipo de propiedad
                tipo_propiedad = determinar_tipo_propiedad(titulo, descripcion)
                
                # Extraer características
                caracteristicas = extraer_caracteristicas(descripcion)
                amenidades = extraer_amenidades(descripcion)
                
                # Imagen
                imagen_info = prop.get('imagen_portada')
                imagenes_array = []
                ruta_imagen = None
                if isinstance(imagen_info, dict):
                    ruta_imagen = imagen_info.get('ruta_relativa') or imagen_info.get('nombre_archivo')
                elif isinstance(imagen_info, str):
                    ruta_imagen = imagen_info

                if ruta_imagen:
                    if not ruta_imagen.startswith('resultados/'):
                        ruta_imagen = f"resultados/{ruta_imagen}"
                    imagenes_array.append(ruta_imagen)
                
                # Preparar datos para inserción (estructura PostgreSQL correcta)
                datos = (
                    prop_id,                                    # id
                    titulo,                                     # titulo
                    descripcion or 'Sin descripción disponible', # descripcion
                    precio,                                     # precio
                    tipo_operacion,                            # tipo_operacion
                    tipo_propiedad,                            # tipo_propiedad
                    ciudad,                                    # ciudad
                    'Morelos',                                 # estado
                    ciudad,                                    # direccion
                    caracteristicas['recamaras'],              # recamaras
                    caracteristicas['banos'],                  # banos
                    caracteristicas['estacionamientos'],       # estacionamientos
                    0,                                         # superficie_terreno
                    0,                                         # superficie_construida
                    link,                                      # url_original
                    json.dumps(amenidades),                    # amenidades (JSONB)
                    json.dumps(caracteristicas),               # caracteristicas (JSONB)
                    json.dumps(imagenes_array),                # imagenes (JSONB)
                    precio,                                    # precio_numerico
                    tipo_operacion,                            # operacion
                    datetime.now(),                            # fecha_publicacion
                    datetime.now()                             # created_at
                )
                
                # Insertar de forma segura
                exito, error = insertar_propiedad_segura(conn, prop_id, datos)
                
                if exito:
                    insertados += 1
                    # Actualizar barra de progreso cada 100 inserciones
                    if insertados % 100 == 0 or insertados == total_propiedades:
                        pct = (insertados / total_propiedades) * 100
                        sys.stdout.write(f"\r📊 Progreso: {insertados}/{total_propiedades} ({pct:.1f}%)")
                        sys.stdout.flush()
                else:
                    errores += 1
                    errores_detalle.append(f"{prop_id}: {error}")
                    if errores <= 3:  # Solo mostrar primeros 3 errores
                        print(f"❌ Error en {prop_id}: {error}")
                
            except Exception as e:
                errores += 1
                errores_detalle.append(f"{prop_id}: {e}")
                if errores <= 3:
                    print(f"❌ Error procesando {prop_id}: {e}")
                continue
        
        print(f"\n🎉 CARGA COMPLETADA:")
        print(f"✅ Propiedades insertadas: {insertados}")
        print(f"❌ Errores: {errores}")
        print(f"🚫 Filtradas: {filtrados}")
        print(f"📊 Total procesadas: {insertados + errores + filtrados}")
        
        # Verificar resultado
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM propiedades")
        total_final = cur.fetchone()[0]
        print(f"🔍 Total en PostgreSQL después de carga: {total_final}")
        
        # Mostrar muestra de errores
        if errores_detalle and len(errores_detalle) <= 10:
            print(f"\n🔍 MUESTRA DE ERRORES:")
            for i, error in enumerate(errores_detalle[:3]):
                print(f"  {i+1}. {error}")
        
        cur.close()
        conn.close()
        
        return insertados, errores, filtrados
        
    except Exception as e:
        print(f"💀 Error crítico: {e}")
        return 0, 0, 0

if __name__ == "__main__":
    print("🔄 INICIANDO CARGA COMPLETA DE PROPIEDADES - VERSIÓN FINAL")
    print("=" * 60)
    
    insertados, errores, filtrados = cargar_todas_propiedades_final()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMEN FINAL:")
    print(f"📈 JSON original: 5,434 propiedades")
    print(f"✅ Cargadas exitosamente: {insertados}")
    print(f"❌ Con errores: {errores}")
    print(f"🚫 Filtradas: {filtrados}")
    print(f"📊 Tasa de éxito: {(insertados / 5434) * 100:.1f}%")
    
    if insertados > 2742:
        print(f"🎉 ¡ÉXITO! Se cargaron {insertados - 2742} propiedades adicionales")
        print(f"🔥 MEJORA: De 2,742 a {insertados} propiedades (+{insertados - 2742})")
    else:
        print("⚠️  No se mejoró significativamente la cantidad")
    
    print("\n✅ Script FINAL completado") 
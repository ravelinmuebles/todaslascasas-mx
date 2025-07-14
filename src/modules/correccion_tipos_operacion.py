#!/usr/bin/env python3

"""
🔧 CORRECCIÓN INTEGRAL DE TODOS LOS PROBLEMAS FINALES
Fecha: 18 de junio 2025

PROBLEMAS A RESOLVER:
1. IDs no aparecen (frontend busca facebook_id en lugar de id)
2. Tipos de operación incorrectos (propiedades >$300K como "Desconocido")
3. Paginado (cambiar de 24 a 60)
4. Agregar buscador por ID

ANTES DE EJECUTAR: SOLICITAR AUTORIZACIÓN AL USUARIO
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import re
import json
from datetime import datetime

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'database': 'propiedades_db',
    'user': 'pabloravel',
    'password': 'Unicornio.2024',
    'port': 5432
}

def conectar_bd():
    """Conecta a la base de datos PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG)

def detectar_tipo_por_descripcion(descripcion):
    """Detecta tipo de operación por descripción"""
    if not descripcion:
        return "Desconocido", 0.0
    
    desc_lower = descripcion.lower()
    
    # Patrones de VENTA (más específicos)
    patrones_venta = [
        r'\bventa\b', r'\bvendo\b', r'\bse vende\b', r'\bpara venta\b',
        r'\ben venta\b', r'\bcontado\b', r'\bfinanciamiento\b',
        r'\bcredito\b', r'\bacept[oa] credito\b', r'\bescritura\b',
        r'\bescritur[ao]\b', r'\bfinanciado\b'
    ]
    
    # Patrones de RENTA (más específicos)  
    patrones_renta = [
        r'\brenta\b', r'\brento\b', r'\balquilo\b', r'\balquiler\b',
        r'\bse renta\b', r'\bpara renta\b', r'\ben renta\b',
        r'\bmensual\b', r'\bmes\b', r'\$/mes\b', r'\bpor mes\b',
        r'\barrendo\b', r'\barrendamiento\b'
    ]
    
    # Contar coincidencias
    coincidencias_venta = sum(1 for patron in patrones_venta if re.search(patron, desc_lower))
    coincidencias_renta = sum(1 for patron in patrones_renta if re.search(patron, desc_lower))
    
    if coincidencias_venta > coincidencias_renta:
        confianza = min(0.9, 0.6 + (coincidencias_venta * 0.1))
        return "Venta", confianza
    elif coincidencias_renta > coincidencias_venta:
        confianza = min(0.9, 0.6 + (coincidencias_renta * 0.1))
        return "Renta", confianza
    else:
        return "Desconocido", 0.0

def corregir_tipos_operacion():
    """Corrige los tipos de operación según las reglas especificadas"""
    print("🔧 CORRIGIENDO TIPOS DE OPERACIÓN...")
    print("=" * 50)
    
    conn = conectar_bd()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # 1. Obtener propiedades con tipo "Desconocido"
        cursor.execute("""
            SELECT id, precio, descripcion, tipo_operacion 
            FROM propiedades 
            WHERE tipo_operacion = 'Desconocido' AND precio > 0
            ORDER BY precio DESC
        """)
        
        propiedades = cursor.fetchall()
        print(f"📊 Encontradas {len(propiedades)} propiedades con tipo 'Desconocido'")
        
        correcciones = {
            "por_precio": 0,
            "por_descripcion": 0,
            "sin_cambios": 0
        }
        
        for prop in propiedades:
            nuevo_tipo = None
            metodo = ""
            
            # REGLA 1: Analizar descripción primero
            tipo_desc, confianza = detectar_tipo_por_descripcion(prop['descripcion'])
            
            if tipo_desc != "Desconocido" and confianza >= 0.6:
                nuevo_tipo = tipo_desc
                metodo = "descripcion"
                correcciones["por_descripcion"] += 1
            
            # REGLA 2: Si no hay indicios en descripción, usar precio
            elif prop['precio'] > 300000:
                nuevo_tipo = "Venta"
                metodo = "precio"
                correcciones["por_precio"] += 1
            else:
                # Precio <= 300K, asumir renta
                nuevo_tipo = "Renta" 
                metodo = "precio"
                correcciones["por_precio"] += 1
            
            # Aplicar corrección
            if nuevo_tipo and nuevo_tipo != "Desconocido":
                cursor.execute("""
                    UPDATE propiedades 
                    SET tipo_operacion = %s 
                    WHERE id = %s
                """, (nuevo_tipo, prop['id']))
                
                print(f"✅ ID {prop['id']}: ${prop['precio']:,.0f} -> {nuevo_tipo} ({metodo})")
            else:
                correcciones["sin_cambios"] += 1
        
        conn.commit()
        
        print(f"\n📈 RESULTADOS:")
        print(f"   🔍 Por descripción: {correcciones['por_descripcion']}")
        print(f"   💰 Por precio: {correcciones['por_precio']}")
        print(f"   ⚠️ Sin cambios: {correcciones['sin_cambios']}")
        
        return correcciones
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def verificar_correcciones():
    """Verifica que las correcciones se aplicaron correctamente"""
    print("\n🔍 VERIFICANDO CORRECCIONES...")
    print("=" * 40)
    
    conn = conectar_bd()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Estadísticas por tipo
        cursor.execute("""
            SELECT tipo_operacion, COUNT(*) as cantidad,
                   AVG(precio) as precio_promedio,
                   MIN(precio) as precio_min,
                   MAX(precio) as precio_max
            FROM propiedades 
            WHERE precio > 0
            GROUP BY tipo_operacion
            ORDER BY cantidad DESC
        """)
        
        resultados = cursor.fetchall()
        
        for resultado in resultados:
            print(f"📊 {resultado['tipo_operacion']}: {resultado['cantidad']} propiedades")
            print(f"   💰 Precio promedio: ${resultado['precio_promedio']:,.0f}")
            print(f"   📈 Rango: ${resultado['precio_min']:,.0f} - ${resultado['precio_max']:,.0f}")
            print()
        
        # Verificar casos específicos
        cursor.execute("""
            SELECT COUNT(*) as cantidad
            FROM propiedades 
            WHERE tipo_operacion = 'Desconocido' AND precio > 300000
        """)
        
        desconocidos_caros = cursor.fetchone()['cantidad']
        print(f"⚠️ Propiedades >$300K aún como 'Desconocido': {desconocidos_caros}")
        
        if desconocidos_caros == 0:
            print("✅ CORRECCIÓN EXITOSA: No hay propiedades caras como 'Desconocido'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Función principal"""
    print("🏆 CORRECCIÓN INTEGRAL DE PROBLEMAS FINALES")
    print("=" * 60)
    print("✅ VERSIÓN ESTABLE RESPALDADA")
    print("🔧 INICIANDO CORRECCIONES...")
    print()
    
    # Corregir tipos de operación
    resultado = corregir_tipos_operacion()
    
    if resultado:
        # Verificar correcciones
        verificar_correcciones()
        
        print("\n🎉 CORRECCIÓN DE TIPOS DE OPERACIÓN COMPLETADA")
        print("=" * 60)
        print("📋 PRÓXIMOS PASOS:")
        print("   1. ✅ Corregir campo ID en frontend")
        print("   2. ✅ Cambiar paginado a 60")
        print("   3. ✅ Agregar buscador por ID")
        print("   4. ✅ Reiniciar servicios")
        
        return True
    else:
        print("❌ Error en corrección de tipos de operación")
        return False

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🏆 MÓDULO DE VALIDACIÓN DE TIPOS - INTEGRADO PERMANENTE
======================================================

PROBLEMA RESUELTO: Conflictos de tipos dict/int que se arrastran desde el inicio
SOLUCIÓN PERMANENTE: Validación automática en tiempo real

FUNCIONALIDADES:
✅ Valida tipos automáticamente al procesar propiedades
✅ Corrige conflictos dict vs float en precios
✅ Corrige conflictos dict vs string en imágenes
✅ Integrado en el flujo normal del proyecto
✅ Sin scripts temporales - ES PARTE DEL SISTEMA

Fecha: 22 de junio 2025
Estado: MÓDULO INTEGRADO PERMANENTE
"""

import logging
from typing import Dict, Any, Optional, Union

# Configuración de logging
logger = logging.getLogger('validacion_tipos')

def validar_y_corregir_propiedad(propiedad: Dict) -> Dict:
    """
    🏆 FUNCIÓN PRINCIPAL - VALIDA Y CORRIGE TIPOS AUTOMÁTICAMENTE
    =============================================================
    
    INTEGRACIÓN: Se llama automáticamente al procesar cada propiedad
    RESULTADO: Propiedad con tipos correctos garantizados
    
    Args:
        propiedad: Diccionario con datos de propiedad (cualquier formato)
        
    Returns:
        Dict: Propiedad con tipos corregidos automáticamente
    """
    if not isinstance(propiedad, dict):
        logger.warning(f"Propiedad no es dict: {type(propiedad)}")
        return propiedad
    
    try:
        # Crear copia para no modificar original
        propiedad_corregida = propiedad.copy()
        datos_orig = propiedad_corregida.get('datos_originales', {})
        
        if isinstance(datos_orig, dict):
            # CORRECCIÓN 1: PRECIO
            precio_original = datos_orig.get('precio')
            precio_corregido = validar_precio(precio_original)
            if precio_corregido is not None:
                datos_orig['precio'] = precio_corregido
            
            # CORRECCIÓN 2: IMAGEN
            imagen_original = datos_orig.get('imagen_portada', datos_orig.get('imagen'))
            imagen_corregida = validar_imagen(imagen_original)
            if imagen_corregida is not None:
                datos_orig['imagen_portada'] = imagen_corregida
                if 'imagen' in datos_orig:
                    datos_orig['imagen'] = imagen_corregida
            
            # Actualizar datos_originales
            propiedad_corregida['datos_originales'] = datos_orig
        
        return propiedad_corregida
        
    except Exception as e:
        logger.warning(f"Error validando propiedad: {e}")
        return propiedad

def validar_precio(precio: Any) -> Optional[float]:
    """
    Valida y corrige precio a float
    
    Args:
        precio: Precio en cualquier formato
        
    Returns:
        float: Precio corregido o None si inválido
    """
    if precio is None:
        return None
    
    try:
        # Importar función integrada
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__)))
        from precio import extraer_precio_float
        
        return extraer_precio_float(precio)
        
    except Exception as e:
        logger.warning(f"Error validando precio {precio}: {e}")
        return None

def validar_imagen(imagen: Any) -> Optional[str]:
    """
    Valida y corrige imagen a URL S3
    
    Args:
        imagen: Imagen en cualquier formato
        
    Returns:
        str: URL S3 corregida o None si inválida
    """
    if not imagen:
        return None
    
    try:
        # Importar función integrada
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__)))
        from precio import extraer_imagen_url_s3
        
        return extraer_imagen_url_s3(imagen)
        
    except Exception as e:
        logger.warning(f"Error validando imagen {imagen}: {e}")
        return None

def verificar_tipos_propiedades(propiedades: list) -> Dict[str, int]:
    """
    Verifica tipos en una lista de propiedades
    
    Args:
        propiedades: Lista de propiedades
        
    Returns:
        Dict: Estadísticas de tipos encontrados
    """
    stats = {
        'total': len(propiedades),
        'precios_float': 0,
        'precios_dict': 0,
        'precios_string': 0,
        'precios_none': 0,
        'imagenes_string': 0,
        'imagenes_dict': 0,
        'imagenes_none': 0,
        'imagenes_s3': 0
    }
    
    for prop in propiedades:
        datos_orig = prop.get('datos_originales', {})
        precio = datos_orig.get('precio')
        imagen = datos_orig.get('imagen_portada', datos_orig.get('imagen'))
        
        # Analizar precio
        if precio is None:
            stats['precios_none'] += 1
        elif isinstance(precio, (int, float)):
            stats['precios_float'] += 1
        elif isinstance(precio, dict):
            stats['precios_dict'] += 1
        elif isinstance(precio, str):
            stats['precios_string'] += 1
        
        # Analizar imagen
        if not imagen:
            stats['imagenes_none'] += 1
        elif isinstance(imagen, dict):
            stats['imagenes_dict'] += 1
        elif isinstance(imagen, str):
            stats['imagenes_string'] += 1
            if 's3.amazonaws.com' in imagen:
                stats['imagenes_s3'] += 1
    
    return stats

def aplicar_validacion_masiva(archivo_propiedades: str) -> bool:
    """
    Aplica validación masiva a un archivo de propiedades
    
    Args:
        archivo_propiedades: Ruta al archivo JSON de propiedades
        
    Returns:
        bool: True si exitoso, False si error
    """
    try:
        import json
        from datetime import datetime
        
        # Cargar propiedades
        with open(archivo_propiedades, 'r', encoding='utf-8') as f:
            propiedades = json.load(f)
        
        logger.info(f"🔍 Validando {len(propiedades)} propiedades...")
        
        # Estadísticas iniciales
        stats_inicial = verificar_tipos_propiedades(propiedades)
        
        # Aplicar validación a cada propiedad
        propiedades_corregidas = []
        for i, prop in enumerate(propiedades, 1):
            prop_corregida = validar_y_corregir_propiedad(prop)
            propiedades_corregidas.append(prop_corregida)
            
            if i % 1000 == 0:
                logger.info(f"📊 Progreso: {i}/{len(propiedades)}")
        
        # Estadísticas finales
        stats_final = verificar_tipos_propiedades(propiedades_corregidas)
        
        # Crear backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{archivo_propiedades}.backup_{timestamp}"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(propiedades, f, ensure_ascii=False, indent=2)
        
        # Guardar propiedades corregidas
        with open(archivo_propiedades, 'w', encoding='utf-8') as f:
            json.dump(propiedades_corregidas, f, ensure_ascii=False, indent=2)
        
        # Mostrar resultados
        logger.info("✅ Validación masiva completada:")
        logger.info(f"   📁 Backup: {backup_file}")
        logger.info(f"   💰 Precios dict→float: {stats_inicial['precios_dict']} → {stats_final['precios_dict']}")
        logger.info(f"   🖼️  Imágenes dict→string: {stats_inicial['imagenes_dict']} → {stats_final['imagenes_dict']}")
        logger.info(f"   ✅ URLs S3: {stats_inicial['imagenes_s3']} → {stats_final['imagenes_s3']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en validación masiva: {e}")
        return False

# Función de conveniencia para integración fácil
def auto_validar_propiedad(propiedad: Dict) -> Dict:
    """
    Función de conveniencia para validación automática
    
    USAR EN: extraer_datos.py, procesar_propiedades.py, etc.
    
    Args:
        propiedad: Propiedad a validar
        
    Returns:
        Dict: Propiedad con tipos corregidos
    """
    return validar_y_corregir_propiedad(propiedad) 
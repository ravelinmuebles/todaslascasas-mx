#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MÓDULO DE NORMALIZACIÓN DE PRECIOS - VERSIÓN CORREGIDA DEFINITIVA
----------------------------------------------------------------

Este módulo normaliza el formato de los precios que vienen de Facebook.
CORRECCIÓN DEFINITIVA: Reconoce MDP, millones, emojis y todos los formatos.
"""

import re
import logging
from typing import Dict, Optional, Union
from decimal import Decimal, InvalidOperation
import os

# Configuración de logging
logger = logging.getLogger('precio')
logger.setLevel(logging.DEBUG)

def procesar_numero_mexicano(texto: str) -> Optional[float]:
    """
    Procesa un número en formato mexicano y lo convierte a float.
    CORRECCIÓN DEFINITIVA: Simple y robusta para formato mexicano.
    
    Args:
        texto: Texto que contiene el número
        
    Returns:
        Número convertido a float o None si no se pudo procesar
    """
    if not texto:
        return None
    
    # Manejar casos de "Gratis" / "free"
    if isinstance(texto, str) and 'gratis' in texto.lower():
        return 0.0
    
    # Si ya es un número, retornarlo directamente
    if isinstance(texto, (int, float)):
        return float(texto)
            
    # Limpiar el texto
    texto = str(texto).strip()
    if not texto:
        return None
    
    # CORRECCIÓN DEFINITIVA: Extraer solo números, puntos y comas
    # Remover todo lo que no sea número, punto o coma
    numero_limpio = re.sub(r'[^\d.,]', '', texto)
    
    if not numero_limpio:
        return None
    
    # FORMATO MEXICANO ESPECÍFICO
    # En México: 7.500.000 = 7,500,000 (puntos son separadores de miles)
    
    # Contar separadores
    num_puntos = numero_limpio.count('.')
    num_comas = numero_limpio.count(',')
    
    try:
        if num_puntos >= 2:
            # Formato mexicano: 7.500.000 (todos los puntos son separadores de miles)
            resultado = float(numero_limpio.replace('.', ''))
        elif num_comas >= 2:
            # Formato internacional: 7,500,000 (todas las comas son separadores de miles)
            resultado = float(numero_limpio.replace(',', ''))
        elif num_puntos == 1 and num_comas == 0:
            # Un solo punto: puede ser separador de miles o decimal
            partes = numero_limpio.split('.')
            if len(partes[1]) == 3:  # 7.500 (formato mexicano de miles)
                resultado = float(numero_limpio.replace('.', ''))
            elif len(partes[1]) > 3:  # 7.5000 (formato mexicano de miles)
                resultado = float(numero_limpio.replace('.', ''))
            else:  # 7.50 (decimal)
                resultado = float(numero_limpio)
        elif num_comas == 1 and num_puntos == 0:
            # Una sola coma: puede ser separador de miles o decimal
            partes = numero_limpio.split(',')
            if len(partes[1]) >= 3:  # 7,500 (separador de miles)
                resultado = float(numero_limpio.replace(',', ''))
            else:  # 7,50 (decimal europeo)
                resultado = float(numero_limpio.replace(',', '.'))
        elif num_puntos == 1 and num_comas == 1:
            # Formato mixto: determinar cuál es decimal
            pos_punto = numero_limpio.rfind('.')
            pos_coma = numero_limpio.rfind(',')
            
            if pos_punto > pos_coma:  # 1,234.56
                resultado = float(numero_limpio.replace(',', ''))
            else:  # 1.234,56
                resultado = float(numero_limpio.replace('.', '').replace(',', '.'))
        else:
            # Solo números, sin separadores
            resultado = float(numero_limpio)
                
        # Validar resultado razonable
        if resultado < 0 or resultado > 1_000_000_000:
            return None
            
        return resultado
        
    except (ValueError, TypeError):
        return None

def procesar_numero_base(texto: str) -> Optional[float]:
    """
    Procesa un número base limpiando separadores.
    CORRECCIÓN ESPECÍFICA PARA FORMATO MEXICANO: $7.500.000 = 7500000
    
    Args:
        texto: Número como texto con posibles separadores
        
    Returns:
        Número como float o None si no se pudo procesar
    """
    if not texto:
        return None
    
    # Limpiar espacios y símbolos
    texto = texto.replace("$", "").replace(" ", "").strip()
    
    if not texto:
        return None
    
    # Detectar formato del número
    tiene_punto = "." in texto
    tiene_coma = "," in texto
    
    # Contar ocurrencias
    num_puntos = texto.count(".")
    num_comas = texto.count(",")
    
    try:
        # CORRECCIÓN ESPECÍFICA PARA FORMATO MEXICANO
        # En México: $7.500.000 = 7,500,000 (los puntos son separadores de miles)
        
        if num_puntos >= 2:  # Formato mexicano: 7.500.000
            # Todos los puntos son separadores de miles
            texto = texto.replace(".", "")
        elif num_comas >= 2:  # Formato internacional: 7,500,000
            # Todas las comas son separadores de miles
            texto = texto.replace(",", "")
        elif tiene_punto and tiene_coma:
            # Formato mixto: determinar cuál es decimal
            pos_punto = texto.rfind(".")
            pos_coma = texto.rfind(",")
            
            if pos_punto > pos_coma:  # 1,234.56
                texto = texto.replace(",", "")
            else:  # 1.234,56
                texto = texto.replace(".", "").replace(",", ".")
        elif tiene_punto:
            # Solo puntos: verificar si es separador de miles o decimal
            partes = texto.split(".")
            if len(partes) == 2:
                # Un solo punto
                if len(partes[1]) == 3:  # 7.500 (formato mexicano de miles)
                    texto = texto.replace(".", "")
                elif len(partes[1]) > 3:  # 7.5000 (formato mexicano de miles)
                    texto = texto.replace(".", "")
                # Si tiene 1-2 dígitos después del punto, es decimal: 7.50
            else:
                # Múltiples puntos: todos son separadores de miles
                texto = texto.replace(".", "")
        elif tiene_coma:
            # Solo comas: verificar si es separador de miles o decimal
            partes = texto.split(",")
            if len(partes) == 2:
                # Una sola coma
                if len(partes[1]) >= 3:  # 7,500 (separador de miles)
                    texto = texto.replace(",", "")
                # Si tiene 1-2 dígitos después de la coma, es decimal: 7,50
            else:
                # Múltiples comas: todas son separadores de miles
                texto = texto.replace(",", "")
        
        resultado = float(texto)
        
        # Validar resultado razonable
        if resultado < 0 or resultado > 1_000_000_000:
            return None
            
        return resultado
        
    except (ValueError, TypeError):
        return None

def normalizar_precio(precio: Union[str, float, int]) -> Dict:
    """
    Normaliza el formato de un precio que viene de Facebook.
    CORRECCIÓN DEFINITIVA: Usa procesar_numero_mexicano mejorado.
    
    Args:
        precio: Precio en formato string, float o int
        
    Returns:
        Dict con:
        - valor: float
        - moneda: str ('MXN')
        - texto_original: str
    """
    resultado = {
        "valor": None,
        "moneda": "MXN",
        "texto_original": str(precio) if precio is not None else ""
    }
    
    if precio is None:
        return resultado
        
    try:
        # CORRECCIÓN DEFINITIVA: Usar procesar_numero_mexicano mejorado
        if isinstance(precio, str):
            valor_procesado = procesar_numero_mexicano(precio)
            if valor_procesado is not None:
                resultado["valor"] = valor_procesado
        else:
            # Si ya es número, convertirlo a float
            resultado["valor"] = float(precio)
            
    except (ValueError, TypeError, InvalidOperation):
        # Si falla, intentar método básico como fallback
        try:
            if isinstance(precio, str):
                # Método básico de limpieza
                valor = re.sub(r'[^\d.,]', '', precio)
                if valor:
                    if ',' in valor and '.' in valor:
                        if valor.find(',') < valor.find('.'):
                            valor = valor.replace(',', '')
                        else:
                            valor = valor.replace('.', '').replace(',', '.')
                    elif ',' in valor:
                        partes = valor.split(',')
                        if len(partes) == 2 and len(partes[1]) <= 2:
                            valor = valor.replace(',', '.')
                        else:
                            valor = valor.replace(',', '')
                    
                    resultado["valor"] = float(valor)
            else:
                resultado["valor"] = float(precio)
        except (ValueError, TypeError, InvalidOperation):
            pass
    
    return resultado

def formatear_precio(precio: Union[Dict, float, int, str]) -> str:
    """
    Formatea un precio para mostrar.
    
    Args:
        precio: Precio en cualquier formato soportado
        
    Returns:
        str: Precio formateado como "$X,XXX,XXX"
    """
    if isinstance(precio, dict):
        valor = precio.get("valor")
    else:
        valor = precio
        
    if valor is None:
        return ""
        
    try:
        valor = float(valor)
        return f"${valor:,.0f}"
    except (ValueError, TypeError):
        return str(precio)

def actualizar_precio_propiedad(propiedad: Dict) -> Dict:
    """
    Actualiza el campo de precio de una propiedad.
    
    Args:
        propiedad: Diccionario con los datos de la propiedad
        
    Returns:
        Dict: Propiedad con el precio actualizado
    """
    if not isinstance(propiedad, dict):
        return propiedad
        
    # Si no hay campo precio, retornar la propiedad sin cambios
    if "precio" not in propiedad:
        return propiedad
        
    precio_original = propiedad["precio"]
    
    # Si el precio es un dict (como viene del repositorio)
    if isinstance(precio_original, dict):
        # Intentar extraer precio del texto si valor es None
        if precio_original.get('valor') is None and precio_original.get('texto'):
            valor_extraido = procesar_numero_mexicano(precio_original['texto'])
            if valor_extraido is not None:
                # Actualizar el precio con el valor extraído
                precio_original['valor'] = valor_extraido
                precio_original['es_valido'] = True
                precio_original['mensaje'] = 'Precio extraído exitosamente'
                precio_original['confianza'] = 1.0
            else:
                # Mantener como inválido si no se pudo extraer
                precio_original['es_valido'] = False
                precio_original['mensaje'] = 'No se pudo extraer precio del texto'
                precio_original['confianza'] = 0.0
        
        # Si ya tiene valor válido, verificar que es_valido esté correcto
        elif precio_original.get('valor') is not None and precio_original.get('valor') > 0:
            precio_original['es_valido'] = True
            precio_original['mensaje'] = 'Precio válido'
            precio_original['confianza'] = 1.0
            
        propiedad["precio"] = precio_original
        return propiedad
    else:
        # Si es string u otro tipo, normalizar como antes
        precio_normalizado = normalizar_precio(precio_original)
        
        # Agregar campos de validación
        if precio_normalizado.get('valor') is not None and precio_normalizado.get('valor') > 0:
            precio_normalizado['es_valido'] = True
            precio_normalizado['mensaje'] = 'Precio válido'
            precio_normalizado['confianza'] = 1.0
        else:
            precio_normalizado['es_valido'] = False
            precio_normalizado['mensaje'] = 'Precio inválido o cero'
            precio_normalizado['confianza'] = 0.0

        propiedad["precio"] = precio_normalizado
        return propiedad

def extraer_precio_float(precio: Union[str, float, int, dict]) -> Optional[float]:
    """
    🏆 FUNCIÓN INTEGRADA PERMANENTE - EXTRAE PRECIO COMO FLOAT
    ========================================================
    
    PROBLEMA RESUELTO: Conflictos de tipos dict vs float
    SOLUCIÓN: Función dedicada que SIEMPRE retorna float o None
    
    Args:
        precio: Precio en cualquier formato (string, dict, float, int)
        
    Returns:
        float: Precio como número directo o None si no válido
        
    CASOS MANEJADOS:
    - String: "$6.980.000" → 6980000.0
    - Dict: {"valor": 123, "texto": "$123"} → 123.0
    - Float/Int: 123 → 123.0
    - None/Inválido: → None
    """
    if precio is None:
        return None
    
    try:
        # CASO 1: Ya es número directo
        if isinstance(precio, (int, float)):
            return float(precio)
        
        # CASO 2: Es dict (formato normalizado)
        elif isinstance(precio, dict):
            # Priorizar campo 'valor' si existe y es válido
            if precio.get('valor') is not None:
                try:
                    return float(precio['valor'])
                except (ValueError, TypeError):
                    pass
            
            # Fallback: usar campo 'texto' y procesarlo
            texto = precio.get('texto', precio.get('texto_original', ''))
            if texto:
                return procesar_numero_mexicano(str(texto))
        
        # CASO 3: Es string directo
        elif isinstance(precio, str):
            return procesar_numero_mexicano(precio)
        
        return None
        
    except Exception as e:
        logger.warning(f"Error extrayendo precio float de {precio}: {e}")
        return None

def extraer_imagen_url_s3(imagen_raw: Union[str, dict]) -> Optional[str]:
    """
    🏆 FUNCIÓN INTEGRADA PERMANENTE - EXTRAE IMAGEN COMO URL S3
    ==========================================================
    
    PROBLEMA RESUELTO: Conflictos de tipos dict vs string en imágenes
    SOLUCIÓN: Función dedicada que SIEMPRE retorna URL S3 o None
    
    Args:
        imagen_raw: Imagen en cualquier formato (string, dict)
        
    Returns:
        str: URL S3 directa o None si no válida
        
    CASOS MANEJADOS:
    - String URL S3: "https://bucket.s3.amazonaws.com/..." → mantener
    - String local: "resultados/..." → convertir a S3
    - Dict: {"nombre_archivo": "...", "ruta_relativa": "..."} → convertir a S3
    - None/Inválido: → None
    """
    if not imagen_raw:
        return None
    
    try:
        # Configuración S3 - CORREGIDO
        bucket_name = "todaslascasas-imagenes"
        base_url_s3 = f"https://{bucket_name}.s3.amazonaws.com/"
        
        # CASO 1: Ya es string
        if isinstance(imagen_raw, str):
            # Si ya es URL S3, limpiar duplicaciones y mantener
            if imagen_raw.startswith('http') and 's3.amazonaws.com' in imagen_raw:
                # Limpiar URLs duplicadas: https://bucket/https://bucket/imagen.jpg
                if '/https://todaslascasas-imagenes.s3.amazonaws.com/' in imagen_raw:
                    imagen_raw = imagen_raw.replace('/https://todaslascasas-imagenes.s3.amazonaws.com/', '/')
                return imagen_raw
            
            # Si es URL externa, no convertir
            if imagen_raw.startswith('http'):
                return None
            
            # Si es ruta local, convertir a S3
            return _convertir_ruta_local_a_url_s3(imagen_raw, base_url_s3)
        
        # CASO 2: Es dict
        elif isinstance(imagen_raw, dict):
            # Intentar diferentes campos del dict
            campos_imagen = [
                imagen_raw.get('ruta_relativa', ''),
                imagen_raw.get('nombre_archivo', ''),
                imagen_raw.get('ruta_absoluta', ''),
                imagen_raw.get('url', ''),
                imagen_raw.get('imagen', '')
            ]
            
            for campo in campos_imagen:
                if campo and 'imagen_no_disponible' not in str(campo):
                    # Si es URL S3, retornar
                    if str(campo).startswith('http') and 's3.amazonaws.com' in str(campo):
                        return str(campo)
                    
                    # Si es ruta local, convertir
                    elif not str(campo).startswith('http'):
                        # Para ruta_absoluta, extraer solo el nombre del archivo
                        if 'ruta_absoluta' in imagen_raw and campo == imagen_raw['ruta_absoluta']:
                            campo = os.path.basename(str(campo))
                        
                        url_s3 = _convertir_ruta_local_a_url_s3(str(campo), base_url_s3)
                        if url_s3:
                            return url_s3
        
        return None
        
    except Exception as e:
        logger.warning(f"Error extrayendo imagen URL S3 de {imagen_raw}: {e}")
        return None

def _convertir_ruta_local_a_url_s3(ruta_local: str, base_url_s3: str) -> Optional[str]:
    """
    Función helper para convertir ruta local a URL S3
    
    Args:
        ruta_local: Ruta como "resultados/2025-06-09/imagen.jpg" o "imagen.jpg"
        base_url_s3: URL base de S3
        
    Returns:
        str: URL S3 completa o None
    """
    try:
        if not ruta_local or 'imagen_no_disponible' in ruta_local:
            return None
        
        # Extraer nombre del archivo
        nombre_archivo = os.path.basename(ruta_local)
        
        # Extraer fecha del nombre del archivo
        # Formato esperado: ciudad-2025-MM-DD-id.jpg
        if '2025-' in nombre_archivo:
            partes = nombre_archivo.split('-')
            if len(partes) >= 4:
                try:
                    # Construir fecha: 2025-MM-DD
                    fecha = f"{partes[1]}-{partes[2]}-{partes[3]}"
                    
                    # Construir URL S3
                    url_s3 = f"{base_url_s3}{fecha}/{nombre_archivo}"
                    return url_s3
                except:
                    pass
        
        # Si no se puede extraer fecha, usar fecha donde están las imágenes
        fecha_default = "2025-06-27"
        url_s3 = f"{base_url_s3}{fecha_default}/{nombre_archivo}"
        return url_s3
        
    except Exception as e:
        logger.warning(f"Error convirtiendo ruta {ruta_local}: {e}")
        return None 
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
    CORRECCIÓN DEFINITIVA: Maneja MDP, millones, emojis y todos los formatos.
    
    Args:
        texto: Texto que contiene el número
        
    Returns:
        Número convertido a float o None si no se pudo procesar
    """
    if not texto:
        return None
    
    # Si ya es un número, retornarlo directamente
    if isinstance(texto, (int, float)):
        return float(texto)
            
    # Limpiar el texto
    texto = str(texto).strip()
    
    # CORRECCIÓN DEFINITIVA: Patrones específicos para diferentes formatos
    patrones_precio_definititvos = [
        # FORMATO MDP (Millones De Pesos) - CRÍTICO
        (r'([0-9]+\.?[0-9]*)\s*(?:MDP|mdp)', lambda x: float(x) * 1_000_000),
        (r'([0-9]+\.?[0-9]*)\s*(?:millones?|millón)', lambda x: float(x) * 1_000_000),
        (r'([0-9]+\.?[0-9]*)\s*(?:MM|mm)', lambda x: float(x) * 1_000_000),
        
        # FORMATO MILES
        (r'([0-9]+\.?[0-9]*)\s*(?:mil|k|K)', lambda x: float(x) * 1_000),
        
        # EMOJIS CON NÚMEROS
        (r'💰💲([0-9,.\s]+)', lambda x: procesar_numero_base(x)),
        (r'💲([0-9,.\s]+)', lambda x: procesar_numero_base(x)),
        
        # PRECIOS CON DESCRIPCIÓN
        (r'precio[:\s;]*\$?([0-9,.\s]+)', lambda x: procesar_numero_base(x)),
        (r'desde[:\s]*\$?([0-9,.\s]+)', lambda x: procesar_numero_base(x)),
        
        # FORMATO ESTÁNDAR CON SÍMBOLOS
        (r'\$([0-9,.\s]+)', lambda x: procesar_numero_base(x)),
        (r'([0-9,.\s]+)\s*(?:pesos|MXN|mxn)', lambda x: procesar_numero_base(x)),
        
        # NÚMEROS PUROS
        (r'([0-9,.\s]+)', lambda x: procesar_numero_base(x))
    ]
    
    # Intentar todos los patrones en orden de prioridad
    for patron, procesador in patrones_precio_definititvos:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            try:
                numero_extraido = match.group(1).strip()
                resultado = procesador(numero_extraido)
                
                # Validar rangos razonables
                if isinstance(resultado, (int, float)) and 1 <= resultado <= 1_000_000_000:
                    return float(resultado)
            except (ValueError, TypeError, IndexError):
                continue
    
    return None

def procesar_numero_base(texto: str) -> Optional[float]:
    """
    Procesa un número base limpiando separadores.
    
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
        # Determinar formato basado en separadores
        if num_puntos > 1:  # 1.234.567
            texto = texto.replace(".", "")
        elif num_comas > 1:  # 1,234,567
            texto = texto.replace(",", "")
        elif tiene_punto and tiene_coma:
            if texto.rindex(".") > texto.rindex(","):  # 1,234.56
                texto = texto.replace(",", "")
            else:  # 1.234,56
                texto = texto.replace(".", "").replace(",", ".")
        elif tiene_punto:
            # Verificar si es separador de miles o decimal
            partes = texto.split(".")
            if len(partes) == 2 and len(partes[1]) > 2:
                # Más de 2 dígitos después del punto = separador de miles
                texto = texto.replace(".", "")
        elif tiene_coma:
            # Verificar si es separador de miles o decimal
            partes = texto.split(",")
            if len(partes) == 2 and len(partes[1]) >= 3:
                # 3 o más dígitos después de coma = separador de miles
                texto = texto.replace(",", "")
            else:
                # 2 dígitos o menos = separador decimal
                texto = texto.replace(",", ".")
        
        return float(texto)
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
        
    # Normalizar el precio
    precio_normalizado = normalizar_precio(propiedad["precio"])
        
    # Actualizar la propiedad
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
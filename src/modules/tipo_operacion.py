#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de procesamiento de tipo de operación.
Detecta y corrige tipos de operación basándose ÚNICAMENTE en descripción explícita.

CRITERIOS DEFINITIVOS (según Pablo - 21 junio 2025):
- RENTA: Solo si se menciona explícitamente en descripción O precio incluye "/mes"
- VENTA: Todo lo demás (por defecto)
- NO usar precio como criterio principal para determinar tipo
"""

import logging
import re
from typing import Dict, Tuple

# Configuración de logging
logger = logging.getLogger('tipo_operacion')
logger.setLevel(logging.INFO)

# Patrones EXPLÍCITOS para detección de RENTA
PATRONES_RENTA = [
    r'\brenta\b', r'\brento\b', r'\balquilo\b', r'\balquiler\b',
    r'\bse renta\b', r'\bpara renta\b', r'\ben renta\b',
    r'\bmensual\b', r'\bmes\b', r'\$/mes\b', r'/mes\b',
    r'\barrendo\b', r'\barrendamiento\b', r'\brento\b'
]

# Patrones EXPLÍCITOS para detección de VENTA
PATRONES_VENTA = [
    r'\bventa\b', r'\bvendo\b', r'\bse vende\b', r'\bpara venta\b',
    r'\ben venta\b', r'\bcontado\b', r'\bfinanciamiento\b',
    r'\bcredito\b', r'\boportunidad\b', r'\binversion\b',
    r'\bnegociable\b', r'\bremate\b', r'\burgente\b',
    r'\bpropietario\b', r'\bescritura\b', r'\btitulo\b'
]

def detectar_tipo_por_descripcion(descripcion: str) -> Tuple[str, float]:
    """
    Detecta el tipo de operación basándose ÚNICAMENTE en la descripción.
    
    Args:
        descripcion: Texto de la descripción de la propiedad
        
    Returns:
        Tuple[str, float]: (tipo_detectado, confianza)
    """
    if not descripcion:
        return "desconocido", 0.0
    
    desc_lower = descripcion.lower()
    
    # Contar coincidencias de renta (EXPLÍCITAS)
    coincidencias_renta = 0
    for patron in PATRONES_RENTA:
        if re.search(patron, desc_lower):
            coincidencias_renta += 1
    
    # Contar coincidencias de venta (EXPLÍCITAS)
    coincidencias_venta = 0
    for patron in PATRONES_VENTA:
        if re.search(patron, desc_lower):
            coincidencias_venta += 1
    
    # LÓGICA CORREGIDA: Solo marcar como renta si es EXPLÍCITO
    if coincidencias_renta > 0:
        confianza = min(0.9, 0.7 + (coincidencias_renta * 0.1))
        return "renta", confianza
    elif coincidencias_venta > 0:
        confianza = min(0.9, 0.7 + (coincidencias_venta * 0.1))
        return "venta", confianza
    else:
        # Si no hay indicios explícitos, es VENTA por defecto
        return "venta", 0.5

def detectar_tipo_por_precio(precio_str: str) -> Tuple[str, float]:
    """
    Detecta tipo ÚNICAMENTE si el precio incluye "/mes"
    
    Args:
        precio_str: String del precio
        
    Returns:
        Tuple[str, float]: (tipo_detectado, confianza)
    """
    if not precio_str or not isinstance(precio_str, str):
        return "desconocido", 0.0
    
    # Verificar si incluye "/mes" o indicadores de renta
    if '/mes' in precio_str.lower() or 'mes' in precio_str.lower():
        return "renta", 0.9
    
    return "desconocido", 0.0

def extraer_precio_numerico(precio_raw) -> float:
    """
    Extrae el valor numérico del precio desde diferentes formatos.
    """
    if precio_raw is None:
        return 0.0
    elif isinstance(precio_raw, (int, float)):
        return float(precio_raw)
    elif isinstance(precio_raw, str):
        if not precio_raw.strip():
            return 0.0
        # Limpiar string y extraer número
        precio_limpio = precio_raw.replace('$', '').replace(',', '').replace('.', '').replace('𝟲', '6').replace('𝟵', '9').replace('𝟴', '8').replace('𝟬', '0')
        match = re.search(r'\d+', precio_limpio)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return 0.0
    elif isinstance(precio_raw, dict):
        # Manejar estructura {"texto": "$27.900/mes", "valor": null}
        texto = precio_raw.get('texto', '')
        if texto and isinstance(texto, str):
            # Verificar si es renta por "/mes" en el texto
            return extraer_precio_numerico(texto)
        
        valor = precio_raw.get('valor', 0)
        if valor is None:
            return 0.0
        return float(valor)
    
    return 0.0

def actualizar_tipo_operacion(propiedad: Dict) -> Dict:
    """
    FUNCIÓN CORREGIDA SEGÚN CRITERIOS DE PABLO:
    
    REGLAS DEFINITIVAS:
    1. RENTA: Solo si se menciona explícitamente en descripción O precio incluye "/mes"
    2. VENTA: Todo lo demás (por defecto)
    3. NO usar precio como criterio principal para determinar tipo
    """
    if not isinstance(propiedad, dict):
        return propiedad
    
    # Obtener datos
    tipo_actual = propiedad.get("tipo_operacion", "").lower()
    descripcion = propiedad.get("datos_originales", {}).get("descripcion", "")
    precio_raw = propiedad.get("datos_originales", {}).get("precio", "")
    
    # 1. Verificar si el precio incluye "/mes"
    tipo_por_precio, confianza_precio = detectar_tipo_por_precio(str(precio_raw))
    
    # 2. Verificar descripción
    tipo_por_desc, confianza_desc = detectar_tipo_por_descripcion(descripcion)
    
    # 3. Determinar tipo final según criterios de Pablo
    nuevo_tipo = "venta"  # Por defecto es VENTA
    metodo = "defecto"
    
    # Si precio incluye "/mes" = RENTA (prioridad máxima)
    if tipo_por_precio == "renta":
        nuevo_tipo = "renta"
        metodo = "precio_mensual"
        logger.info(f"RENTA detectada por precio mensual: {precio_raw}")
    
    # Si descripción menciona explícitamente RENTA
    elif tipo_por_desc == "renta" and confianza_desc >= 0.7:
        nuevo_tipo = "renta"
        metodo = "descripcion_explicita"
        logger.info(f"RENTA detectada por descripción explícita")
    
    # Si descripción menciona explícitamente VENTA
    elif tipo_por_desc == "venta" and confianza_desc >= 0.7:
        nuevo_tipo = "venta"
        metodo = "descripcion_venta"
        logger.info(f"VENTA detectada por descripción explícita")
    
    # En todos los demás casos = VENTA por defecto
    else:
        nuevo_tipo = "venta"
        metodo = "venta_por_defecto"
        logger.debug(f"VENTA por defecto (sin indicios explícitos de renta)")
    
    # Actualizar solo si cambió
    if tipo_actual != nuevo_tipo:
        logger.info(f"Cambio: {tipo_actual} -> {nuevo_tipo} (método: {metodo})")
        propiedad["tipo_operacion"] = nuevo_tipo.title()
    
    return propiedad

def corregir_tipos_masivo(propiedades: list) -> dict:
    """
    Corrige tipos de operación de forma masiva.
    """
    estadisticas = {
        "total_procesadas": 0,
        "correcciones": 0,
        "tipos_antes": {},
        "tipos_despues": {},
        "metodos_deteccion": {}
    }
    
    for propiedad in propiedades:
        # Contar tipo antes
        tipo_antes = propiedad.get("tipo_operacion", "desconocido").lower()
        estadisticas["tipos_antes"][tipo_antes] = estadisticas["tipos_antes"].get(tipo_antes, 0) + 1
        
        # Aplicar corrección
        propiedad_corregida = actualizar_tipo_operacion(propiedad)
        
        # Contar tipo después
        tipo_despues = propiedad_corregida.get("tipo_operacion", "desconocido").lower()
        estadisticas["tipos_despues"][tipo_despues] = estadisticas["tipos_despues"].get(tipo_despues, 0) + 1
        
        # Contar corrección si cambió
        if tipo_antes != tipo_despues:
            estadisticas["correcciones"] += 1
        
        estadisticas["total_procesadas"] += 1
    
    return estadisticas

if __name__ == "__main__":
    # Pruebas del módulo
    print("🧪 Probando módulo tipo_operacion CORREGIDO...")
    
    # Casos de prueba con estructura real
    casos_prueba = [
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Casa en renta, 3 recámaras",
                "precio": "$15000"
            }
        },
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Hermosa casa",
                "precio": {"texto": "$27.900/mes", "valor": None}
            }
        },
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Se vende casa en Cuernavaca",
                "precio": "$2500000"
            }
        },
        {
            "tipo_operacion": "",
            "datos_originales": {
                "descripcion": "Hermosa propiedad, excelente ubicación",
                "precio": "$450000"
            }
        }
    ]
    
    for i, caso in enumerate(casos_prueba, 1):
        print(f"\n--- Caso {i} ---")
        resultado = actualizar_tipo_operacion(caso.copy())
        print(f"Descripción: {caso['datos_originales']['descripcion']}")
        print(f"Precio: {caso['datos_originales']['precio']}")
        print(f"Resultado: {resultado['tipo_operacion']}") 
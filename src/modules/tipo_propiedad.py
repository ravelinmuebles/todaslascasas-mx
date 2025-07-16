#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Módulo de procesamiento de tipo de propiedad.
Detecta inteligentemente el tipo de propiedad basándose en descripción y características.

CORRECCIÓN PABLO (21 junio 2025):
- Cuando se mencionan recámaras, niveles, estacionamientos = CASA (no terreno)
- Detección inteligente basada en características específicas
- Prioridad a indicios explícitos en descripción
"""

import logging
import re
from typing import Dict, Optional

# Configuración de logging
logger = logging.getLogger('tipo_propiedad')
logger.setLevel(logging.INFO)

# PATRONES ESPECÍFICOS PARA CADA TIPO DE PROPIEDAD

# PATRONES CASA - Indicios de construcción habitacional
PATRONES_CASA = [
    # Espacios habitacionales (PESO ALTO)
    r'\b(\d+\s*)?(recámara|recamara|dormitorio|habitacion|habitación|cuarto)\b',
    r'\b(\d+\s*)?(baño|baños|bathroom)\b',
    r'\b(\d+\s*)?(nivel|niveles|piso|pisos|planta|plantas)\b',
    r'\b(\d+\s*)?(estacionamiento|garage|garaje|cochera)\b',
    
    # Espacios de casa
    r'\b(sala|comedor|cocina|kitchen|living|estar)\b',
    r'\b(patio|jardín|jardin|terraza|balcón|balcon)\b',
    r'\b(azotea|roof\s*garden|roof)\b',
    
    # Características de construcción
    r'\b(construida|construcción|construccion|edificada)\b',
    r'\b(residencia|vivienda|hogar)\b',
    r'\b(amplia|espaciosa|cómoda|comoda)\b',
    
    # Amenidades de casa
    r'\b(alberca|piscina|pool|jacuzzi)\b',
    r'\b(cisterna|tinaco|gas\s*estacionario)\b'
]

# PATRONES CASA EXPLÍCITOS (mayor peso)
PATRONES_CASA_EXPLICITOS = [
    r'\bcasa\b',
    r'\bhouse\b'
]

# PATRONES DEPARTAMENTO
PATRONES_DEPARTAMENTO = [
    r'\b(departamento|depto|apartment|condominio|condo)\b',
    r'\b(torre|edificio|complejo|unidad)\b',
    r'\b(elevador|ascensor|elevator)\b',
    r'\b(amenidades|gym|gimnasio|roof\s*garden)\b'
]

# PATRONES TERRENO - Solo cuando NO hay indicios de construcción
PATRONES_TERRENO = [
    r'\b(terreno|lote|predio|solar)\b',
    r'\b(metros\s*cuadrados|m2|m²|hectárea|hectarea)\b',
    r'\b(esquina|frente|fondo)\b',
    r'\b(plano|irregular|regular)\b'
]

# PATRONES COMERCIAL
PATRONES_LOCAL = [
    # Singular, plural y frase más común
    r'\b(local|locales)\b',
    r'\blocal\s+comercial(es)?\b',
    r'\b(comercial|negocio|tienda|shop)\b',
    r'\b(restaurante|café|cafe|bar)\b',
    r'\b(consultorio|clínica|clinica|hospital)\b'
]

PATRONES_OFICINA = [
    # Singular y plural, español e inglés
    r'\b(oficina|oficinas|office|offices)\b',
    # Términos corporativos habituales
    r'\b(corporativo|corporativos|ejecutivo|ejecutivos)\b',
    # Despachos y consultorías
    r'\b(consultoría|consultoria|despacho|bufete)\b',
    # Espacios de coworking
    r'\b(coworking|co-working)\b'
]

# Para clasificar como BODEGA requerimos palabras clave específicas de uso industrial / almacenamiento.
# Evitamos que la sola mención de "bodega" (cuartito de guardado) en una casa dispare esta categoría.
PATRONES_BODEGA = [
    # Combinaciones típicas de bodega industrial / nave / almacén
    r'\b(bodega\s+(industrial|comercial|grande|almac[eé]n|log[ií]stica))\b',
    r'\b(nave\s+(industrial|almac[eé]n))\b',
    r'\b(warehouse)\b',
    r'\b(almac[eé]n\s+industrial)\b'
]

def detectar_tipo_por_descripcion(descripcion: str) -> Optional[str]:
    """
    Detecta el tipo de propiedad basándose en la descripción.
    
    Args:
        descripcion: Texto de descripción de la propiedad
        
    Returns:
        str: Tipo de propiedad detectado o None
    """
    if not descripcion:
        return None
    
    desc_lower = descripcion.lower()
    
    # CONTADOR DE COINCIDENCIAS POR TIPO
    puntos_casa = 0
    puntos_casa_explicitos = 0
    puntos_departamento = 0
    puntos_terreno = 0
    puntos_local = 0
    puntos_oficina = 0
    puntos_bodega = 0
    
    # VERIFICAR PATRONES DE CASA EXPLÍCITOS (mayor peso)
    for patron in PATRONES_CASA_EXPLICITOS:
        if re.search(patron, desc_lower):
            puntos_casa_explicitos += 2  # Peso mayor
            logger.debug(f"Patrón CASA EXPLÍCITO encontrado: {patron}")
    
    # VERIFICAR PATRONES DE CASA
    for patron in PATRONES_CASA:
        if re.search(patron, desc_lower):
            puntos_casa += 1
            logger.debug(f"Patrón CASA encontrado: {patron}")
    
    # VERIFICAR PATRONES DE DEPARTAMENTO
    for patron in PATRONES_DEPARTAMENTO:
        if re.search(patron, desc_lower):
            puntos_departamento += 1
            logger.debug(f"Patrón DEPARTAMENTO encontrado: {patron}")
    
    # VERIFICAR PATRONES DE TERRENO (solo si NO hay indicios de construcción)
    for patron in PATRONES_TERRENO:
        if re.search(patron, desc_lower):
            puntos_terreno += 1
            logger.debug(f"Patrón TERRENO encontrado: {patron}")
    
    # VERIFICAR PATRONES COMERCIALES
    for patron in PATRONES_LOCAL:
        if re.search(patron, desc_lower):
            puntos_local += 1
    
    for patron in PATRONES_OFICINA:
        if re.search(patron, desc_lower):
            puntos_oficina += 1
    
    for patron in PATRONES_BODEGA:
        if re.search(patron, desc_lower):
            puntos_bodega += 1
    
    # LÓGICA DE DECISIÓN
    
    total_puntos_casa = puntos_casa + puntos_casa_explicitos
    
    # Si hay indicios de CASA (recámaras, niveles, etc.), es CASA
    if total_puntos_casa >= 1:
        logger.info(f"Detectado como CASA ({total_puntos_casa} indicios: {puntos_casa} normales + {puntos_casa_explicitos} explícitos)")
        return "casa"
    
    # Si hay indicios de DEPARTAMENTO
    if puntos_departamento >= 1:
        logger.info(f"Detectado como DEPARTAMENTO ({puntos_departamento} indicios)")
        return "departamento"
    
    # Comerciales (prioridad: oficina > bodega > local)
    if puntos_oficina >= 1:
        return "oficina"

    if puntos_bodega >= 1:
        return "bodega"

    if puntos_local >= 1:
        return "local"
    
    # Solo es TERRENO si NO hay indicios de construcción Y tiene patrones de terreno
    if puntos_terreno >= 1 and total_puntos_casa == 0 and puntos_departamento == 0:
        logger.info(f"Detectado como TERRENO ({puntos_terreno} indicios, sin construcción)")
        return "terreno"
    
    return None

def actualizar_tipo_propiedad(propiedad: Dict) -> Dict:
    """
    Actualiza el tipo de propiedad usando detección inteligente.
    
    Args:
        propiedad: Diccionario con los datos de la propiedad
        
    Returns:
        Dict: Propiedad con el tipo de propiedad actualizado
    """
    if not isinstance(propiedad, dict):
        return propiedad
    
    # Obtener descripción completa
    descripcion = ""
    titulo = ""
    
    # Extraer texto de diferentes fuentes
    if "titulo" in propiedad:
        titulo = str(propiedad["titulo"])
        descripcion += f" {titulo}"
    
    if "descripcion" in propiedad:
        desc = str(propiedad["descripcion"])
        descripcion += f" {desc}"
    
    # También revisar en datos_originales si existe
    if "datos_originales" in propiedad:
        datos_orig = propiedad["datos_originales"]
        if isinstance(datos_orig, dict):
            if "descripcion" in datos_orig:
                descripcion += f" {datos_orig['descripcion']}"
            if "titulo" in datos_orig:
                descripcion += f" {datos_orig['titulo']}"
    
    # Detectar tipo basándose en descripción
    tipo_detectado = detectar_tipo_por_descripcion(descripcion)
    
    if tipo_detectado:
        # Actualizar el tipo de propiedad
        if "propiedad" in propiedad:
            propiedad["propiedad"]["tipo_propiedad"] = tipo_detectado
        else:
            # Si no existe la estructura, crearla
            if "tipo_propiedad" in propiedad:
                propiedad["tipo_propiedad"] = tipo_detectado
            else:
                propiedad["tipo_propiedad"] = tipo_detectado
        
        logger.info(f"Tipo de propiedad actualizado a: {tipo_detectado}")
    else:
        logger.debug("No se pudo detectar tipo de propiedad específico")
    
    return propiedad

# Función de prueba
if __name__ == "__main__":
    # Casos de prueba
    casos_prueba = [
        {
            "titulo": "Casa con 3 recámaras y 2 baños",
            "descripcion": "Hermosa casa de 2 niveles con 3 recámaras, 2 baños completos, sala, comedor, cocina equipada y 2 lugares de estacionamiento"
        },
        {
            "titulo": "Terreno en venta",
            "descripcion": "Terreno plano de 500 m2 en esquina, ideal para construcción, sin construcción"
        },
        {
            "titulo": "Departamento en torre",
            "descripcion": "Departamento en edificio con elevador, 2 recámaras, amenidades"
        },
        {
            "titulo": "Propiedad con recámaras",
            "descripcion": "Propiedad de 2 niveles con 4 recámaras y estacionamiento"
        }
    ]
    
    for i, caso in enumerate(casos_prueba, 1):
        print(f"\n--- Caso {i} ---")
        print(f"Título: {caso['titulo']}")
        print(f"Descripción: {caso['descripcion']}")
        
        resultado = actualizar_tipo_propiedad(caso)
        tipo_final = resultado.get("tipo_propiedad", "No detectado")
        print(f"Tipo detectado: {tipo_final}") 
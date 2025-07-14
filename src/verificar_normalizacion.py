#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Verificador de Normalización
---------------------------
Este script verifica que los datos se hayan normalizado correctamente,
mostrando estadísticas de los campos normalizados.
"""

import json
import logging
from typing import Dict, List, Any
from collections import Counter

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analizar_precios(propiedades: List[Dict]) -> Dict:
    """Analiza los precios normalizados."""
    stats = {
        "total": len(propiedades),
        "con_precio_valido": 0,
        "rangos": {
            "0-1M": 0,
            "1M-3M": 0,
            "3M-5M": 0,
            "5M+": 0
        },
        "periodos": Counter(),
        "monedas": Counter()
    }
    
    for prop in propiedades:
        precio = prop.get('propiedad', {}).get('precio', {})
        if isinstance(precio, dict) and 'valor' in precio and precio['valor'] is not None and precio.get('es_valido', False):
            stats["con_precio_valido"] += 1
            valor = precio['valor']
            
            # Contar rangos
            if valor < 1_000_000:
                stats["rangos"]["0-1M"] += 1
            elif valor < 3_000_000:
                stats["rangos"]["1M-3M"] += 1
            elif valor < 5_000_000:
                stats["rangos"]["3M-5M"] += 1
            else:
                stats["rangos"]["5M+"] += 1
            
            # Contar periodos y monedas
            stats["periodos"][precio.get('periodo', 'Desconocido')] += 1
            stats["monedas"][precio.get('moneda', 'Desconocido')] += 1
    
    return stats

def analizar_caracteristicas(propiedades: List[Dict]) -> Dict:
    """Analiza las características normalizadas."""
    stats = {
        "total": len(propiedades),
        "con_caracteristicas": 0,
        "recamaras": Counter(),
        "banos": Counter(),
        "estacionamientos": Counter(),
        "niveles": Counter(),
        "superficie": {
            "construida": {"min": float('inf'), "max": 0, "promedio": 0},
            "terreno": {"min": float('inf'), "max": 0, "promedio": 0}
        }
    }
    
    total_construida = 0
    total_terreno = 0
    count_construida = 0
    count_terreno = 0
    
    for prop in propiedades:
        car = prop.get('caracteristicas', {})
        if car:
            stats["con_caracteristicas"] += 1
            
            # Contar recámaras
            if 'recamaras' in car and car['recamaras'] is not None:
                stats["recamaras"][car['recamaras']] += 1
            
            # Contar baños
            if 'banos' in car and car['banos'] is not None:
                stats["banos"][car['banos']] += 1
            
            # Contar estacionamientos
            if 'estacionamientos' in car and car['estacionamientos'] is not None:
                stats["estacionamientos"][car['estacionamientos']] += 1
            
            # Contar niveles
            if 'niveles' in car and car['niveles'] is not None:
                stats["niveles"][car['niveles']] += 1
            
            # Analizar superficies
            if 'superficie_construida' in car and car['superficie_construida'] is not None:
                sup = car['superficie_construida']
                stats["superficie"]["construida"]["min"] = min(stats["superficie"]["construida"]["min"], sup)
                stats["superficie"]["construida"]["max"] = max(stats["superficie"]["construida"]["max"], sup)
                total_construida += sup
                count_construida += 1
            
            if 'superficie_terreno' in car and car['superficie_terreno'] is not None:
                sup = car['superficie_terreno']
                stats["superficie"]["terreno"]["min"] = min(stats["superficie"]["terreno"]["min"], sup)
                stats["superficie"]["terreno"]["max"] = max(stats["superficie"]["terreno"]["max"], sup)
                total_terreno += sup
                count_terreno += 1
    
    # Calcular promedios
    if count_construida > 0:
        stats["superficie"]["construida"]["promedio"] = total_construida / count_construida
    if count_terreno > 0:
        stats["superficie"]["terreno"]["promedio"] = total_terreno / count_terreno
    
    return stats

def analizar_amenidades(propiedades: List[Dict]) -> Dict:
    """Analiza las amenidades normalizadas."""
    stats = {
        "total": len(propiedades),
        "con_amenidades": 0,
        "alberca": 0,
        "jardin": 0,
        "seguridad": 0,
        "areas_comunes": Counter(),
        "adicionales": Counter()
    }
    
    for prop in propiedades:
        amen = prop.get('amenidades', {})
        if amen:
            stats["con_amenidades"] += 1
            
            # Contar booleanos
            if amen.get('alberca'):
                stats["alberca"] += 1
            if amen.get('jardin'):
                stats["jardin"] += 1
            if amen.get('seguridad'):
                stats["seguridad"] += 1
            
            # Contar áreas comunes
            for area in amen.get('areas_comunes', []):
                stats["areas_comunes"][area] += 1
            
            # Contar adicionales
            for adic in amen.get('adicionales', []):
                stats["adicionales"][adic] += 1
    
    return stats

def main():
    """Función principal."""
    # Cargar propiedades normalizadas
    try:
        with open('resultados/propiedades_normalizadas.json', 'r', encoding='utf-8') as f:
            propiedades = json.load(f)
        logger.info(f"Propiedades cargadas: {len(propiedades)}")
    except Exception as e:
        logger.error(f"Error cargando propiedades: {e}")
        return
    
    # Analizar datos
    logger.info("\n=== Análisis de Precios ===")
    stats_precios = analizar_precios(propiedades)
    logger.info(f"Total propiedades: {stats_precios['total']}")
    logger.info(f"Con precio válido: {stats_precios['con_precio_valido']}")
    logger.info("\nRangos de precio:")
    for rango, count in stats_precios['rangos'].items():
        logger.info(f"- {rango}: {count}")
    logger.info("\nPeriodos:")
    for periodo, count in stats_precios['periodos'].most_common():
        logger.info(f"- {periodo}: {count}")
    logger.info("\nMonedas:")
    for moneda, count in stats_precios['monedas'].most_common():
        logger.info(f"- {moneda}: {count}")
    
    logger.info("\n=== Análisis de Características ===")
    stats_car = analizar_caracteristicas(propiedades)
    logger.info(f"Total propiedades: {stats_car['total']}")
    logger.info(f"Con características: {stats_car['con_caracteristicas']}")
    logger.info("\nRecámaras:")
    for rec, count in sorted(stats_car['recamaras'].items()):
        logger.info(f"- {rec}: {count}")
    logger.info("\nBaños:")
    for ban, count in sorted(stats_car['banos'].items()):
        logger.info(f"- {ban}: {count}")
    logger.info("\nEstacionamientos:")
    for est, count in sorted(stats_car['estacionamientos'].items()):
        logger.info(f"- {est}: {count}")
    logger.info("\nNiveles:")
    for niv, count in sorted(stats_car['niveles'].items()):
        logger.info(f"- {niv}: {count}")
    logger.info("\nSuperficie construida:")
    logger.info(f"- Mínima: {stats_car['superficie']['construida']['min']:.1f} m²")
    logger.info(f"- Máxima: {stats_car['superficie']['construida']['max']:.1f} m²")
    logger.info(f"- Promedio: {stats_car['superficie']['construida']['promedio']:.1f} m²")
    logger.info("\nSuperficie terreno:")
    logger.info(f"- Mínima: {stats_car['superficie']['terreno']['min']:.1f} m²")
    logger.info(f"- Máxima: {stats_car['superficie']['terreno']['max']:.1f} m²")
    logger.info(f"- Promedio: {stats_car['superficie']['terreno']['promedio']:.1f} m²")
    
    logger.info("\n=== Análisis de Amenidades ===")
    stats_amen = analizar_amenidades(propiedades)
    logger.info(f"Total propiedades: {stats_amen['total']}")
    logger.info(f"Con amenidades: {stats_amen['con_amenidades']}")
    logger.info(f"\nAlberca: {stats_amen['alberca']}")
    logger.info(f"Jardín: {stats_amen['jardin']}")
    logger.info(f"Seguridad: {stats_amen['seguridad']}")
    logger.info("\nÁreas comunes:")
    for area, count in stats_amen['areas_comunes'].most_common():
        logger.info(f"- {area}: {count}")
    logger.info("\nAdicionales:")
    for adic, count in stats_amen['adicionales'].most_common():
        logger.info(f"- {adic}: {count}")

if __name__ == '__main__':
    main() 
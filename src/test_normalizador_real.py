#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba para el normalizador usando datos reales.
"""

import json
import logging
from datetime import datetime
from normalizador import normalizar_propiedad

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cargar_propiedades(archivo: str) -> list:
    """Carga propiedades desde un archivo JSON."""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            if isinstance(datos, list):
                return datos
            return datos.get('propiedades', [])
    except Exception as e:
        logger.error(f"Error cargando propiedades: {e}")
        return []

def guardar_propiedades(propiedades: list, archivo: str):
    """Guarda propiedades normalizadas en un archivo JSON."""
    try:
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(propiedades, f, indent=2, ensure_ascii=False)
        logger.info(f"Propiedades guardadas en: {archivo}")
    except Exception as e:
        logger.error(f"Error guardando propiedades: {e}")

def probar_filtros(propiedades_normalizadas: list):
    """Prueba los filtros con las propiedades normalizadas."""
    # Filtros de prueba
    filtros = [
        {
            "nombre": "Precio entre 1M y 3M",
            "precio_min": 1000000,
            "precio_max": 3000000
        },
        {
            "nombre": "Casas con alberca",
            "tipo_propiedad": "casa",
            "amenidades": ["alberca"]
        },
        {
            "nombre": "Propiedades en Cuernavaca",
            "ciudad": "Cuernavaca"
        }
    ]
    
    for filtro in filtros:
        propiedades_filtradas = []
        for prop in propiedades_normalizadas:
            cumple_filtro = True
            
            # Filtrar por precio
            if "precio_min" in filtro or "precio_max" in filtro:
                precio = prop.get("precio", {}).get("valor")
                if precio is None:
                    cumple_filtro = False
                else:
                    if "precio_min" in filtro and precio < filtro["precio_min"]:
                        cumple_filtro = False
                    if "precio_max" in filtro and precio > filtro["precio_max"]:
                        cumple_filtro = False
            
            # Filtrar por tipo de propiedad
            if "tipo_propiedad" in filtro:
                if prop.get("tipo_propiedad") != filtro["tipo_propiedad"]:
                    cumple_filtro = False
            
            # Filtrar por amenidades
            if "amenidades" in filtro:
                for amenidad in filtro["amenidades"]:
                    if not prop.get("amenidades", {}).get(amenidad, False):
                        cumple_filtro = False
                        break
            
            # Filtrar por ciudad
            if "ciudad" in filtro:
                if prop.get("ubicacion", {}).get("ciudad") != filtro["ciudad"]:
                    cumple_filtro = False
            
            if cumple_filtro:
                propiedades_filtradas.append(prop)
        
        logger.info(f"\nFiltro: {filtro['nombre']}")
        logger.info(f"Propiedades encontradas: {len(propiedades_filtradas)}")
        for prop in propiedades_filtradas[:3]:  # Mostrar primeras 3 propiedades
            logger.info(f"- ID: {prop['id']}")
            logger.info(f"  Precio: {prop['precio']}")
            logger.info(f"  Tipo: {prop['tipo_propiedad']}")
            logger.info(f"  Ubicación: {prop['ubicacion']['ciudad']}")
            if prop.get("amenidades"):
                logger.info(f"  Amenidades: {prop['amenidades']}")

def main():
    """Función principal."""
    # Archivos
    archivo_entrada = "resultados/propiedades_estructuradas.json"
    archivo_salida = "resultados/propiedades_normalizadas.json"
    
    # Cargar propiedades
    logger.info("Cargando propiedades...")
    propiedades = cargar_propiedades(archivo_entrada)
    logger.info(f"Propiedades cargadas: {len(propiedades)}")
    
    # Normalizar propiedades
    logger.info("\nNormalizando propiedades...")
    propiedades_normalizadas = []
    for prop in propiedades:
        try:
            prop_normalizada = normalizar_propiedad(prop)
            propiedades_normalizadas.append(prop_normalizada)
        except Exception as e:
            logger.error(f"Error normalizando propiedad {prop.get('id')}: {e}")
    
    # Guardar propiedades normalizadas
    guardar_propiedades(propiedades_normalizadas, archivo_salida)
    
    # Probar filtros
    logger.info("\nProbando filtros...")
    probar_filtros(propiedades_normalizadas)

if __name__ == "__main__":
    main() 
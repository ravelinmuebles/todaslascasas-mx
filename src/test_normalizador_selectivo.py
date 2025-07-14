#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test del Normalizador Selectivo
------------------------------
Este script prueba que la normalización selectiva funciona correctamente,
manteniendo los campos bien formateados y corrigiendo solo los mal formateados.
"""

import json
import logging
from normalizador_selectivo import normalizar_propiedad

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def probar_normalizacion_selectiva():
    """Prueba la normalización selectiva con ejemplos específicos."""
    
    # Ejemplo 1: Precio mal formateado, resto correcto
    prop1 = {
        "id": "1",
        "precio": "2.5 millones",
        "ubicacion": {
            "ciudad": "Cuernavaca",
            "colonia": "Lomas de Cortés",
            "direccion": "Av. Principal 123",
            "coordenadas": {"lat": 18.9186, "lng": -99.2345}
        },
        "caracteristicas": {
            "recamaras": 3,
            "banos": 2.5,
            "estacionamientos": 2,
            "niveles": 2,
            "superficie_construida": 180.0,
            "superficie_terreno": 250.0
        },
        "amenidades": {
            "alberca": True,
            "jardin": True,
            "seguridad": True,
            "areas_comunes": ["gimnasio"],
            "adicionales": []
        }
    }
    
    # Ejemplo 2: Características mal formateadas, resto correcto
    prop2 = {
        "id": "2",
        "precio": {
            "valor": 15000.0,
            "moneda": "MXN",
            "periodo": "Mensual"
        },
        "ubicacion": {
            "ciudad": "Cuernavaca",
            "colonia": "Delicias",
            "direccion": "Calle Reforma 456",
            "coordenadas": {"lat": 18.92, "lng": -99.23}
        },
        "caracteristicas": {
            "recamaras": "2",
            "banos": "1",
            "estacionamientos": "1",
            "niveles": "1",
            "superficie_construida": "80",
            "superficie_terreno": "80"
        },
        "amenidades": {
            "alberca": False,
            "jardin": False,
            "seguridad": True,
            "areas_comunes": ["gimnasio"],
            "adicionales": []
        }
    }
    
    # Normalizar propiedades
    prop1_norm = normalizar_propiedad(prop1)
    prop2_norm = normalizar_propiedad(prop2)
    
    # Verificar resultados
    logger.info("\n=== Propiedad 1 ===")
    logger.info("Precio original: %s", prop1["precio"])
    logger.info("Precio normalizado: %s", prop1_norm["precio"])
    logger.info("Ubicación se mantuvo igual: %s", 
                prop1["ubicacion"] == prop1_norm["ubicacion"])
    
    logger.info("\n=== Propiedad 2 ===")
    logger.info("Precio se mantuvo igual: %s", 
                prop2["precio"] == prop2_norm["precio"])
    logger.info("Características originales: %s", prop2["caracteristicas"])
    logger.info("Características normalizadas: %s", prop2_norm["caracteristicas"])

def main():
    """Función principal."""
    logger.info("Iniciando pruebas de normalización selectiva...")
    probar_normalizacion_selectiva()
    logger.info("\nPruebas completadas.")

if __name__ == '__main__':
    main() 
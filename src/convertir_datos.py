#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convertir_datos.py

Script simple para convertir propiedades_estructuradas.json
al formato que necesita el frontend.
"""

import json
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convertir_propiedad(prop):
    """
    Convierte una propiedad del formato estructurado al formato del frontend.
    """
    # Obtener datos originales
    datos_orig = prop.get("datos_originales", {})
    caract_orig = datos_orig.get("caracteristicas", {})
    
    # Crear nueva propiedad con características numéricas
    nueva_prop = prop.copy()
    
    # Reemplazar características con formato numérico
    nueva_prop["caracteristicas"] = {
        "recamaras": caract_orig.get("recamaras"),
        "banos": caract_orig.get("banos"),
        "estacionamientos": caract_orig.get("estacionamientos"),
        "niveles": caract_orig.get("niveles"),
        "superficie_terreno": caract_orig.get("superficie_m2"),
        "superficie_construida": caract_orig.get("construccion_m2"),
        "antiguedad": caract_orig.get("edad")
    }
    
    return nueva_prop

def main():
    """Función principal."""
    try:
        logger.info("Leyendo propiedades estructuradas...")
        with open("resultados/propiedades_estructuradas.json", 'r', encoding='utf-8') as f:
            propiedades = json.load(f)
        
        logger.info(f"Convirtiendo {len(propiedades)} propiedades...")
        propiedades_convertidas = []
        
        for i, prop in enumerate(propiedades):
            try:
                prop_convertida = convertir_propiedad(prop)
                propiedades_convertidas.append(prop_convertida)
                
                if (i + 1) % 1000 == 0:
                    logger.info(f"Convertidas {i + 1} propiedades...")
                    
            except Exception as e:
                logger.error(f"Error convirtiendo propiedad {i}: {e}")
                continue
        
        logger.info("Guardando propiedades convertidas...")
        with open("resultados/propiedades_normalizadas.json", 'w', encoding='utf-8') as f:
            json.dump(propiedades_convertidas, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Conversión completada: {len(propiedades_convertidas)} propiedades")
        
        # Mostrar estadísticas
        stats = {"con_recamaras": 0, "con_banos": 0, "con_superficie": 0}
        for prop in propiedades_convertidas:
            caract = prop["caracteristicas"]
            if caract.get("recamaras"):
                stats["con_recamaras"] += 1
            if caract.get("banos"):
                stats["con_banos"] += 1
            if caract.get("superficie_terreno") or caract.get("superficie_construida"):
                stats["con_superficie"] += 1
        
        logger.info(f"📊 Estadísticas:")
        logger.info(f"   - Con recámaras: {stats['con_recamaras']}")
        logger.info(f"   - Con baños: {stats['con_banos']}")
        logger.info(f"   - Con superficie: {stats['con_superficie']}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    main() 
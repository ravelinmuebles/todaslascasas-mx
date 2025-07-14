#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from datetime import datetime
from procesa_propiedad import procesar_propiedad, procesar_archivo

def configurar_logging():
    """Configura el sistema de logging para pruebas."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test_procesamiento.log'),
            logging.StreamHandler()
        ]
    )

def crear_propiedad_prueba():
    """Crea una propiedad de prueba con diferentes escenarios."""
    return {
        "id": "12345",
        "titulo": "Casa en venta en zona residencial",
        "descripcion": "Hermosa casa de 3 habitaciones, 2 baños, con jardín y garaje. Precio: $250,000 USD",
        "link": "https://facebook.com/marketplace/item/12345",
        "precio": "250000",
        "moneda": "USD",
        "tipo_propiedad": "casa",
        "tipo_operacion": "venta",
        "ubicacion": {
            "ciudad": "Ciudad Ejemplo",
            "estado": "Estado Ejemplo",
            "pais": "México"
        },
        "caracteristicas": {
            "habitaciones": 3,
            "banos": 2,
            "metros_cuadrados": 150
        },
        "amenidades": ["jardin", "garaje", "seguridad"],
        "legal": {
            "estado_legal": "libre",
            "documentacion": "completa"
        }
    }

def crear_propiedad_invalida():
    """Crea una propiedad inválida para probar el manejo de errores."""
    return {
        "id": "67890",
        "titulo": "",  # Título vacío
        "descripcion": None,  # Descripción nula
        "link": None,  # Link nulo
        "precio": "no_valido",  # Precio inválido
        "tipo_propiedad": "tipo_invalido",
        "tipo_operacion": "operacion_invalida",
        "ubicacion": {
            "ciudad": "Ciudad Invalida",
            "estado": "Estado Invalido",
            "pais": "Pais Invalido"
        }
    }

def test_procesar_propiedad():
    """Prueba el procesamiento de una propiedad individual."""
    logging.info("Iniciando prueba de procesamiento de propiedad individual")
    
    # Probar propiedad válida
    propiedad_valida = crear_propiedad_prueba()
    resultado_valido = procesar_propiedad(propiedad_valida)
    
    # Verificar estructura del resultado
    assert "datos_originales" in resultado_valido
    assert "datos_procesados" in resultado_valido
    assert "metadatos_procesamiento" in resultado_valido
    
    # Verificar metadatos
    metadatos = resultado_valido["metadatos_procesamiento"]
    assert "fecha_procesamiento" in metadatos
    assert "modulos_aplicados" in metadatos
    assert "errores" in metadatos
    assert "advertencias" in metadatos
    
    # Verificar que no hay errores en propiedad válida
    assert len(metadatos["errores"]) == 0
    
    # Probar propiedad inválida
    propiedad_invalida = crear_propiedad_invalida()
    resultado_invalido = procesar_propiedad(propiedad_invalida)
    
    # Verificar que se detectaron errores
    assert len(resultado_invalido["metadatos_procesamiento"]["errores"]) > 0
    assert len(resultado_invalido["metadatos_procesamiento"]["advertencias"]) > 0
    
    logging.info("Prueba de procesamiento de propiedad individual completada exitosamente")

def test_procesar_archivo():
    """Prueba el procesamiento de un archivo completo."""
    logging.info("Iniciando prueba de procesamiento de archivo")
    
    # Crear directorio de prueba
    Path("test_data").mkdir(exist_ok=True)
    
    # Crear archivo de prueba
    propiedades_prueba = {
        "propiedades": [
            crear_propiedad_prueba(),
            crear_propiedad_invalida()
        ]
    }
    
    archivo_entrada = "test_data/propiedades_prueba.json"
    archivo_salida = "test_data/resultados_prueba.json"
    
    # Guardar archivo de prueba
    with open(archivo_entrada, 'w', encoding='utf-8') as f:
        json.dump(propiedades_prueba, f, ensure_ascii=False, indent=2)
    
    # Procesar archivo
    procesar_archivo(archivo_entrada, archivo_salida)
    
    # Verificar resultados
    with open(archivo_salida, 'r', encoding='utf-8') as f:
        resultados = json.load(f)
    
    # Verificar estructura del resultado
    assert "propiedades" in resultados
    assert "fecha_procesamiento" in resultados
    assert "estadisticas" in resultados
    assert "version" in resultados
    
    # Verificar estadísticas
    estadisticas = resultados["estadisticas"]
    assert estadisticas["total_propiedades"] == 2
    assert estadisticas["con_errores"] > 0
    assert "modulos_con_errores" in estadisticas
    assert "campos_criticos_faltantes" in estadisticas
    
    logging.info("Prueba de procesamiento de archivo completada exitosamente")

def main():
    """Función principal de pruebas."""
    try:
        # Configurar logging
        configurar_logging()
        
        # Crear directorio de logs si no existe
        Path("logs").mkdir(exist_ok=True)
        
        # Ejecutar pruebas
        test_procesar_propiedad()
        test_procesar_archivo()
        
        logging.info("Todas las pruebas completadas exitosamente")
        
    except Exception as e:
        logging.error(f"Error en las pruebas: {e}")
        raise

if __name__ == "__main__":
    main() 
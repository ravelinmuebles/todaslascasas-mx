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
            logging.FileHandler('logs/test_procesamiento_real.log'),
            logging.StreamHandler()
        ]
    )

def cargar_propiedad_ejemplo():
    """Carga una propiedad real del repositorio para pruebas."""
    try:
        with open('resultados/repositorio_propiedades.json', 'r', encoding='utf-8') as f:
            datos = json.load(f)
            
        # Tomar la primera propiedad del repositorio
        primera_clave = next(iter(datos.keys()))
        propiedad = datos[primera_clave]
        
        logging.info(f"Propiedad cargada: ID={primera_clave}")
        return propiedad
        
    except Exception as e:
        logging.error(f"Error cargando propiedad de ejemplo: {e}")
        return None

def test_procesar_propiedad_real():
    """Prueba el procesamiento de una propiedad real."""
    logging.info("Iniciando prueba con propiedad real")
    
    # Cargar propiedad real
    propiedad = cargar_propiedad_ejemplo()
    if not propiedad:
        logging.error("No se pudo cargar la propiedad de ejemplo")
        return
    
    # Crear backup de la propiedad original
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"resultados/test_propiedad_original_{timestamp}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(propiedad, f, ensure_ascii=False, indent=2)
    logging.info(f"Backup de propiedad original guardado en: {backup_file}")
    
    # Preparar la propiedad para el procesamiento
    propiedad_procesar = {
        "id": propiedad["id"],
        "titulo": propiedad["titulo"],
        "descripcion": propiedad["descripcion"],
        "link": propiedad["link"],
        "precio": propiedad["precio"],
        "tipo_operacion": propiedad["tipo_operacion"],
        "ubicacion": propiedad["ubicacion"],
        "caracteristicas": propiedad["caracteristicas"],
        "imagen_portada": propiedad["imagen_portada"],
        "fecha_extraccion": propiedad["fecha_extraccion"]
    }
    
    # Procesar la propiedad
    resultado = procesar_propiedad(propiedad_procesar)
    
    # Guardar resultado del procesamiento
    resultado_file = f"resultados/test_propiedad_procesada_{timestamp}.json"
    with open(resultado_file, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    logging.info(f"Resultado del procesamiento guardado en: {resultado_file}")
    
    # Analizar resultados
    metadatos = resultado["metadatos_procesamiento"]
    
    logging.info("\n=== RESULTADOS DEL PROCESAMIENTO ===")
    logging.info(f"Fecha de procesamiento: {metadatos['fecha_procesamiento']}")
    logging.info(f"Módulos aplicados: {', '.join(metadatos['modulos_aplicados'])}")
    
    if metadatos["errores"]:
        logging.warning("\nErrores encontrados:")
        for error in metadatos["errores"]:
            logging.warning(f"- {error}")
    
    if metadatos["advertencias"]:
        logging.warning("\nAdvertencias encontradas:")
        for advertencia in metadatos["advertencias"]:
            logging.warning(f"- {advertencia}")
    
    # Mostrar cambios en campos importantes
    logging.info("\nCambios en campos importantes:")
    campos_importantes = ["precio", "tipo_propiedad", "tipo_operacion", "ubicacion", "caracteristicas"]
    for campo in campos_importantes:
        original = propiedad_procesar.get(campo)
        procesado = resultado["datos_procesados"].get(campo)
        if original != procesado:
            logging.info(f"\n{campo}:")
            logging.info(f"  Original: {original}")
            logging.info(f"  Procesado: {procesado}")

def main():
    """Función principal de pruebas."""
    try:
        # Configurar logging
        configurar_logging()
        
        # Crear directorios necesarios
        Path("logs").mkdir(exist_ok=True)
        Path("resultados").mkdir(exist_ok=True)
        
        # Ejecutar prueba con propiedad real
        test_procesar_propiedad_real()
        
        logging.info("\nPrueba completada exitosamente")
        
    except Exception as e:
        logging.error(f"Error en las pruebas: {e}")
        raise

if __name__ == "__main__":
    main() 
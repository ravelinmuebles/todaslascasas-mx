#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Importar módulos de procesamiento
from modules.tipo_propiedad import actualizar_tipo_propiedad
from modules.tipo_operacion import actualizar_tipo_operacion
from modules.precio import actualizar_precio_propiedad
from modules.ubicacion import actualizar_ubicacion
from modules.caracteristicas import actualizar_caracteristicas
from modules.amenidades import actualizar_amenidades
from modules.legal import actualizar_legal
from modules.validacion import validar_propiedad_completa

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/procesa_propiedades_real.log'),
        logging.StreamHandler()
    ]
)

def cargar_propiedades(archivo: str) -> Dict:
    """Carga las propiedades desde un archivo JSON."""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error cargando archivo {archivo}: {e}")
        return {}

def guardar_propiedades(datos: Dict, archivo: str) -> None:
    """Guarda las propiedades en un archivo JSON."""
    try:
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        logging.info(f"Archivo guardado: {archivo}")
    except Exception as e:
        logging.error(f"Error guardando archivo {archivo}: {e}")

def adaptar_propiedad(propiedad: Dict) -> Dict:
    """Adapta la propiedad para que tenga la estructura esperada por los módulos."""
    # Crear una copia profunda
    propiedad_adaptada = json.loads(json.dumps(propiedad))
    
    # Preservar el ID
    if "id" not in propiedad_adaptada and isinstance(propiedad_adaptada, dict):
        propiedad_adaptada["id"] = list(propiedad.keys())[0]
    
    # Mapear descripcion a descripcion_original
    if "descripcion" in propiedad_adaptada:
        propiedad_adaptada["descripcion_original"] = propiedad_adaptada["descripcion"]
    
    # Crear sección propiedad si no existe
    if "propiedad" not in propiedad_adaptada:
        propiedad_adaptada["propiedad"] = {}
    
    # Mover campos a la sección propiedad
    campos_a_mover = {
        "tipo_operacion": "tipo_operacion",
        "tipo_propiedad": "tipo_propiedad",
        "precio": "precio",
        "ubicacion": "ubicacion",
        "caracteristicas": "caracteristicas"
    }
    
    for campo_origen, campo_destino in campos_a_mover.items():
        if campo_origen in propiedad_adaptada:
            propiedad_adaptada["propiedad"][campo_destino] = propiedad_adaptada.pop(campo_origen)
    
    # Asegurar que los campos críticos existan
    if "titulo" not in propiedad_adaptada:
        propiedad_adaptada["titulo"] = "Sin título"
    
    if "link" not in propiedad_adaptada:
        propiedad_adaptada["link"] = ""
    
    if "descripcion_original" not in propiedad_adaptada:
        propiedad_adaptada["descripcion_original"] = ""
    
    return propiedad_adaptada

def procesar_propiedad(propiedad: Dict) -> Dict:
    """Procesa una propiedad aplicando todos los módulos."""
    try:
        # Adaptar la propiedad
        propiedad_adaptada = adaptar_propiedad(propiedad)
        
        # Crear diccionario de resultado
        resultado = {
            "datos_originales": propiedad,
            "datos_procesados": {},
            "metadatos_procesamiento": {
                "fecha_procesamiento": datetime.now().isoformat(),
                "modulos_aplicados": [],
                "errores": [],
                "advertencias": []
            }
        }
        
        # Procesar la propiedad
        propiedad_procesada = propiedad_adaptada.copy()
        
        # Aplicar cada módulo en secuencia
        modulos = [
            (actualizar_caracteristicas, "caracteristicas"),
            (actualizar_amenidades, "amenidades"),
            (actualizar_tipo_propiedad, "tipo_propiedad"),
            (actualizar_tipo_operacion, "tipo_operacion"),
            (actualizar_precio_propiedad, "precio"),
            (actualizar_ubicacion, "ubicacion"),
            (actualizar_legal, "legal")
        ]
        
        for modulo, nombre in modulos:
            try:
                propiedad_procesada = modulo(propiedad_procesada)
                resultado["metadatos_procesamiento"]["modulos_aplicados"].append(nombre)
            except Exception as e:
                error_msg = f"Error en módulo {nombre}: {str(e)}"
                logging.error(error_msg)
                resultado["metadatos_procesamiento"]["errores"].append(error_msg)
        
        # Validar la propiedad
        es_valida, errores = validar_propiedad_completa(propiedad_procesada)
        if not es_valida:
            logging.warning(f"Propiedad con errores de validación: {errores}")
            resultado["metadatos_procesamiento"]["errores"].extend(errores)
        
        # Guardar datos procesados
        resultado["datos_procesados"] = propiedad_procesada
        
        return resultado
        
    except Exception as e:
        error_msg = f"Error general procesando propiedad: {str(e)}"
        logging.error(error_msg)
        return {
            "datos_originales": propiedad,
            "datos_procesados": propiedad,
            "metadatos_procesamiento": {
                "fecha_procesamiento": datetime.now().isoformat(),
                "modulos_aplicados": [],
                "errores": [error_msg],
                "advertencias": []
            }
        }

def procesar_archivo(archivo_entrada: str, archivo_salida: str) -> None:
    """Procesa un archivo completo de propiedades."""
    # Cargar datos
    datos = cargar_propiedades(archivo_entrada)
    if not datos:
        logging.error("No se encontraron propiedades para procesar")
        return
        
    # Inicializar contadores y listas
    propiedades_procesadas = []
    propiedades_invalidas = []
    estadisticas = {
        "total_propiedades": len(datos),
        "procesadas_exitosamente": 0,
        "con_errores": 0,
        "con_advertencias": 0,
        "modulos_con_errores": {},
        "campos_criticos_faltantes": {}
    }
    
    # Procesar cada propiedad
    for i, (id_prop, propiedad) in enumerate(datos.items(), 1):
        logging.info(f"Procesando propiedad {i}/{len(datos)} (ID: {id_prop})")
        
        # Asegurar que la propiedad tenga su ID
        propiedad["id"] = id_prop
        
        resultado = procesar_propiedad(propiedad)
        
        # Actualizar estadísticas
        if resultado["metadatos_procesamiento"]["errores"]:
            estadisticas["con_errores"] += 1
            # Contar errores por módulo
            for error in resultado["metadatos_procesamiento"]["errores"]:
                if "Error en módulo" in error:
                    modulo = error.split("módulo ")[1].split(":")[0]
                    estadisticas["modulos_con_errores"][modulo] = estadisticas["modulos_con_errores"].get(modulo, 0) + 1
        
        if resultado["metadatos_procesamiento"]["advertencias"]:
            estadisticas["con_advertencias"] += 1
            # Contar campos críticos faltantes
            for advertencia in resultado["metadatos_procesamiento"]["advertencias"]:
                if "Campo crítico" in advertencia:
                    campo = advertencia.split("'")[1]
                    estadisticas["campos_criticos_faltantes"][campo] = estadisticas["campos_criticos_faltantes"].get(campo, 0) + 1
        
        if not resultado["metadatos_procesamiento"]["errores"]:
            estadisticas["procesadas_exitosamente"] += 1
        
        # Añadir a la lista principal
        propiedades_procesadas.append(resultado)
        
        # Si hay errores de validación, añadir a la lista de inválidas
        if resultado["metadatos_procesamiento"]["errores"]:
            propiedades_invalidas.append(resultado)
            
    # Guardar resultados
    resultado_final = {
        "propiedades": propiedades_procesadas,
        "fecha_procesamiento": datetime.now().isoformat(),
        "estadisticas": estadisticas,
        "version": "2.1"  # Nueva versión con metadatos mejorados
    }
    
    guardar_propiedades(resultado_final, archivo_salida)
    
    # Guardar propiedades inválidas en un archivo separado
    if propiedades_invalidas:
        archivo_invalidas = archivo_salida.replace(".json", "_invalidas.json")
        guardar_propiedades({
            "propiedades": propiedades_invalidas,
            "fecha_procesamiento": datetime.now().isoformat(),
            "estadisticas": {
                "total_invalidas": len(propiedades_invalidas),
                "razones_invalidacion": estadisticas["modulos_con_errores"]
            },
            "version": "2.1"
        }, archivo_invalidas)
        
    # Generar reporte detallado
    logging.info(f"""
    Procesamiento completado:
    - Total propiedades: {estadisticas['total_propiedades']}
    - Procesadas exitosamente: {estadisticas['procesadas_exitosamente']}
    - Con errores: {estadisticas['con_errores']}
    - Con advertencias: {estadisticas['con_advertencias']}
    
    Errores por módulo:
    {json.dumps(estadisticas['modulos_con_errores'], indent=2, ensure_ascii=False)}
    
    Campos críticos faltantes:
    {json.dumps(estadisticas['campos_criticos_faltantes'], indent=2, ensure_ascii=False)}
    
    Versión: 2.1 (con metadatos mejorados)
    """)

if __name__ == "__main__":
    # Definir archivos
    archivo_entrada = "resultados/repositorio_propiedades.json"
    archivo_salida = "resultados/propiedades_procesadas_real.json"
    
    # Crear directorios necesarios
    Path("logs").mkdir(exist_ok=True)
    Path("resultados").mkdir(exist_ok=True)
    
    # Procesar archivo
    procesar_archivo(archivo_entrada, archivo_salida) 
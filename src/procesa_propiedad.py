#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import re

# Importar todos los módulos
from modules.tipo_propiedad import actualizar_tipo_propiedad
from modules.tipo_operacion import actualizar_tipo_operacion
from modules.precio import actualizar_precio_propiedad
from modules.ubicacion import actualizar_ubicacion
from modules.caracteristicas import actualizar_caracteristicas
from modules.amenidades import actualizar_amenidades
from modules.legal import actualizar_legal
from modules.validacion import validar_propiedad_completa

def configurar_logging():
    """Configura el sistema de logging."""
    # Asegurar que la carpeta 'logs' exista para evitar FileNotFoundError
    Path('logs').mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/procesa_propiedades.log'),
            logging.StreamHandler()
        ]
    )

def cargar_propiedades(archivo: str) -> Dict:
    """
    Carga las propiedades desde un archivo JSON.
    Maneja tanto el formato de repositorio_propiedades.json (objeto con IDs como claves)
    como el formato de propiedades_estructuradas.json (array en clave "propiedades")
    
    Args:
        archivo: Ruta al archivo JSON
        
    Returns:
        Dict con las propiedades en formato estándar {"propiedades": [...]}
    """
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            datos = json.load(f)
            
        # Si ya tiene el formato correcto
        if "propiedades" in datos:
            return datos
            
        # Si es el formato de repositorio (IDs como claves)
        if isinstance(datos, dict) and len(datos) > 0:
            # Verificar si las claves parecen IDs de propiedades
            primera_clave = next(iter(datos.keys()))
            if primera_clave.isdigit() or len(primera_clave) > 10:
                # Convertir a formato estándar
                propiedades = list(datos.values())
                return {"propiedades": propiedades}
        
        # Fallback: asumir que es un array directo
        if isinstance(datos, list):
            return {"propiedades": datos}
            
        logging.warning(f"Formato inesperado en {archivo}")
        return {"propiedades": []}
        
    except Exception as e:
        logging.error(f"Error cargando archivo {archivo}: {e}")
        return {"propiedades": []}

def guardar_propiedades(datos: Dict, archivo: str) -> None:
    """
    Guarda las propiedades en un archivo JSON.
    
    Args:
        datos: Dict con los datos a guardar
        archivo: Ruta donde guardar el archivo
    """
    try:
        # Crear backup antes de guardar
        if Path(archivo).exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = f"{archivo}.backup_{timestamp}"
            Path(archivo).rename(backup)
            logging.info(f"Backup creado: {backup}")
        
        # Guardar archivo actualizado
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        logging.info(f"Archivo guardado: {archivo}")
            
    except Exception as e:
        logging.error(f"Error guardando archivo {archivo}: {e}")

def extraer_titulo_inteligente(propiedad: Dict) -> Dict:
    """
    Extrae título inteligentemente desde descripción cuando título = "Notificaciones"
    
    PABLO: Función específica para corregir problema de títulos incorrectos de Facebook
    
    Args:
        propiedad: Diccionario con datos de la propiedad
        
    Returns:
        Dict: Propiedad con título corregido
    """
    try:
        titulo_actual = propiedad.get('titulo', '').strip()
        descripcion = propiedad.get('descripcion', '').strip()
        
        # Si el título NO es problemático, no tocar
        if titulo_actual and titulo_actual.lower() not in ['notificaciones', 'notification', 'facebook']:
            return propiedad
            
        # Si no hay descripción, usar ID como fallback
        if not descripcion:
            propiedad['titulo'] = f"Propiedad {propiedad.get('id', 'ID_DESCONOCIDO')}"
            return propiedad
            
        # EXTRACCIÓN INTELIGENTE DEL TÍTULO REAL
        # Patrón 1: Precio + Ubicación (ej: "$6,980,000📍Fracc. Burgos Bugambilias")
        patron_precio_ubicacion = r'[$＄][\d,.,\s]+[📍🏠🏡]?\s*([^📍🏠🏡\n]+?)(?:,|\n|al\s|en\s|$)'
        match = re.search(patron_precio_ubicacion, descripcion, re.IGNORECASE)
        
        if match:
            titulo_extraido = match.group(1).strip()
            # Limpiar el título extraído
            titulo_extraido = re.sub(r'[🌇🌿✨👮‍♂️📐🏊‍♀️🔹🛋️🍳🚻🛏️🌤️🏖️🧹🧺🛌☕🌞💡🔒💧🛠️📷🪴🏊‍♀️💌]', '', titulo_extraido)
            titulo_extraido = titulo_extraido.replace('al sur de', '').replace('al norte de', '').replace('en ', '').strip()
            
            if len(titulo_extraido) >= 8:  # Título válido mínimo
                propiedad['titulo'] = titulo_extraido[:80]  # Límite razonable
                return propiedad
        
        # Patrón 2: Buscar ubicación sin precio (ej: "Fracc. Burgos Bugambilias")
        patron_ubicacion = r'(?:Fracc\.|Fraccionamiento|Col\.|Colonia|Residencial|Privada)\s+([A-Za-zÁÉÍÓÚáéíóúñÑ\s]+?)(?:\n|,|al\s|en\s|$)'
        match = re.search(patron_ubicacion, descripcion, re.IGNORECASE)
        
        if match:
            ubicacion_extraida = match.group(1).strip()
            if len(ubicacion_extraida) >= 5:
                propiedad['titulo'] = f"Casa en {ubicacion_extraida}"[:80]
                return propiedad
        
        # Patrón 3: Extraer primera línea significativa
        primera_linea = descripcion.split('\n')[0].strip()
        # Limpiar emojis y caracteres especiales
        primera_linea_limpia = re.sub(r'[🏡$＄📍🌇🌿✨👮‍♂️📐🏊‍♀️💌]', '', primera_linea)
        primera_linea_limpia = re.sub(r'[\d,\.\s]*$', '', primera_linea_limpia).strip()
        
        if len(primera_linea_limpia) >= 10:
            propiedad['titulo'] = primera_linea_limpia[:80]
        else:
            # Fallback final
            ciudad = propiedad.get('ciudad', 'Ubicación')
            propiedad['titulo'] = f"Propiedad en {ciudad.title()}"
            
        return propiedad
        
    except Exception as e:
        logging.warning(f"Error extrayendo título inteligente: {e}")
        # Fallback seguro
        ciudad = propiedad.get('ciudad', 'Ubicación')
        propiedad['titulo'] = f"Propiedad en {ciudad.title()}"
        return propiedad

def procesar_propiedad(propiedad: Dict) -> Dict:
    """
    Procesa una propiedad aplicando todos los módulos.
    
    Args:
        propiedad: Diccionario con los datos de la propiedad
        
    Returns:
        Dict: Propiedad procesada con campos originales preservados y metadatos de procesamiento
    """
    try:
        # Crear una copia profunda de la propiedad original
        propiedad_original = json.loads(json.dumps(propiedad))
        
        # Crear diccionario de resultado con campos originales y metadatos
        resultado = {
            "datos_originales": propiedad_original,
            "datos_procesados": {},
            "metadatos_procesamiento": {
                "fecha_procesamiento": datetime.now().isoformat(),
                "modulos_aplicados": [],
                "errores": [],
                "advertencias": []
            }
        }
        
        # Validar campos críticos antes del procesamiento
        campos_criticos = ["id", "titulo", "descripcion"]
        for campo in campos_criticos:
            if campo not in propiedad or not propiedad[campo]:
                resultado["metadatos_procesamiento"]["advertencias"].append(
                    f"Campo crítico '{campo}' no presente o vacío"
                )
        
        # Procesar la propiedad
        propiedad_procesada = propiedad.copy()
        
        # ✅ PABLO: AGREGAR EXTRACCIÓN DE TÍTULOS COMO PRIMER MÓDULO
        # Aplicar cada módulo en secuencia con manejo de errores individual
        modulos = [
            (extraer_titulo_inteligente, "extraccion_titulo"),  # ← NUEVO MÓDULO AÑADIDO
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
        
        # Validar la propiedad usando los datos originales
        es_valida, errores = validar_propiedad_completa(propiedad_original)
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
    """
    Procesa un archivo completo de propiedades.
    
    Args:
        archivo_entrada: Ruta al archivo de entrada
        archivo_salida: Ruta donde guardar el resultado
    """
    # Cargar datos
    datos = cargar_propiedades(archivo_entrada)
    
    if not datos.get("propiedades"):
        logging.error("No se encontraron propiedades para procesar")
        return
        
    # Inicializar contadores y listas
    propiedades_procesadas = []
    propiedades_invalidas = []
    estadisticas = {
        "total_propiedades": len(datos["propiedades"]),
        "procesadas_exitosamente": 0,
        "con_errores": 0,
        "con_advertencias": 0,
        "modulos_con_errores": {},
        "campos_criticos_faltantes": {}
    }
    
    # Procesar cada propiedad
    for i, propiedad in enumerate(datos["propiedades"], 1):
        logging.info(f"Procesando propiedad {i}/{len(datos['propiedades'])}")
        
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
    # Configurar logging
    configurar_logging()
    
    # Definir archivos (desde la perspectiva de la carpeta src)
    archivo_entrada = "/Users/pabloravel/Proyectos/facebook_scraper/resultados/repositorio_propiedades.json"
    archivo_salida = "/Users/pabloravel/Proyectos/facebook_scraper/resultados/propiedades_estructuradas.json"
    
    # Crear directorios necesarios
    Path("logs").mkdir(exist_ok=True)
    Path("resultados").mkdir(exist_ok=True)
    
    # Procesar archivo
    procesar_archivo(archivo_entrada, archivo_salida) 
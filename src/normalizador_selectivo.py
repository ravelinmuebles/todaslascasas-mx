#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Normalizador Selectivo de Propiedades
-----------------------------------
Este script normaliza selectivamente los datos de propiedades,
manteniendo la estructura original cuando es correcta y normalizando
solo los campos que necesitan ajustes.
"""

import json
import logging
from typing import Dict, List, Any, Optional
import re

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalizar_precio(precio: Dict) -> Dict:
    """Normaliza el precio si es necesario."""
    if not isinstance(precio, dict):
        return {
            "texto": str(precio),
            "valor": None,
            "es_valido": False,
            "confianza": 0.0,
            "mensaje": "Formato inválido",
            "formato": str(precio),
            "moneda": None
        }
    # Si ya tiene la estructura correcta y el valor es válido, mantenerlo
    if all(k in precio for k in ["texto", "valor", "es_valido", "confianza", "mensaje", "formato"]):
        if precio.get("valor") is not None and precio.get("es_valido", False):
            return precio
    # Si tiene campo valor y parece válido, usarlo
    valor = precio.get("valor")
    if valor is not None:
        try:
            valor_float = float(valor)
            es_valido = valor_float > 1000 and valor_float < 100_000_000
            moneda = precio.get("moneda", "MXN")
            return {
                "texto": precio.get("texto", str(valor)),
                "valor": valor_float,
                "es_valido": es_valido,
                "confianza": 1.0 if es_valido else 0.0,
                "mensaje": "Valor numérico directo" if es_valido else "Valor fuera de rango",
                "formato": precio.get("formato", str(valor)),
                "moneda": moneda
            }
        except Exception:
            pass
    # Si no, intentar extraer del texto
    texto = str(precio.get("texto", ""))
    valor_extraido = None
    moneda = "MXN"
    es_valido = False
    confianza = 0.0
    mensaje = ""
    formato = texto
    try:
        texto_limpio = re.sub(r'[^\d.]', '', texto)
        if texto_limpio:
            valor_extraido = float(texto_limpio)
            es_valido = valor_extraido > 1000 and valor_extraido < 100_000_000
            confianza = 1.0 if es_valido else 0.0
            mensaje = "Extraído de texto" if es_valido else "Valor fuera de rango"
    except Exception as e:
        mensaje = f"Error al extraer precio: {str(e)}"
    return {
        "texto": texto,
        "valor": valor_extraido,
        "es_valido": es_valido,
        "confianza": confianza,
        "mensaje": mensaje,
        "formato": formato,
        "moneda": moneda
    }

def normalizar_caracteristicas(caracteristicas: List[str]) -> Dict:
    """Normaliza las características si es necesario."""
    if not isinstance(caracteristicas, list):
        return {}
    
    # Extraer valores numéricos de las características
    recamaras = None
    banos = None
    estacionamientos = None
    niveles = None
    superficie_construida = None
    superficie_terreno = None
    
    for car in caracteristicas:
        if isinstance(car, str):
            # Buscar números en el texto
            match = re.search(r'(\d+)', car)
            if match:
                num = int(match.group(1))
                if 'recamara' in car.lower():
                    recamaras = num
                elif 'bano' in car.lower():
                    banos = num
                elif 'estacionamiento' in car.lower():
                    estacionamientos = num
                elif 'nivel' in car.lower():
                    niveles = num
                elif 'm2' in car.lower() or 'm²' in car.lower():
                    if 'construccion' in car.lower():
                        superficie_construida = num
                    else:
                        superficie_terreno = num
    
    return {
        "recamaras": recamaras,
        "banos": banos,
        "estacionamientos": estacionamientos,
        "niveles": niveles,
        "superficie_construida": superficie_construida,
        "superficie_terreno": superficie_terreno
    }

def normalizar_amenidades(amenidades: Dict) -> Dict:
    """Normaliza las amenidades si es necesario."""
    if not isinstance(amenidades, dict):
        return {
            "alberca": False,
            "jardin": False,
            "seguridad": False,
            "areas_comunes": [],
            "adicionales": []
        }
    
    # Extraer valores booleanos
    alberca = amenidades.get("alberca", {}).get("presente", False)
    jardin = amenidades.get("jardin", {}).get("presente", False)
    seguridad = False
    
    # Extraer áreas comunes y adicionales
    areas_comunes = []
    adicionales = []
    
    for key, value in amenidades.items():
        if isinstance(value, dict) and value.get("presente", False):
            if key in ["alberca", "jardin"]:
                continue
            elif key in ["seguridad", "vigilancia"]:
                seguridad = True
            elif key in ["gimnasio", "salon", "area_comun"]:
                areas_comunes.append(key)
            else:
                adicionales.append(key)
    
    return {
        "alberca": alberca,
        "jardin": jardin,
        "seguridad": seguridad,
        "areas_comunes": areas_comunes,
        "adicionales": adicionales
    }

def normalizar_propiedad(propiedad: Dict) -> Dict:
    """Normaliza una propiedad manteniendo la estructura original cuando es correcta."""
    if not isinstance(propiedad, dict):
        return {}
    
    # Crear una copia de la propiedad original
    prop_normalizada = propiedad.copy()
    
    # Normalizar precio si existe
    if "propiedad" in prop_normalizada and "precio" in prop_normalizada["propiedad"]:
        prop_normalizada["propiedad"]["precio"] = normalizar_precio(prop_normalizada["propiedad"]["precio"])
    
    # Normalizar características si existen
    if "caracteristicas" in prop_normalizada:
        prop_normalizada["caracteristicas"] = normalizar_caracteristicas(prop_normalizada["caracteristicas"])
    
    # Normalizar amenidades si existen
    if "amenidades" in prop_normalizada:
        prop_normalizada["amenidades"] = normalizar_amenidades(prop_normalizada["amenidades"])
    
    return prop_normalizada

def extraer_caracteristicas_numericas(propiedad: Dict) -> Dict:
    """
    Extrae las características numéricas de los datos originales.
    
    Args:
        propiedad: Propiedad con datos estructurados
        
    Returns:
        Dict con características en formato numérico
    """
    # Obtener características de datos_originales si existen
    datos_orig = propiedad.get("datos_originales", {})
    caract_orig = datos_orig.get("caracteristicas", {})
    
    # Mapear superficie_m2 y construccion_m2 a los nombres esperados
    resultado = {
        "recamaras": caract_orig.get("recamaras"),
        "banos": caract_orig.get("banos"),
        "estacionamientos": caract_orig.get("estacionamientos"),
        "niveles": caract_orig.get("niveles"),
        "superficie_terreno": caract_orig.get("superficie_m2"),
        "superficie_construida": caract_orig.get("construccion_m2"),
        "antiguedad": caract_orig.get("edad")
    }
    
    # Limpiar valores None y convertir a tipos apropiados
    for key, value in resultado.items():
        if value is not None:
            try:
                if key in ["recamaras", "estacionamientos", "niveles", "antiguedad"]:
                    resultado[key] = int(value)
                elif key in ["banos", "superficie_terreno", "superficie_construida"]:
                    resultado[key] = float(value)
            except (ValueError, TypeError):
                resultado[key] = None
    
    return resultado

def extraer_precio_numerico(propiedad: Dict) -> Dict:
    """
    Extrae el precio en formato numérico.
    
    Args:
        propiedad: Propiedad con datos estructurados
        
    Returns:
        Dict con precio normalizado
    """
    datos_orig = propiedad.get("datos_originales", {})
    precio_str = datos_orig.get("precio", "")
    
    # Extraer número del precio
    if precio_str:
        # Remover símbolos y extraer números
        precio_limpio = re.sub(r'[^\d.]', '', precio_str.replace(',', ''))
        try:
            precio_num = float(precio_limpio)
            return {
                "valor": precio_num,
                "moneda": "MXN",
                "periodo": "Total" if propiedad.get("operacion") == "Venta" else "Mensual"
            }
        except ValueError:
            pass
    
    return {"valor": None, "moneda": "MXN", "periodo": "Total"}

def normalizar_propiedad_selectiva(propiedad: Dict) -> Dict:
    """
    Normaliza una propiedad manteniendo la estructura original pero
    convirtiendo características y precios a formato numérico.
    
    Args:
        propiedad: Propiedad original
        
    Returns:
        Propiedad normalizada
    """
    # Copiar la propiedad original
    resultado = propiedad.copy()
    
    # Reemplazar características con versión numérica
    resultado["caracteristicas"] = extraer_caracteristicas_numericas(propiedad)
    
    # Agregar precio numérico
    resultado["precio_numerico"] = extraer_precio_numerico(propiedad)
    
    # Asegurar que operacion esté en formato correcto
    if "operacion" in resultado:
        resultado["tipo_operacion"] = resultado["operacion"].lower()
    
    # Asegurar que ubicacion.ciudad esté disponible
    if "ubicacion" in resultado and "ciudad" in resultado["ubicacion"]:
        resultado["ciudad"] = resultado["ubicacion"]["ciudad"]
    
    return resultado

def main():
    """Función principal."""
    # Cargar propiedades originales
    try:
        with open('resultados/propiedades_estructuradas.json', 'r', encoding='utf-8') as f:
            propiedades = json.load(f)
        logger.info(f"Propiedades cargadas: {len(propiedades)}")
    except Exception as e:
        logger.error(f"Error cargando propiedades: {e}")
        return
    
    # Normalizar propiedades
    propiedades_normalizadas = []
    for i, prop in enumerate(propiedades):
        try:
            prop_norm = normalizar_propiedad_selectiva(prop)
            propiedades_normalizadas.append(prop_norm)
            if (i + 1) % 100 == 0:
                logger.info(f"Propiedades normalizadas: {i + 1}")
        except Exception as e:
            logger.error(f"Error normalizando propiedad {i}: {e}")
    
    # Guardar propiedades normalizadas
    try:
        with open('resultados/propiedades_normalizadas.json', 'w', encoding='utf-8') as f:
            json.dump(propiedades_normalizadas, f, ensure_ascii=False, indent=2)
        logger.info("Propiedades normalizadas guardadas")
    except Exception as e:
        logger.error(f"Error guardando propiedades: {e}")

if __name__ == '__main__':
    main() 
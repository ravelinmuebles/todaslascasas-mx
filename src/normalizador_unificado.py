#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
normalizador_unificado.py
------------------------
Unifica las capacidades de «normalizador.py» (normalización completa)
y «normalizador_selectivo.py» (normalización rápida / selectiva).

USO:
    python3 normalizador_unificado.py --entrada resultados/propiedades_estructuradas.json \
                                      --salida resultados/propiedades_normalizadas.json \
                                      --modo full         # (default)  

    python3 normalizador_unificado.py --entrada resultados/propiedades_estructuradas.json \
                                      --salida resultados/propiedades_normalizadas.json \
                                      --modo selectivo

Características:
1. CLI sencilla usando argparse.
2. Respalda automáticamente el archivo de salida si existe (añade sufijo timestamp).
3. Incluye campo «schema_version» y «generated_at» para control de versión.
4. Mantiene logs detallados y colores si está disponible (colorama).
"""

import argparse
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    INFO = lambda msg: print(f"{Fore.CYAN}ℹ️  {msg}{Style.RESET_ALL}")
    OK = lambda msg: print(f"{Fore.GREEN}✅ {msg}{Style.RESET_ALL}")
    WARN = lambda msg: print(f"{Fore.YELLOW}⚠️  {msg}{Style.RESET_ALL}")
    ERR = lambda msg: print(f"{Fore.RED}❌ {msg}{Style.RESET_ALL}")
except ImportError:
    INFO = OK = WARN = ERR = print

# ---------------------------------------------------------------------------
# Reutilizar funciones del normalizador completo
# ---------------------------------------------------------------------------
from normalizador import (
    normalizar_propiedad as normalizar_propiedad_full,
    ErrorNormalizacion
)

# ---------------------------------------------------------------------------
# Funciones selectivas (copiadas y adaptadas de normalizador_selectivo.py)
# ---------------------------------------------------------------------------
import re

def _extraer_caracteristicas_numericas(propiedad: Dict) -> Dict:
    datos_orig = propiedad.get("datos_originales", {})
    caract_orig = datos_orig.get("caracteristicas", {})
    resultado = {
        "recamaras": caract_orig.get("recamaras"),
        "banos": caract_orig.get("banos"),
        "estacionamientos": caract_orig.get("estacionamientos"),
        "niveles": caract_orig.get("niveles"),
        "superficie_terreno": caract_orig.get("superficie_m2"),
        "superficie_construida": caract_orig.get("construccion_m2"),
        "antiguedad": caract_orig.get("edad"),
    }
    # Convertir a tipos numéricos
    for k, v in resultado.items():
        if v is None:
            continue
        try:
            if k in {"banos", "superficie_terreno", "superficie_construida"}:
                resultado[k] = float(v)
            else:
                resultado[k] = int(v)
        except (ValueError, TypeError):
            resultado[k] = None
    return resultado


def _extraer_precio_numerico(propiedad: Dict) -> Dict:
    datos_orig = propiedad.get("datos_originales", {})
    precio_str = datos_orig.get("precio", "")
    if precio_str:
        precio_limpio = re.sub(r"[^\d.]", "", precio_str.replace(",", ""))
        try:
            valor = float(precio_limpio)
            periodo = "Total" if propiedad.get("operacion", "").lower() == "venta" else "Mensual"
            return {"valor": valor, "moneda": "MXN", "periodo": periodo}
        except ValueError:
            pass
    return {"valor": None, "moneda": "MXN", "periodo": "Total"}


def normalizar_propiedad_selectiva(propiedad: Dict) -> Dict:
    resultado = propiedad.copy()
    resultado["caracteristicas"] = _extraer_caracteristicas_numericas(propiedad)
    resultado["precio_numerico"] = _extraer_precio_numerico(propiedad)
    if "operacion" in resultado:
        resultado["tipo_operacion"] = resultado["operacion"].lower()
    if "ubicacion" in resultado and "ciudad" in resultado["ubicacion"]:
        resultado["ciudad"] = resultado["ubicacion"]["ciudad"]
    return resultado

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def respaldar_archivo(path: Path) -> None:
    if path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(path.suffix + f".backup_{timestamp}")
        shutil.copy2(path, backup_path)
        WARN(f"Backup creado: {backup_path}")

# ---------------------------------------------------------------------------
# Proceso principal
# ---------------------------------------------------------------------------

def procesar(entrada: Path, salida: Path, modo: str) -> None:
    INFO(f"Modo de normalización: {modo}")
    INFO(f"Leyendo: {entrada}")
    with entrada.open("r", encoding="utf-8") as f:
        datos = json.load(f)

    total = len(datos) if isinstance(datos, list) else len(datos.keys())
    INFO(f"Propiedades encontradas: {total}")

    propiedades_norm: List[Dict] = []
    for i, prop in enumerate(datos if isinstance(datos, list) else datos.values(), 1):
        try:
            if modo == "selectivo":
                prop_norm = normalizar_propiedad_selectiva(prop)
            else:
                prop_norm = normalizar_propiedad_full(prop)
            propiedades_norm.append(prop_norm)
            if i % 500 == 0:
                INFO(f"Procesadas {i}/{total} propiedades…")
        except ErrorNormalizacion as e:
            ERR(f"Error en propiedad {prop.get('id', i)}: {e}")
        except Exception as e:
            ERR(f"Error inesperado en propiedad {prop.get('id', i)}: {e}")

    # Backup salida si existe
    respaldar_archivo(salida)

    # Empaquetar con metadatos
    output_payload = {
        "schema_version": "2.0" if modo == "full" else "2.0-selective",
        "generated_at": datetime.now().isoformat(),
        "propiedades": propiedades_norm,
        "total": len(propiedades_norm)
    }

    with salida.open("w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)
    OK(f"Archivo guardado: {salida} ({len(propiedades_norm)} propiedades)")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Normalizador unificado de propiedades")
    parser.add_argument("--entrada", required=True, help="Ruta al archivo de entrada")
    parser.add_argument("--salida", required=True, help="Ruta al archivo de salida")
    parser.add_argument("--modo", choices=["full", "selectivo"], default="full", help="Tipo de normalización")
    args = parser.parse_args()

    procesar(Path(args.entrada), Path(args.salida), args.modo)

if __name__ == "__main__":
    main() 
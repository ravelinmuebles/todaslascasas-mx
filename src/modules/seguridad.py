#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""seguridad.py – Detección de amenidades de seguridad

Extrae indicadores de seguridad comunes a partir de texto (título, descripción,
amenidades). Devuelve un dict con booleanos:
  • caseta_vigilancia
  • camaras_seguridad
  • vigilancia_24h
  • acceso_controlado

Uso:
    from seguridad import extraer_seguridad, actualizar_seguridad

    resultado = extraer_seguridad("Casa con caseta de vigilancia y cámaras 24/7")
    # {'caseta_vigilancia': True, 'camaras_seguridad': True, 'vigilancia_24h': True,
    #  'acceso_controlado': False, 'confianza': 0.9}

Dentro del pipeline ETL llamar `actualizar_seguridad(prop)` para añadir los
campos al dict de la propiedad.
"""

from __future__ import annotations

import re
from typing import Dict, List

# -------------------------------------------------------------
# PATRONES REGEX
# -------------------------------------------------------------
PATRONES_CASETA = [
    r"\bcaseta\b",
    r"vigilancia",
    r"vigilantes?",
]

PATRONES_CAMARAS = [
    r"c[aá]maras?",
    r"cctv",
]

PATRONES_24H = [
    r"24\s*(h|horas|hrs)",
    r"24/7",
]

PATRONES_ACCESO = [
    r"acceso\s*controlado",
    r"control\s*de\s*acceso",
    r"port[óo]n\s*el[eé]ctrico",
]

# -------------------------------------------------------------
def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.lower()
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ü": "u", "ñ": "n",
    }
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto


def extraer_seguridad(texto: str) -> Dict[str, bool]:
    """Devuelve dict con indicadores de seguridad."""
    texto = _normalizar(texto)
    caseta = any(re.search(p, texto) for p in PATRONES_CASETA)
    camaras = any(re.search(p, texto) for p in PATRONES_CAMARAS)
    h24 = any(re.search(p, texto) for p in PATRONES_24H)
    acceso = any(re.search(p, texto) for p in PATRONES_ACCESO)

    return {
        "caseta_vigilancia": caseta,
        "camaras_seguridad": camaras,
        "vigilancia_24h": h24,
        "acceso_controlado": acceso,
    }


def actualizar_seguridad(propiedad: Dict) -> Dict:
    """Agrega campos de seguridad al dict de la propiedad."""
    if not isinstance(propiedad, dict):
        return propiedad

    texto_fuente: List[str] = []
    for key in ("titulo", "descripcion"):
        if key in propiedad and propiedad[key]:
            texto_fuente.append(str(propiedad[key]))
    # amenidades puede ser lista o string
    amenidades = propiedad.get("amenidades")
    if amenidades:
        if isinstance(amenidades, list):
            texto_fuente.extend([str(a) for a in amenidades])
        else:
            texto_fuente.append(str(amenidades))

    resultados = extraer_seguridad(" ".join(texto_fuente))
    propiedad.update(resultados)
    return propiedad


# -------------------------------------------------------------
if __name__ == "__main__":
    ejemplo = "Casa nueva con caseta de vigilancia, cámaras CCTV y acceso controlado 24/7"
    print(extraer_seguridad(ejemplo)) 
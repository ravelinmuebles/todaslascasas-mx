#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modulo: direccion_completa.py
----------------------------------
Funciones utilitarias para extraer la dirección completa de un
HTML de Facebook Marketplace.

• Reutiliza la lógica de extract_precise_address.py.
• No depende de BeautifulSoup en el llamador; importa internamente.
• Pensado para ser usado por scripts de ingestión y otros módulos.
"""
from __future__ import annotations

import html as html_lib
import re
from typing import List

from bs4 import BeautifulSoup

__all__ = [
    "extract_address_from_html",
]

# Ciudades de referencia para heurística DOM (idéntico al script original)
CIUDADES_CONOCIDAS: List[str] = [
    "cuernavaca",
    "jiutepec",
    "temixco",
    "zapata",
    "yautepec",
    "tres de mayo",
    "burgos",
]

# Expresiones regulares compiladas una sola vez
_RE_SUBTITLE = re.compile(r'"subtitle":"(.*?)"')
_RE_MARKER = re.compile(r'📍([^\n\r<]+)')
_RE_PIN_LABEL = re.compile(r'"display_label":"([^"\\]+)",\s*"icon_name":"pin"')


def _clean_addr(addr: str) -> str:
    """Normaliza y limpia la cadena de dirección."""
    if not addr:
        return ""
    addr = html_lib.unescape(addr)
    addr = re.sub(r"\s+", " ", addr).strip(" ,•\u200e\u200f")
    return addr


def extract_address_from_html(html: str) -> str:
    """Extrae la dirección completa desde el HTML de Facebook Marketplace."""
    # 0) JSON display_label con icon_name="pin"
    m_pin = _RE_PIN_LABEL.search(html)
    if m_pin:
        candidate = _clean_addr(m_pin.group(1))
        if candidate and "," in candidate and not re.search(r"\d+\s*km", candidate.lower()):
            return candidate

    # 1) "subtitle":"..."
    for m in _RE_SUBTITLE.finditer(html):
        candidate = _clean_addr(m.group(1))
        if not candidate:
            continue
        if "km" in candidate.lower() and re.search(r"\d+\s*km", candidate.lower()):
            continue
        if "," in candidate:
            return candidate

    # 2) Emoji 📍
    m = _RE_MARKER.search(html)
    if m:
        candidate = _clean_addr(m.group(1))
        if candidate and "," in candidate:
            return candidate

    # 3) Heurística DOM
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(["span", "div"]):
        text = _clean_addr(tag.get_text(" ", strip=True))
        if not text or "," not in text or len(text) > 120:
            continue
        lt = text.lower()
        if lt.startswith("ubicación") or "radio de" in lt:
            continue
        if any(c in lt for c in CIUDADES_CONOCIDAS):
            return text

    # 4) Nada hallado
    return "" 
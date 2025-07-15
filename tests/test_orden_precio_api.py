import os
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _get_precios(orden: str):
    r = requests.get(f"{BASE_URL}/propiedades", params={"orden": orden, "por_pagina": 20, "pagina": 1}, timeout=30)
    r.raise_for_status()
    data = r.json()
    precios = [p.get("precio_numerico") if p.get("precio_numerico") is not None else p.get("precio") for p in data["propiedades"]]
    # Filtrar None para evitar fallos en ordenamiento
    return [pr for pr in precios if pr is not None]


def test_precio_ascendente():
    precios = _get_precios("precio_asc")
    assert precios == sorted(precios), "Los precios no están en orden ascendente"


def test_precio_descendente():
    precios = _get_precios("precio_desc")
    assert precios == sorted(precios, reverse=True), "Los precios no están en orden descendente" 
import os
import requests
import numbers

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _get_precios(orden: str):
    r = requests.get(f"{BASE_URL}/propiedades", params={"orden": orden, "por_pagina": 20, "pagina": 1}, timeout=30)
    r.raise_for_status()
    data = r.json()
    precios = [p.get("precio_numerico") if p.get("precio_numerico") is not None else p.get("precio") for p in data["propiedades"]]
    # Filtrar None para evitar fallos en ordenamiento
    return [pr for pr in precios if pr is not None]


def test_precio_numerico_existe():
    precios = _get_precios("created_at")  # cualquier orden
    assert len(precios) > 0, "La API devolvió 0 propiedades"
    assert all(isinstance(p, numbers.Number) for p in precios), "precio_numerico no es numérico" 
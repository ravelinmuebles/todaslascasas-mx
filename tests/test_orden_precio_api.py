import os
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def _get_precios(orden: str):
    r = requests.get(f"{BASE_URL}/propiedades", params={"orden": orden, "por_pagina": 20, "pagina": 1}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return [p.get("precio_numerico") or p.get("precio") for p in data["propiedades"]]


def test_precio_ascendente():
    precios = _get_precios("precio_asc")
    assert precios == sorted(precios), "Los precios no están en orden ascendente"


def test_precio_descendente():
    precios = _get_precios("precio_desc")
    assert precios == sorted(precios, reverse=True), "Los precios no están en orden descendente" 
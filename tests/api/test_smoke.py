import json, requests

def test_precio_endpoint():
    url = "https://api.todaslascasas.mx/propiedades?por_pagina=1&precio_min=1"
    resp = requests.get(url, timeout=10)
    assert resp.status_code == 200, f"Status {resp.status_code} != 200"
    data = resp.json()
    assert isinstance(data, dict) or isinstance(data, list) 
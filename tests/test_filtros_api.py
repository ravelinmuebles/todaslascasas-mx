import os
import pytest
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

@pytest.mark.parametrize("params, nombre", [
    ({"caseta_vigilancia": True}, "caseta_vigilancia"),
    ({"camaras_seguridad": True}, "camaras_seguridad"),
    ({"vigilancia_24h": True}, "vigilancia_24h"),
    ({"acceso_controlado": True}, "acceso_controlado"),
    ({"niveles": 1}, "un_nivel (fallback API)"),
    ({"caracteristicas_adicionales": ["Recámara en planta baja"]}, "recamara_pb"),
    ({"tipo_propiedad": ["local"]}, "local"),
    ({"tipo_propiedad": ["oficina"]}, "oficina"),
])
def test_filtro_devuelve_resultados(params, nombre):
    """Hace una llamada GET /propiedades con el filtro y asegura que devuelva ≥1 tarjeta."""
    url = f"{BASE_URL}/propiedades"
    # Usar página 1 con 3 resultados para hacer la prueba rápida
    params_full = {**params, "pagina": 1, "por_pagina": 3}
    r = requests.get(url, params=params_full, timeout=30)
    assert r.status_code == 200, f"{nombre}: status {r.status_code}"
    data = r.json()
    assert data["total"] >= 1, f"{nombre}: total 0"
    assert len(data["propiedades"]) >= 1, f"{nombre}: lista vacía" 
# -*- coding: utf-8 -*-
"""Test de regresión: asegura que cada propiedad tenga precio y dirección.

Ejecutar con pytest.  El test se salta automáticamente si el archivo de
repositorio no existe todavía (permite CI en etapas tempranas).
"""
import json
import os
import pytest

REPO_PATH = os.path.join(os.path.dirname(__file__), os.pardir, "resultados", "repositorio_propiedades.json")

@pytest.mark.skipif(not os.path.exists(REPO_PATH), reason="Repositorio aún no generado")
def test_propiedades_tienen_precio_y_direccion():
    with open(REPO_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = list(data.values())

    assert isinstance(data, list), "El repositorio debe ser una lista de propiedades"
    faltantes_precio = []
    faltantes_direccion = []

    for prop in data:
        precio_valor = None
        if isinstance(prop.get("precio"), dict):
            precio_valor = prop["precio"].get("valor")
        elif isinstance(prop.get("precio"), (int, float)):
            precio_valor = prop["precio"]
        elif isinstance(prop.get("precio"), str):
            precio_valor = prop["precio"].strip()

        if not precio_valor:
            faltantes_precio.append(prop.get("id", "sin_id"))

        direccion = prop.get("ubicacion", {}).get("direccion_completa", "").strip()
        if not direccion:
            faltantes_direccion.append(prop.get("id", "sin_id"))

    assert not faltantes_precio, f"Propiedades sin precio: {faltantes_precio[:10]} ... total {len(faltantes_precio)}"
    assert not faltantes_direccion, f"Propiedades sin direccion_completa: {faltantes_direccion[:10]} ... total {len(faltantes_direccion)}" 
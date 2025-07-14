#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from decimal import Decimal
from .precio import (
    extraer_precio,
    validar_precio,
    formatear_precio,
    _convertir_a_decimal,
    _normalizar_texto
)

def test_extraer_precio():
    """Test para la función extraer_precio."""
    # Casos de prueba con precios válidos
    casos = [
        ("$1,500,000", {"valor": 1500000.0, "moneda": "MXN", "es_valido": True}),
        ("2.5 millones", {"valor": 2500000.0, "moneda": "MXN", "es_valido": True}),
        ("USD 100,000", {"valor": 1750000.0, "moneda": "USD", "es_valido": True}),
        ("$500,000", {"valor": 500000.0, "moneda": "MXN", "es_valido": True}),
        ("1.5M", {"valor": 1500000.0, "moneda": "MXN", "es_valido": True}),
        ("750k", {"valor": 750000.0, "moneda": "MXN", "es_valido": True}),
    ]
    
    for texto, esperado in casos:
        resultado = extraer_precio(texto)
        print(f"\nProbando: {texto}")
        print(f"Esperado: {esperado}")
        print(f"Obtenido: {resultado}")
        assert resultado["valor"] == esperado["valor"], f"Valor incorrecto para {texto}"
        assert resultado["moneda"] == esperado["moneda"], f"Moneda incorrecta para {texto}"
        assert resultado["es_valido"] == esperado["es_valido"], f"Estado de validez incorrecto para {texto}"

def test_validar_precio():
    """Test para la función validar_precio."""
    # Casos de prueba con diferentes formatos
    casos = [
        (1500000.0, {"valor": 1500000.0, "moneda": "MXN", "es_valido": True}),
        ("$1,500,000", {"valor": 1500000.0, "moneda": "MXN", "es_valido": True}),
        (None, {"valor": None, "moneda": None, "es_valido": False}),
        ("", {"valor": None, "moneda": None, "es_valido": False}),
    ]
    
    for precio, esperado in casos:
        resultado = validar_precio(precio)
        print(f"\nProbando: {precio}")
        print(f"Esperado: {esperado}")
        print(f"Obtenido: {resultado}")
        assert resultado["valor"] == esperado["valor"], f"Valor incorrecto para {precio}"
        assert resultado["moneda"] == esperado["moneda"], f"Moneda incorrecta para {precio}"
        assert resultado["es_valido"] == esperado["es_valido"], f"Estado de validez incorrecto para {precio}"

def test_formatear_precio():
    """Test para la función formatear_precio."""
    # Casos de prueba con diferentes formatos
    casos = [
        (1500000.0, "completo", "$1,500,000 MXN"),
        (1500000.0, "simple", "$1,500,000"),
        (1500000.0, "numero", "1500000"),
        (None, "completo", "Precio no disponible"),
    ]
    
    for precio, formato, esperado in casos:
        resultado = formatear_precio(precio, formato)
        print(f"\nProbando: {precio} con formato {formato}")
        print(f"Esperado: {esperado}")
        print(f"Obtenido: {resultado}")
        assert resultado == esperado, f"Formato incorrecto para {precio} con formato {formato}"

def test_convertir_a_decimal():
    """Test para la función _convertir_a_decimal."""
    # Casos de prueba con diferentes formatos
    casos = [
        ("1,500,000", Decimal("1500000")),
        ("1.500.000", Decimal("1500000")),
        ("1,500.00", Decimal("1500.00")),
        ("1.500,00", Decimal("1500.00")),
        ("1500000", Decimal("1500000")),
        ("", None),
        (None, None),
    ]
    
    for valor, esperado in casos:
        resultado = _convertir_a_decimal(valor)
        print(f"\nProbando: {valor}")
        print(f"Esperado: {esperado}")
        print(f"Obtenido: {resultado}")
        assert resultado == esperado, f"Conversión incorrecta para {valor}"

def test_normalizar_texto():
    """Test para la función _normalizar_texto."""
    # Casos de prueba con diferentes formatos
    casos = [
        ("  Hola  Mundo  ", "hola mundo"),
        ("HOLA MUNDO", "hola mundo"),
        ("", ""),
        (None, ""),
    ]
    
    for texto, esperado in casos:
        resultado = _normalizar_texto(texto)
        print(f"\nProbando: {texto}")
        print(f"Esperado: {esperado}")
        print(f"Obtenido: {resultado}")
        assert resultado == esperado, f"Normalización incorrecta para {texto}" 
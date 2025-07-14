#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from modules.precio import normalizar_precio, formatear_precio

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_precio():
    """Prueba la normalización y formateo de precios."""
    
    # Casos de prueba
    casos = [
        # Precios directos de Facebook
        "2500000",
        "2,500,000",
        "2.500.000",
        "2500000.00",
        "2,500,000.00",
        "2.500.000,00",
        
        # Valores nulos o vacíos
        None,
        "",
        " ",
        
        # Valores inválidos
        "abc",
        "1,2,3",
        "1.2.3"
    ]
    
    print("\n=== PRUEBAS DE NORMALIZACIÓN DE PRECIOS ===")
    for caso in casos:
        print(f"\nCaso: {caso}")
        resultado = normalizar_precio(caso)
        print(f"Resultado: {resultado}")
        print(f"Formateado: {formatear_precio(resultado)}")

if __name__ == "__main__":
    test_precio() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba para el normalizador de propiedades.
"""

import json
from normalizador import normalizar_propiedad

# Datos de ejemplo
PROPIEDADES_EJEMPLO = [
    {
        "id": "1",
        "fecha_publicacion": "2024-03-20",
        "tipo_operacion": "venta",
        "tipo_propiedad": "casa",
        "precio": "$2.5 millones",
        "ciudad": "Cuernavaca",
        "colonia": "Lomas de Cortés",
        "direccion": "Av. Principal 123",
        "lat": 18.9186,
        "lng": -99.2345,
        "caracteristicas": {
            "recamaras": "3",
            "banos": "2.5",
            "estacionamientos": "2",
            "niveles": "2",
            "superficie_construida": "180",
            "superficie_terreno": "250"
        },
        "amenidades": {
            "alberca": True,
            "jardin": True,
            "seguridad": True,
            "areas_comunes": ["gimnasio", "salón de fiestas"],
            "adicionales": ["asador", "terraza"]
        },
        "legal": {
            "escrituras": True,
            "credito_infonavit": True,
            "credito_fovissste": False,
            "credito_bancario": True,
            "estatus_legal": "libre de gravamen"
        },
        "nombre_contacto": "Juan Pérez",
        "telefono": "7771234567",
        "email": "juan@ejemplo.com",
        "tipo_agente": "particular",
        "imagenes": [
            "https://ejemplo.com/img1.jpg",
            "https://ejemplo.com/img2.jpg"
        ],
        "video": "https://ejemplo.com/video.mp4",
        "activa": True
    },
    {
        "id": "2",
        "fecha_publicacion": "2024-03-19",
        "tipo_operacion": "renta",
        "tipo_propiedad": "departamento",
        "precio": "15 mil",
        "ciudad": "Cuernavaca",
        "colonia": "Delicias",
        "direccion": "Calle Reforma 456",
        "lat": 18.9200,
        "lng": -99.2300,
        "caracteristicas": {
            "recamaras": "2",
            "banos": "1",
            "estacionamientos": "1",
            "niveles": "1",
            "superficie_construida": "80",
            "superficie_terreno": "80"
        },
        "amenidades": {
            "alberca": False,
            "jardin": False,
            "seguridad": True,
            "areas_comunes": ["gimnasio"],
            "adicionales": []
        },
        "legal": {
            "escrituras": True,
            "credito_infonavit": False,
            "credito_fovissste": False,
            "credito_bancario": False,
            "estatus_legal": "libre de gravamen"
        },
        "nombre_contacto": "María García",
        "telefono": "7777654321",
        "email": "maria@ejemplo.com",
        "tipo_agente": "inmobiliaria",
        "imagenes": [
            "https://ejemplo.com/img3.jpg"
        ],
        "video": None,
        "activa": True
    }
]

def probar_normalizador():
    """Prueba el normalizador con datos de ejemplo."""
    print("\n=== PRUEBA DEL NORMALIZADOR ===\n")
    
    for i, prop in enumerate(PROPIEDADES_EJEMPLO, 1):
        print(f"\n--- Propiedad {i} Original ---")
        print(json.dumps(prop, indent=2, ensure_ascii=False))
        
        try:
            prop_norm = normalizar_propiedad(prop)
            print(f"\n--- Propiedad {i} Normalizada ---")
            print(json.dumps(prop_norm, indent=2, ensure_ascii=False))
            
            # Verificar campos importantes
            print(f"\nVerificación de campos importantes:")
            print(f"- Precio: {prop_norm['precio']}")
            print(f"- Características: {prop_norm['caracteristicas']}")
            print(f"- Amenidades: {prop_norm['amenidades']}")
            print(f"- Legal: {prop_norm['legal']}")
            
        except Exception as e:
            print(f"\nError normalizando propiedad {i}: {e}")
            
        print("\n" + "="*50)

if __name__ == "__main__":
    probar_normalizador() 
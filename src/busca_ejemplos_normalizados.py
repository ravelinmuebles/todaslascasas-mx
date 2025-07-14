#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Busca ejemplos concretos en el archivo de propiedades normalizadas para depuración de filtros.
"""
import json

# Cambia el path si es necesario
ARCHIVO = 'resultados/propiedades_normalizadas.json'

# Criterios de ejemplo
FILTROS = [
    ("Precio entre 1M y 3M", lambda p: p.get('precio', {}).get('valor') is not None and 1_000_000 <= p['precio']['valor'] <= 3_000_000),
    ("Casa con alberca", lambda p: p.get('tipo_propiedad') == 'casa' and p.get('amenidades', {}).get('alberca') is True),
    ("Propiedad en Cuernavaca", lambda p: p.get('ubicacion', {}).get('ciudad', '').lower() == 'cuernavaca'),
    ("Departamento en renta menor a 20 mil", lambda p: p.get('tipo_propiedad') == 'departamento' and p.get('tipo_operacion') == 'renta' and p.get('precio', {}).get('valor') is not None and p['precio']['valor'] < 20000),
]


def main():
    with open(ARCHIVO, 'r', encoding='utf-8') as f:
        propiedades = json.load(f)
    print(f"Total propiedades: {len(propiedades)}\n")
    for nombre, filtro in FILTROS:
        print(f"=== Ejemplo: {nombre} ===")
        encontrados = [p for p in propiedades if filtro(p)]
        print(f"Encontrados: {len(encontrados)}")
        for p in encontrados[:3]:
            print(f"- ID: {p.get('id')}")
            print(f"  Precio: {p.get('precio')}")
            print(f"  Tipo: {p.get('tipo_propiedad')}")
            print(f"  Operación: {p.get('tipo_operacion')}")
            print(f"  Ciudad: {p.get('ubicacion', {}).get('ciudad')}")
            print(f"  Amenidades: {p.get('amenidades')}")
        print()

if __name__ == '__main__':
    main() 
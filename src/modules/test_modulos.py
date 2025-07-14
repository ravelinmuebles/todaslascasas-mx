import pytest
import json
from decimal import Decimal
from typing import Dict, List

from tipo_propiedad import detectar_tipo_propiedad, TIPOS_PROPIEDAD, actualizar_tipo_propiedad
from caracteristicas import extraer_caracteristicas
from amenidades import detectar_amenidades
from legal import analizar_estatus_legal
from ubicacion import actualizar_ubicacion, extraer_ciudad, extraer_colonia, extraer_calle
from tipo_operacion import detectar_tipo_operacion
from precio import extraer_precio, validar_precio, formatear_precio

def test_serializacion_json():
    """Prueba que todos los módulos devuelvan resultados serializables a JSON"""
    
    # Caso complejo con todos los campos
    texto_prueba = """
    Hermosa casa sola en venta, ubicada en Av. Insurgentes Sur 1234, Col. Del Valle, 
    Benito Juárez, CDMX. 3 recámaras, 2.5 baños, 200m2 de construcción y 300m2 de terreno. 
    Cuenta con alberca techada, jardín con asador, y estacionamiento para 3 autos.
    Roof garden y área de juegos infantiles. 2 niveles. Con escrituras, acepta créditos 
    Infonavit y Fovissste. Precio: $8,500,000 MXN negociables.
    """
    
    # Probar cada módulo individualmente
    resultados = {
        "tipo_propiedad": detectar_tipo_propiedad(texto_prueba),
        "caracteristicas": extraer_caracteristicas(texto_prueba),
        "amenidades": detectar_amenidades(texto_prueba),
        "legal": analizar_estatus_legal(texto_prueba),
        "ubicacion": {
            "ciudad": extraer_ciudad(texto_prueba),
            "colonia": extraer_colonia(texto_prueba),
            "calle": extraer_calle(texto_prueba)
        },
        "tipo_operacion": detectar_tipo_operacion(texto_prueba),
        "precio": extraer_precio(texto_prueba)
    }
    
    # Intentar serializar a JSON
    try:
        json_str = json.dumps(resultados, ensure_ascii=False, indent=2)
        # Verificar que se puede deserializar
        json_back = json.loads(json_str)
        assert isinstance(json_back, dict)
        assert all(k in json_back for k in resultados.keys())
    except Exception as e:
        pytest.fail(f"Error al serializar/deserializar JSON: {str(e)}")

def test_tipos_numericos():
    """Prueba el manejo correcto de tipos numéricos"""
    
    # Probar superficie y precios con decimales
    texto_prueba = "Casa con 150.5 m2 de construcción. Precio: $2,500,500.50 USD"
    
    # Extraer características
    caract = extraer_caracteristicas(texto_prueba)
    assert isinstance(caract.get("superficie_construida"), (int, float, Decimal))
    
    # Extraer precio
    precio = extraer_precio(texto_prueba)
    assert isinstance(precio["valor"], (int, float, Decimal))
    assert isinstance(precio["texto_original"], str)  # Mantener formato original

def test_caracteres_especiales():
    """Prueba el manejo de caracteres especiales y codificación"""
    
    texto_prueba = """
    Departamento en México, Jalisco, área de Zapopan.
    Ubicado en Av. Américas #123, Colonia Ladrón de Guevara.
    Características: 2 recámaras, 1 baño, área 80m².
    """
    
    # Probar cada módulo con texto que tiene caracteres especiales
    for modulo, funcion in [
        ("ubicacion", extraer_ciudad),
        ("caracteristicas", extraer_caracteristicas),
        ("tipo_propiedad", detectar_tipo_propiedad)
    ]:
        resultado = funcion(texto_prueba)
        # Verificar que se puede serializar/deserializar
        try:
            json_str = json.dumps(resultado, ensure_ascii=False)
            json_back = json.loads(json_str)
            assert isinstance(json_back, dict)
        except Exception as e:
            pytest.fail(f"Error en módulo {modulo}: {str(e)}")

def test_integracion_propiedad():
    """Prueba la integración completa de una propiedad"""
    
    # Caso real completo
    propiedad = {
        "titulo": "Casa en venta en Colonia Del Valle",
        "descripcion": """
        Hermosa casa en venta ubicada en la mejor zona de la Del Valle.
        3 recámaras, 2.5 baños, 200m2 de construcción, 2 niveles.
        Cuenta con alberca, jardín y 2 lugares de estacionamiento.
        Acepta créditos bancarios e Infonavit.
        Precio: $7,500,000 pesos.
        """,
        "ubicacion": "Colonia Del Valle, Benito Juárez, Ciudad de México",
        "fecha_publicacion": "2025-06-05T12:00:00",
        "caracteristicas_raw": {
            "superficie_construida": 200,
            "superficie_terreno": 300,
            "recamaras": 3,
            "banos": 2.5,
            "niveles": 2
        }
    }
    
    # Procesar con cada módulo
    try:
        # Actualizar tipo de propiedad
        propiedad = actualizar_tipo_propiedad(propiedad)
        
        # Extraer características
        caracteristicas = extraer_caracteristicas(propiedad["descripcion"])
        propiedad["caracteristicas"] = caracteristicas
        
        # Detectar amenidades
        amenidades = detectar_amenidades(propiedad["descripcion"])
        propiedad["amenidades"] = amenidades
        
        # Analizar estatus legal
        legal = analizar_estatus_legal(propiedad["descripcion"])
        propiedad["legal"] = legal
        
        # Analizar ubicación
        propiedad = actualizar_ubicacion(propiedad)
        
        # Detectar tipo de operación
        tipo_op = detectar_tipo_operacion(propiedad["descripcion"])
        propiedad["tipo_operacion"] = tipo_op
        
        # Extraer y validar precio
        precio = extraer_precio(propiedad["descripcion"])
        if precio["es_valido"]:
            precio = validar_precio(precio)
            propiedad["precio_estructurado"] = {
                "valor": precio["valor"],
                "moneda": precio["moneda"],
                "formato": formatear_precio(precio)
            }
        
        # Verificar serialización
        json_str = json.dumps(propiedad, ensure_ascii=False, indent=2)
        json_back = json.loads(json_str)
        assert isinstance(json_back, dict)
        
    except Exception as e:
        pytest.fail(f"Error en integración: {str(e)}")

def test_valores_invalidos():
    """Prueba el manejo de valores inválidos y casos extremos"""
    
    casos_invalidos = [
        None,
        "",
        " ",
        "   \n   \t   ",
        "12345",
        "!@#$%^&*()",
        "Lorem " * 1000,  # Texto muy largo
        "casa" * 100,     # Palabra repetida muchas veces
        json.dumps({"a": 1}),  # String JSON
        "undefined",
        "null",
        "NaN",
        "Infinity"
    ]
    
    for texto in casos_invalidos:
        # Probar cada módulo con valores inválidos
        for modulo, funcion in [
            ("tipo_propiedad", detectar_tipo_propiedad),
            ("caracteristicas", extraer_caracteristicas),
            ("amenidades", detectar_amenidades),
            ("legal", analizar_estatus_legal),
            ("ubicacion", extraer_ciudad),
            ("tipo_operacion", detectar_tipo_operacion),
            ("precio", extraer_precio)
        ]:
            try:
                resultado = funcion(texto)
                # Verificar que devuelve un resultado válido
                assert isinstance(resultado, dict)
                # Verificar serialización
                json_str = json.dumps(resultado)
                json_back = json.loads(json_str)
                assert isinstance(json_back, dict)
            except Exception as e:
                pytest.fail(f"Error en módulo {modulo} con valor inválido '{texto}': {str(e)}") 
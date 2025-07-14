import json
import os
import sys
# Añadir lambda_build al PYTHONPATH si existe
current_dir = os.path.dirname(__file__)
lambda_build_path = os.path.join(current_dir, 'lambda_build')
if os.path.isdir(lambda_build_path) and lambda_build_path not in sys.path:
    sys.path.append(lambda_build_path)

# Algunas compilaciones guardan los paquetes dentro de "lambda_build/lambda_build".
# Añadimos esa ruta adicional para garantizar que se pueda importar Mangum y otras dependencias.
nested_build_path = os.path.join(lambda_build_path, 'lambda_build')
if os.path.isdir(nested_build_path) and nested_build_path not in sys.path:
    sys.path.append(nested_build_path)

try:
    from mangum import Mangum
except ModuleNotFoundError:
    try:
        from lambda_build.mangum import Mangum  # type: ignore
    except ModuleNotFoundError as e:
        # Registrar error claro antes de volver a lanzar
        import logging
        logging.error("Mangum no encontrado en ninguna ruta: %s", e)
        raise

# Importar la aplicación FastAPI de api_postgresql.py
from api_postgresql import app

# Crear el handler de Lambda usando Mangum
handler = Mangum(app)

def lambda_handler(event, context):
    """
    Función principal para AWS Lambda
    """
    return handler(event, context)
 